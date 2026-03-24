#!/usr/bin/env python3
"""
 ███╗   ██╗███████╗ █████╗ ████████╗    ███████╗██████╗ ███████╗ █████╗ ██╗  ██╗
 ████╗  ██║██╔════╝██╔══██╗╚══██╔══╝    ██╔════╝██╔══██╗██╔════╝██╔══██╗██║ ██╔╝
 ██╔██╗ ██║█████╗  ███████║   ██║       █████╗  ██████╔╝█████╗  ███████║█████╔╝
 ██║╚██╗██║██╔══╝  ██╔══██║   ██║       ██╔══╝  ██╔══██╗██╔══╝  ██╔══██║██╔═██╗
 ██║ ╚████║███████╗██║  ██║   ██║       ██║     ██║  ██║███████╗██║  ██║██║  ██╗
 ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝   ╚═╝       ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝

 Obsessively organised. Every pixel. Every file.
 macOS media organiser — sorts photos & videos into Year / Month / Day folders.

 Run:   python3 NeatFreak.py
 Deps:  brew install python-tk
        pip3 install pillow hachoir   (optional — better date extraction)
"""

import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
from pathlib import Path
import math

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_AVAILABLE = True
except ImportError:
    HACHOIR_AVAILABLE = False

# ── file types ─────────────────────────────────────────────────────────────────
PHOTO_EXT = {".jpg",".jpeg",".png",".heic",".heif",".tiff",".tif",
             ".bmp",".webp",".raw",".cr2",".nef",".arw",".dng"}
VIDEO_EXT = {".mp4",".mov",".avi",".mkv",".m4v",".3gp",
             ".wmv",".flv",".mts",".m2ts"}
ALL_EXT   = PHOTO_EXT | VIDEO_EXT

MONTH_NAMES = ["","1-January","2-February","3-March","4-April",
               "5-May","6-June","7-July","8-August",
               "9-September","10-October","11-November","12-December"]

# ── BRAND PALETTE ──────────────────────────────────────────────────────────────
# Neat Freak identity: deep obsidian + surgical mint + warm off-white
INK       = "#0a0c10"       # deepest background
VOID      = "#0e1118"       # main bg
OBSIDIAN  = "#141720"       # card bg
SLATE     = "#1c2030"       # elevated surface
RIM       = "#252a3a"       # border / divider
RIM2      = "#2f3650"       # hover border

MINT      = "#00e5b0"       # PRIMARY accent — the brand colour
MINT_DIM  = "#00b888"       # pressed mint
MINT_GLOW = "#0a2e28"       # dark teal wash (no alpha — Tk doesn't support it)

CORAL     = "#ff6b6b"       # error
AMBER     = "#ffb347"       # warning / rename
SAGE      = "#34d399"       # success / copied
STEEL     = "#6b7fa3"       # skipped / muted

CREAM     = "#f0ece0"       # primary text
CREAM_DIM = "#8a9bb5"       # secondary text
GHOST     = "#3a4560"       # very dim text

# Typography — clean geometric + monospace log
F_BRAND  = ("SF Pro Display", 28, "bold")
F_TAG    = ("SF Pro Display", 10)
F_LABEL  = ("SF Pro Text", 11, "bold")
F_BODY   = ("SF Pro Text", 11)
F_SMALL  = ("SF Pro Text", 10)
F_MONO   = ("SF Mono", 10)
F_NUM    = ("SF Pro Display", 20, "bold")
F_NUM_SM = ("SF Pro Display", 13, "bold")


# ── helpers ────────────────────────────────────────────────────────────────────
def get_exif_date(p):
    if not PILLOW_AVAILABLE or p.suffix.lower() not in PHOTO_EXT:
        return None
    try:
        img = Image.open(p)
        exif = img._getexif()
        if not exif:
            return None
        for tid, val in exif.items():
            if TAGS.get(tid, tid) in ("DateTimeOriginal","DateTime","DateTimeDigitized"):
                return datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None

def get_video_date(p):
    if not HACHOIR_AVAILABLE or p.suffix.lower() not in VIDEO_EXT:
        return None
    try:
        parser = createParser(str(p))
        if not parser:
            return None
        with parser:
            meta = extractMetadata(parser)
        if meta:
            dt = meta.get("creation_date")
            return dt if isinstance(dt, datetime) else None
    except Exception:
        pass
    return None

def get_file_date(p):
    return (get_exif_date(p) or get_video_date(p)
            or datetime.fromtimestamp(p.stat().st_mtime))

def resolve_target(target_dir, src):
    t = target_dir / src.name
    if not t.exists():
        return t, "copy"
    if t.stat().st_size == src.stat().st_size:
        return None, "skip"
    stem, suf, i = src.stem, src.suffix, 1
    while True:
        t = target_dir / f"{stem}_{i}{suf}"
        if not t.exists():
            return t, "rename"
        i += 1

def fmt_time(s):
    s = int(s)
    if s < 60:   return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:   return f"{m}m {s:02d}s"
    h, m = divmod(m, 60)
    return f"{h}h {m:02d}m"

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def lerp_color(c1, c2, t):
    r1,g1,b1 = hex_to_rgb(c1)
    r2,g2,b2 = hex_to_rgb(c2)
    r = int(r1 + (r2-r1)*t)
    g = int(g1 + (g2-g1)*t)
    b = int(b1 + (b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── animated canvas progress bar ───────────────────────────────────────────────
class MintProgressBar(tk.Canvas):
    def __init__(self, parent, height=6, **kwargs):
        super().__init__(parent, height=height, bg=OBSIDIAN,
                         highlightthickness=0, bd=0, **kwargs)
        self._fraction = 0.0
        self._anim_fraction = 0.0
        self._height = height
        self._shimmer_x = -200
        self._animating = False
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, fraction):
        self._fraction = max(0.0, min(1.0, fraction))
        if not self._animating:
            self._animating = True
            self._animate()

    def _animate(self):
        diff = self._fraction - self._anim_fraction
        if abs(diff) > 0.001:
            self._anim_fraction += diff * 0.15
            self._draw()
            self.after(16, self._animate)
        else:
            self._anim_fraction = self._fraction
            self._draw()
            self._animating = False

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self._height
        if w < 2:
            return
        r = h // 2

        # track
        self.create_rectangle(0, 0, w, h, fill=RIM, outline="")

        # fill
        fill_w = int(w * self._anim_fraction)
        if fill_w > r * 2:
            self.create_rectangle(0, 0, fill_w, h, fill=MINT, outline="")

        # shimmer sweep over filled area
        if fill_w > 20:
            sx = self._shimmer_x % (fill_w + 200) - 100
            for i in range(60):
                alpha = math.sin(math.pi * i / 60)
                shade = lerp_color(MINT, "#ffffff", alpha * 0.35)
                x = sx + i
                if 0 <= x < fill_w:
                    self.create_line(x, 0, x, h, fill=shade)

        self._shimmer_x += 4
        if self._animating:
            pass  # shimmer runs while animating

    def start_pulse(self):
        """Continuous shimmer for indeterminate state."""
        self._shimmer_x += 6
        self._draw()
        self.after(30, self.start_pulse)


# ── flat label button ──────────────────────────────────────────────────────────
class NeatButton(tk.Label):
    def __init__(self, parent, text, command=None, style="primary",
                 padx=20, pady=10, font=None, **kwargs):
        styles = {
            "primary": (MINT,     INK,      MINT_DIM,  INK),
            "ghost":   (SLATE,    CREAM_DIM, RIM2,     CREAM),
            "danger":  (CORAL,    INK,      "#cc5555",  INK),
        }
        bg, fg, hbg, hfg = styles.get(style, styles["primary"])
        font = font or F_LABEL
        super().__init__(parent, text=text, bg=bg, fg=fg, font=font,
                         padx=padx, pady=pady, cursor="hand2", **kwargs)
        self._bg = bg; self._fg = fg
        self._hbg = hbg; self._hfg = hfg
        self._command = command
        self._enabled = True

        self.bind("<Enter>",           self._hover_on)
        self.bind("<Leave>",           self._hover_off)
        self.bind("<ButtonPress-1>",   self._press)
        self.bind("<ButtonRelease-1>", self._release)

    def set_enabled(self, v):
        self._enabled = v
        self.configure(fg=self._fg if v else GHOST,
                       cursor="hand2" if v else "arrow")

    def _hover_on(self, _=None):
        if self._enabled:
            self.configure(bg=self._hbg, fg=self._hfg)

    def _hover_off(self, _=None):
        self.configure(bg=self._bg,
                       fg=self._fg if self._enabled else GHOST)

    def _press(self, _=None):
        if self._enabled:
            self.configure(bg=INK)

    def _release(self, _=None):
        self._hover_off()
        if self._enabled and self._command:
            self._command()


# ── folder picker card ────────────────────────────────────────────────────────
class FolderCard(tk.Frame):
    def __init__(self, parent, label, hint, icon, var, on_pick, **kwargs):
        super().__init__(parent, bg=OBSIDIAN, **kwargs)
        self._var = var
        self._active = False

        # outer border frame for the glowing rim effect
        self._rim = tk.Frame(self, bg=RIM, padx=1, pady=1)
        self._rim.pack(fill="both", expand=True)

        inner = tk.Frame(self._rim, bg=OBSIDIAN)
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        # top row: icon + label
        top = tk.Frame(inner, bg=OBSIDIAN)
        top.pack(fill="x")

        tk.Label(top, text=icon, font=("SF Pro Text", 18),
                 bg=OBSIDIAN, fg=MINT).pack(side="left", padx=(0,10))

        meta = tk.Frame(top, bg=OBSIDIAN)
        meta.pack(side="left", fill="x", expand=True)
        tk.Label(meta, text=label, font=F_LABEL,
                 bg=OBSIDIAN, fg=CREAM).pack(anchor="w")
        tk.Label(meta, text=hint, font=F_SMALL,
                 bg=OBSIDIAN, fg=CREAM_DIM).pack(anchor="w")

        NeatButton(top, text="Choose", command=on_pick,
                   style="ghost", padx=14, pady=6,
                   font=F_SMALL).pack(side="right")

        # path display
        self._path_lbl = tk.Label(inner, text="No folder selected",
                                  font=F_MONO, bg=OBSIDIAN, fg=GHOST,
                                  anchor="w", wraplength=480, justify="left")
        self._path_lbl.pack(fill="x", pady=(8,0))

        var.trace_add("write", self._on_change)

    def _on_change(self, *_):
        p = self._var.get()
        if p and p != "No folder selected":
            self._path_lbl.configure(text=p, fg=MINT)
            self._rim.configure(bg=MINT)
            self._active = True
        else:
            self._path_lbl.configure(text="No folder selected", fg=GHOST)
            self._rim.configure(bg=RIM)
            self._active = False


# ── stat tile ─────────────────────────────────────────────────────────────────
class StatTile(tk.Frame):
    def __init__(self, parent, label, color, **kwargs):
        super().__init__(parent, bg=SLATE, **kwargs)
        self._color = color
        # top accent bar
        tk.Frame(self, bg=color, height=2).pack(fill="x")
        pad = tk.Frame(self, bg=SLATE)
        pad.pack(fill="both", expand=True, padx=12, pady=10)
        self._var = tk.StringVar(value="—")
        tk.Label(pad, textvariable=self._var, font=F_NUM,
                 bg=SLATE, fg=color).pack(anchor="w")
        tk.Label(pad, text=label, font=F_SMALL,
                 bg=SLATE, fg=CREAM_DIM).pack(anchor="w")

    def set(self, v): self._var.set(str(v))


# ── main application ──────────────────────────────────────────────────────────
class NeatFreak(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Neat Freak")
        self.geometry("900x820")
        self.minsize(780, 700)
        self.configure(bg=VOID)
        self.resizable(True, True)

        self._source = tk.StringVar()
        self._dest   = tk.StringVar()
        self._mode   = tk.StringVar(value="copy")
        self._dry    = tk.BooleanVar(value=False)
        self._running   = False
        self._cancelled = False

        self._build()

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self):
        # ── top bar ──
        topbar = tk.Frame(self, bg=INK, height=56)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tb_inner = tk.Frame(topbar, bg=INK)
        tb_inner.pack(fill="both", expand=True, padx=28)

        # logo mark — geometric NF monogram drawn on canvas
        logo_canvas = tk.Canvas(tb_inner, width=34, height=34,
                                bg=INK, highlightthickness=0)
        logo_canvas.pack(side="left", pady=11)
        self._draw_logo(logo_canvas, 34)

        # brand name
        tk.Label(tb_inner, text="NEAT FREAK", font=("SF Pro Display", 15, "bold"),
                 bg=INK, fg=CREAM).pack(side="left", padx=(10, 0), pady=(0,1))
        tk.Label(tb_inner, text="·  media organiser", font=F_SMALL,
                 bg=INK, fg=GHOST).pack(side="left", padx=(8,0), pady=(2,0))

        # version badge
        badge = tk.Frame(tb_inner, bg=MINT_GLOW)
        badge.pack(side="right", pady=18)
        tk.Label(badge, text="v 1.0", font=("SF Mono", 9),
                 bg=MINT_GLOW, fg=MINT, padx=8, pady=2).pack()

        # ── thin mint rule ──
        tk.Frame(self, bg=MINT, height=1).pack(fill="x")

        # ── main scroll container ──
        main = tk.Frame(self, bg=VOID)
        main.pack(fill="both", expand=True, padx=30, pady=24)

        # ── section: WHERE ──
        self._section_label(main, "01", "SOURCE & DESTINATION")

        folders = tk.Frame(main, bg=VOID)
        folders.pack(fill="x", pady=(8, 0))
        folders.columnconfigure(0, weight=1)
        folders.columnconfigure(1, weight=1)

        FolderCard(folders, "Source Folder",
                   "Folder containing your original media",
                   "📂", self._source, self._pick_source).grid(
                   row=0, column=0, sticky="nsew", padx=(0,6))

        FolderCard(folders, "Destination Folder",
                   "Where organised Year / Month / Day folders will be created",
                   "🗂", self._dest, self._pick_dest).grid(
                   row=0, column=1, sticky="nsew", padx=(6,0))

        # ── section: HOW ──
        self._section_label(main, "02", "OPTIONS", pady=(22,0))

        opts_card = tk.Frame(main, bg=OBSIDIAN,
                             highlightbackground=RIM, highlightthickness=1)
        opts_card.pack(fill="x", pady=(8,0))

        opts_inner = tk.Frame(opts_card, bg=OBSIDIAN)
        opts_inner.pack(fill="x", padx=20, pady=14)

        # mode selector
        mode_frame = tk.Frame(opts_inner, bg=OBSIDIAN)
        mode_frame.pack(side="left")
        tk.Label(mode_frame, text="MODE", font=("SF Mono", 9),
                 bg=OBSIDIAN, fg=GHOST).pack(anchor="w")
        rb_row = tk.Frame(mode_frame, bg=OBSIDIAN)
        rb_row.pack(anchor="w", pady=(4,0))
        for label, val in (("Copy files", "copy"), ("Move files", "move")):
            tk.Radiobutton(rb_row, text=label, variable=self._mode, value=val,
                           font=F_BODY, bg=OBSIDIAN, fg=CREAM,
                           selectcolor=MINT_GLOW, activebackground=OBSIDIAN,
                           activeforeground=MINT, highlightthickness=0,
                           cursor="hand2").pack(side="left", padx=(0,16))

        # vertical divider
        tk.Frame(opts_inner, bg=RIM, width=1).pack(side="left",
                                                    fill="y", padx=24)

        # dry run toggle
        dry_frame = tk.Frame(opts_inner, bg=OBSIDIAN)
        dry_frame.pack(side="left")
        tk.Label(dry_frame, text="DRY RUN", font=("SF Mono", 9),
                 bg=OBSIDIAN, fg=GHOST).pack(anchor="w")
        tk.Checkbutton(dry_frame, text="Preview only — no files touched",
                       variable=self._dry, font=F_BODY,
                       bg=OBSIDIAN, fg=CREAM, selectcolor=MINT_GLOW,
                       activebackground=OBSIDIAN, activeforeground=MINT,
                       highlightthickness=0, cursor="hand2").pack(
                       anchor="w", pady=(4,0))

        # ── section: ACTION ──
        self._section_label(main, "03", "RUN", pady=(22,0))

        action_row = tk.Frame(main, bg=VOID)
        action_row.pack(fill="x", pady=(8,0))

        self._btn_start = NeatButton(
            action_row, text="▶   Organise Now",
            command=self._start, style="primary",
            font=("SF Pro Display", 13, "bold"), padx=28, pady=12)
        self._btn_start.pack(side="left")

        self._btn_cancel = NeatButton(
            action_row, text="✕   Cancel",
            command=self._cancel, style="ghost",
            font=F_LABEL, padx=20, pady=12)
        self._btn_cancel.set_enabled(False)
        self._btn_cancel.pack(side="left", padx=(10,0))

        # ── section: PROGRESS ──
        self._section_label(main, "04", "PROGRESS", pady=(22,0))

        prog_card = tk.Frame(main, bg=OBSIDIAN,
                             highlightbackground=RIM, highlightthickness=1)
        prog_card.pack(fill="x", pady=(8,0))
        pc = tk.Frame(prog_card, bg=OBSIDIAN)
        pc.pack(fill="x", padx=20, pady=16)

        # status + eta row
        sr = tk.Frame(pc, bg=OBSIDIAN)
        sr.pack(fill="x", pady=(0,8))
        self._lbl_status = tk.Label(sr, text="Ready to organise.",
                                    font=F_NUM_SM, bg=OBSIDIAN, fg=CREAM)
        self._lbl_status.pack(side="left")
        self._lbl_eta = tk.Label(sr, text="", font=("SF Mono", 10),
                                 bg=OBSIDIAN, fg=CREAM_DIM)
        self._lbl_eta.pack(side="right")

        # progress bar
        self._pbar = MintProgressBar(pc, height=6)
        self._pbar.pack(fill="x")

        # stat tiles
        tiles = tk.Frame(pc, bg=OBSIDIAN)
        tiles.pack(fill="x", pady=(14,0))
        tiles.columnconfigure((0,1,2,3,4), weight=1)

        self._stats = {}
        for i, (key, label, color) in enumerate([
            ("total",   "TOTAL",   CREAM_DIM),
            ("copied",  "COPIED",  SAGE),
            ("skipped", "SKIPPED", STEEL),
            ("renamed", "RENAMED", AMBER),
            ("errors",  "ERRORS",  CORAL),
        ]):
            t = StatTile(tiles, label, color)
            t.grid(row=0, column=i, sticky="nsew",
                   padx=(0 if i==0 else 4, 0))
            self._stats[key] = t

        # ── section: LOG ──
        log_hdr = tk.Frame(main, bg=VOID)
        log_hdr.pack(fill="x", pady=(22,0))

        # inline section label with clear button
        lh_left = tk.Frame(log_hdr, bg=VOID)
        lh_left.pack(side="left")
        tk.Frame(lh_left, bg=MINT, width=3, height=14).pack(
            side="left", padx=(0,8))
        tk.Label(lh_left, text="05", font=("SF Mono", 8),
                 bg=VOID, fg=MINT).pack(side="left", padx=(0,6))
        tk.Label(lh_left, text="ACTIVITY LOG", font=("SF Mono", 9, "bold"),
                 bg=VOID, fg=CREAM_DIM).pack(side="left")

        NeatButton(log_hdr, text="Clear Log", command=self._clear_log,
                   style="ghost", padx=12, pady=4,
                   font=F_SMALL).pack(side="right")

        log_wrap = tk.Frame(main, bg=OBSIDIAN,
                            highlightbackground=RIM, highlightthickness=1)
        log_wrap.pack(fill="both", expand=True, pady=(8,0))

        self._log = tk.Text(
            log_wrap, bg=OBSIDIAN, fg=CREAM_DIM, font=F_MONO,
            relief="flat", bd=0, padx=16, pady=14,
            wrap="none", cursor="arrow", state="disabled",
            spacing1=2, spacing3=2)
        sb = tk.Scrollbar(log_wrap, orient="vertical",
                          command=self._log.yview)
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True)

        # log tags
        self._log.tag_config("copy",    foreground=SAGE)
        self._log.tag_config("skip",    foreground=STEEL)
        self._log.tag_config("rename",  foreground=AMBER)
        self._log.tag_config("error",   foreground=CORAL)
        self._log.tag_config("info",    foreground=MINT)
        self._log.tag_config("dim",     foreground=GHOST)
        self._log.tag_config("head",    foreground=CREAM,
                             font=("SF Mono", 10, "bold"))
        self._log.tag_config("done",    foreground=MINT,
                             font=("SF Mono", 10, "bold"))

        # ── footer ──
        footer = tk.Frame(self, bg=INK, height=32)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        tk.Label(footer,
                 text="Neat Freak  ·  made with obsession  ·  every file in its place",
                 font=("SF Mono", 9), bg=INK, fg=GHOST).pack(
                 side="left", padx=28, pady=8)

    # ─────────────────────────────────────────────────────────────────────────
    def _section_label(self, parent, num, text, pady=(0,0)):
        row = tk.Frame(parent, bg=VOID)
        row.pack(fill="x", pady=pady)
        tk.Frame(row, bg=MINT, width=3, height=14).pack(
            side="left", padx=(0,8), pady=2)
        tk.Label(row, text=num, font=("SF Mono", 8),
                 bg=VOID, fg=MINT).pack(side="left", padx=(0,6))
        tk.Label(row, text=text, font=("SF Mono", 9, "bold"),
                 bg=VOID, fg=CREAM_DIM).pack(side="left")

    def _draw_logo(self, canvas, size):
        """Draw the NF geometric logo mark in mint."""
        s = size
        canvas.create_rectangle(0, 0, s, s, fill=MINT, outline="")
        canvas.create_text(s//2, s//2 + 1, text="NF",
                           font=("SF Pro Display", 13, "bold"),
                           fill=INK)

    # ── folder pickers ────────────────────────────────────────────────────────
    def _pick_source(self):
        p = filedialog.askdirectory(title="Select Source Folder")
        if p: self._source.set(p)

    def _pick_dest(self):
        p = filedialog.askdirectory(title="Select Destination Folder")
        if p: self._dest.set(p)

    # ── log ───────────────────────────────────────────────────────────────────
    def _log_write(self, text, tag=""):
        self._log.configure(state="normal")
        self._log.insert("end", text, tag)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _log_line(self, text, tag=""):
        self._log_write(text + "\n", tag)

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    # ── start / cancel ────────────────────────────────────────────────────────
    def _start(self):
        src  = self._source.get()
        dest = self._dest.get()

        if not src or src == "No folder selected":
            self._log_line("  ✕  Please select a source folder first.", "error")
            return
        if not dest or dest == "No folder selected":
            self._log_line("  ✕  Please select a destination folder first.", "error")
            return

        src_p  = Path(src).expanduser().resolve()
        dest_p = Path(dest).expanduser().resolve()

        if not src_p.exists():
            self._log_line(f"  ✕  Source not found: {src_p}", "error")
            return

        self._running   = True
        self._cancelled = False
        self._btn_start.set_enabled(False)
        self._btn_cancel.set_enabled(True)

        for t in self._stats.values():
            t.set("…")
        self._pbar.set(0)
        self._lbl_eta.configure(text="")
        self._lbl_status.configure(text="Scanning…")

        threading.Thread(
            target=self._worker,
            args=(src_p, dest_p, self._mode.get(), self._dry.get()),
            daemon=True
        ).start()

    def _cancel(self):
        if self._running:
            self._cancelled = True
            self._lbl_status.configure(text="Cancelling…")

    # ── worker ────────────────────────────────────────────────────────────────
    def _worker(self, src, dest, mode, dry):
        def ui(fn): self.after(0, fn)

        stamp = datetime.now().strftime("%H:%M:%S")
        ui(lambda: self._log_line(
            f"\n  ── Run started {stamp} ──────────────────────────────", "dim"))
        ui(lambda: self._log_line(f"  Scanning {src} …", "dim"))

        all_files = [p for p in src.rglob("*")
                     if p.is_file() and p.suffix.lower() in ALL_EXT]
        total = len(all_files)

        if total == 0:
            ui(lambda: self._lbl_status.configure(text="No media found."))
            ui(lambda: self._log_line("  No media files found in source folder.", "error"))
            self._finish_ui()
            return

        ui(lambda: self._stats["total"].set(total))
        ui(lambda: self._log_line(
            f"  Found {total} file(s)  ·  {'DRY RUN — ' if dry else ''}"
            f"{'Moving' if mode=='move' else 'Copying'} to {dest}\n", "info"))

        copied = skipped = renamed = errors = 0
        t0 = time.time()

        for i, fp in enumerate(sorted(all_files), 1):
            if self._cancelled:
                break
            try:
                date   = get_file_date(fp)
                tdir   = dest / str(date.year) / MONTH_NAMES[date.month] / str(date.day)
                target, action = resolve_target(tdir, fp)

                if action == "skip":
                    skipped += 1
                    ui(lambda m=fp.name: self._log_line(
                        f"  ·  SKIP     {m}", "skip"))
                else:
                    if not dry:
                        tdir.mkdir(parents=True, exist_ok=True)
                        if mode == "move":
                            shutil.move(str(fp), str(target))
                        else:
                            shutil.copy2(str(fp), str(target))
                    verb = "MOVE" if mode == "move" else "COPY"
                    if action == "rename":
                        renamed += 1
                        ui(lambda m=fp.name, t=target.name: self._log_line(
                            f"  ·  {verb}     {m}  →  {t}  (renamed)", "rename"))
                    else:
                        copied += 1
                        rel = str(target.relative_to(dest))
                        ui(lambda m=fp.name, r=rel: self._log_line(
                            f"  ·  {verb}     {m}  →  {r}", "copy"))

            except Exception as e:
                errors += 1
                ui(lambda m=fp.name, err=str(e): self._log_line(
                    f"  ·  ERROR    {m}  —  {err}", "error"))

            # progress update
            frac = i / total
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            rem  = (total - i) / rate if rate > 0 else 0
            eta  = f"ETA  {fmt_time(rem)}" if rem > 1 else "Almost done…"

            def _up(c=copied, sk=skipped, rn=renamed, er=errors,
                    f=frac, e=eta, d=i, t=total):
                self._pbar.set(f)
                self._stats["copied"].set(c)
                self._stats["skipped"].set(sk)
                self._stats["renamed"].set(rn)
                self._stats["errors"].set(er)
                self._lbl_eta.configure(text=e)
                self._lbl_status.configure(text=f"Processing  {d} / {t}")
            ui(_up)

        # ── summary ──
        elapsed = time.time() - t0
        cancelled = self._cancelled
        label = "CANCELLED" if cancelled else ("DRY RUN COMPLETE" if dry else "COMPLETE")
        tag   = "error" if cancelled else "done"

        def _summary(c=copied, sk=skipped, rn=renamed, er=errors,
                     el=elapsed, lbl=label, tg=tag):
            self._pbar.set(1.0 if not cancelled else
                           (c+sk+rn+er) / max(total, 1))
            self._lbl_status.configure(
                text=f"{'⚠  ' if cancelled else '✓  '}{lbl}")
            self._lbl_eta.configure(text=f"Total time: {fmt_time(el)}")
            self._log_line("\n  " + "─"*54, "dim")
            self._log_line(
                f"  {lbl}  ·  {fmt_time(el)}", tg)
            self._log_line(
                f"  Copied {c}  ·  Skipped {sk}  ·  "
                f"Renamed {rn}  ·  Errors {er}\n", "head")
            if dry:
                self._log_line(
                    "  Dry-run mode — no files were actually moved or copied.", "dim")
        ui(_summary)
        self._finish_ui()

    def _finish_ui(self):
        def _re():
            self._running = False
            self._btn_start.set_enabled(True)
            self._btn_cancel.set_enabled(False)
        self.after(0, _re)


# ── entry ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = NeatFreak()
    app.mainloop()