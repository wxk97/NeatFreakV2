#!/usr/bin/env python3
"""
make_icon.py — Generates NeatFreak.png (1024x1024) using Pillow.
Run: python3 make_icon.py
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "pillow",
                    "--break-system-packages"], check=True)
    from PIL import Image, ImageDraw, ImageFont

SIZE    = 1024
INK     = (10, 12, 16)
CARD    = (20, 23, 32)
MINT    = (0, 229, 176)
CREAM   = (240, 236, 224)
BORDER  = 6

img  = Image.new("RGBA", (SIZE, SIZE), INK)
draw = ImageDraw.Draw(img)

# ── rounded rect background card ──
margin = 60
r      = 120   # corner radius

def rounded_rect(draw, x0, y0, x1, y1, r, fill, outline=None, width=1):
    draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
    draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
    draw.ellipse([x0, y0, x0+2*r, y0+2*r], fill=fill)
    draw.ellipse([x1-2*r, y0, x1, y0+2*r], fill=fill)
    draw.ellipse([x0, y1-2*r, x0+2*r, y1], fill=fill)
    draw.ellipse([x1-2*r, y1-2*r, x1, y1], fill=fill)
    if outline:
        for i in range(width):
            draw.arc([x0+i, y0+i, x0+2*r-i, y0+2*r-i], 180, 270, fill=outline)
            draw.arc([x1-2*r+i, y0+i, x1-i, y0+2*r-i], 270, 360, fill=outline)
            draw.arc([x0+i, y1-2*r+i, x0+2*r-i, y1-i], 90, 180, fill=outline)
            draw.arc([x1-2*r+i, y1-2*r+i, x1-i, y1-i], 0, 90, fill=outline)
            draw.line([x0+r, y0+i, x1-r, y0+i], fill=outline)
            draw.line([x0+r, y1-i, x1-r, y1-i], fill=outline)
            draw.line([x0+i, y0+r, x0+i, y1-r], fill=outline)
            draw.line([x1-i, y0+r, x1-i, y1-r], fill=outline)

rounded_rect(draw, margin, margin, SIZE-margin, SIZE-margin,
             r, fill=CARD, outline=MINT, width=8)

# ── mint top accent bar (full width, fixed height) ──
bar_h = 18
draw.rectangle([margin, margin, SIZE-margin, margin+bar_h], fill=MINT)

# ── NF letters — drawn as bold geometric shapes ──
# We'll draw them manually as rectangles/polygons for reliability
# N
cx = SIZE // 2
cy = SIZE // 2 - 30

stroke = 52
lh     = 320
lw     = stroke
gap    = 30
total  = lw*2 + gap*3 + lw   # two letters
start  = cx - total // 2

# ─ Letter N ─
nx = start
# left vertical
draw.rectangle([nx, cy - lh//2, nx + lw, cy + lh//2], fill=MINT)
# right vertical
draw.rectangle([nx + lw + gap*2, cy - lh//2,
                nx + lw + gap*2 + lw, cy + lh//2], fill=MINT)
# diagonal — drawn as a series of horizontal slices
diag_x0 = nx + lw
diag_x1 = nx + lw + gap*2
for row in range(lh):
    t  = row / lh
    x0 = int(diag_x0 + t * (diag_x1 - diag_x0))
    x1 = x0 + stroke // 2
    y  = (cy - lh//2) + row
    draw.rectangle([x0, y, x1, y+1], fill=MINT)

# ─ Letter F ─
letter_gap = gap * 4
fx = nx + lw + gap*2 + lw + letter_gap
# vertical bar
draw.rectangle([fx, cy - lh//2, fx + lw, cy + lh//2], fill=MINT)
# top horizontal
draw.rectangle([fx, cy - lh//2, fx + lw + gap*2 + lw, cy - lh//2 + stroke], fill=MINT)
# middle horizontal
draw.rectangle([fx, cy - stroke//2, fx + lw + gap + lw, cy + stroke//2], fill=MINT)

# ── tagline ──
try:
    font_tag = ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Futura.ttc", 52)
except Exception:
    try:
        font_tag = ImageFont.truetype(
            "/System/Library/Fonts/Helvetica.ttc", 52)
    except Exception:
        font_tag = ImageFont.load_default()

tag_text = "NEAT FREAK"
bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
tw = bbox[2] - bbox[0]
draw.text(((SIZE - tw) // 2, cy + lh//2 + 50),
          tag_text, font=font_tag, fill=CREAM)

# ── mint dot accent ──
dot_y = cy + lh//2 + 148
draw.ellipse([SIZE//2 - 12, dot_y, SIZE//2 + 12, dot_y + 24], fill=MINT)

img.save("icon.png", "PNG")
print("✓  icon.png created (1024×1024)")