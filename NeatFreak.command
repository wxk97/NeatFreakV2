#!/bin/bash
# ═══════════════════════════════════════════════════
#  NEAT FREAK — Double-click launcher
#  Keep this file in the SAME folder as NeatFreak.py
# ═══════════════════════════════════════════════════
#
#  ONE-TIME SETUP (run once in Terminal, then never again):
#
#    chmod +x "NeatFreak.command"
#
#  After that, just double-click this file to launch the app.
# ═══════════════════════════════════════════════════

# Go to the folder this launcher lives in (same as NeatFreak.py)
cd "$(dirname "$0")"

# Find the best available Python (Homebrew first — it has modern Tk)
PYTHON=""
for candidate in \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    /opt/homebrew/bin/python3.13 \
    /opt/homebrew/bin/python3.12 \
    /opt/homebrew/bin/python3.11 \
    "$(which python3 2>/dev/null)"; do
    if [ -x "$candidate" ]; then
        PYTHON="$candidate"
        break
    fi
done

# No Python found
if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "Python 3 not found" message "Install it with:\n\nbrew install python-tk" as critical'
    exit 1
fi

# Tkinter not available
$PYTHON -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    osascript -e 'display alert "Tkinter missing" message "Run this in Terminal:\n\nbrew install python-tk" as critical'
    exit 1
fi

# NeatFreak.py not found next to this file
if [ ! -f "NeatFreak.py" ]; then
    osascript -e 'display alert "NeatFreak.py not found" message "Make sure NeatFreak.command and NeatFreak.py are in the same folder." as critical'
    exit 1
fi

# Launch
$PYTHON NeatFreak.py
