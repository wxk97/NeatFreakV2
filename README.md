# 📸 Neat Freak

> Obsessively organised. Every pixel. Every file.

A macOS app that automatically sorts your photos and videos into tidy **Year / Month / Day** folders based on when they were actually filmed — not when they were copied.
```
2026/
  3-March/
    14/
      IMG_1234.jpg
      VID_0012.mp4
```

## Features

- Reads actual shot date from EXIF and video metadata
- Falls back to file modification date if metadata is unavailable
- Skips files already copied (same name + same size)
- Renames duplicates with different content instead of overwriting
- Copy or Move mode — your choice
- Dry-run preview before committing anything
- Clean dark UI with live progress bar and activity log

## Requirements
```bash
brew install python-tk
pip3 install pillow hachoir   # optional but recommended
```

## Run
```bash
python3 NeatFreak.py
```

Or double-click `NeatFreak.command` after running:
```bash
chmod +x NeatFreak.command
```

## Background

Started as a rough script in 2 quickly transfer vlog footage off a camera.
Rebuilt in 2026 as a full macOS desktop app with a proper UI.
