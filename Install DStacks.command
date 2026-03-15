#!/bin/bash
# macOS: double-click this file to install DStacks
# (Right-click → Open the first time if Gatekeeper blocks it)

cd "$(dirname "$0")"   # always run from the folder containing this script

clear
echo ""
echo " ██████╗ ███████╗████████╗ █████╗  ██████╗██╗  ██╗███████╗"
echo " ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝██╔════╝"
echo " ██║  ██║███████╗   ██║   ███████║██║     █████╔╝ ███████╗ "
echo " ██║  ██║╚════██║   ██║   ██╔══██║██║     ██╔═██╗ ╚════██║ "
echo " ██████╔╝███████║   ██║   ██║  ██║╚██████╗██║  ██╗███████║ "
echo " ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝"
echo ""
echo " ─────────────────────────────────────────────────────────"
echo " Installer — this will set everything up automatically"
echo " ─────────────────────────────────────────────────────────"
echo ""

# ── Step 1: Find Python 3.9+ ───────────────────────────────────────────────
echo "[1/4] Checking Python installation..."
PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3.9 python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        OK=$("$cmd" -c "import sys; print(int(sys.version_info >= (3,9)))" 2>/dev/null)
        if [ "$OK" = "1" ]; then
            PYTHON="$cmd"
            echo " Found: $cmd  ($VER)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo " ERROR: Python 3.9 or newer not found."
    echo ""
    echo " Install it from:  https://www.python.org/downloads/"
    echo " Or via Homebrew:  brew install python"
    echo ""
    read -p " Press Enter to exit..."
    exit 1
fi

# ── Step 2: Virtual environment ────────────────────────────────────────────
echo ""
echo "[2/4] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv || { echo " ERROR: venv creation failed."; read -p "Press Enter..."; exit 1; }
    echo " Created ./venv"
else
    echo " Already exists — skipping."
fi

# ── Step 3: Install packages ───────────────────────────────────────────────
echo ""
echo "[3/4] Installing packages (may take a minute)..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt || {
    echo ""
    echo " ERROR: Package installation failed."
    echo " Check your internet connection and try again."
    read -p " Press Enter to exit..."
    exit 1
}

# ── Step 4: Verify & done ─────────────────────────────────────────────────
echo ""
echo "[4/4] Verifying..."
python -c "import pygame, pymunk, numpy, scipy, cv2; print(' All packages OK')"

echo ""
echo " ─────────────────────────────────────────────────────────"
echo " Installation complete!"
echo ""
echo " Double-click  'Play DStacks.command'  to start the game."
echo " ─────────────────────────────────────────────────────────"
echo ""
read -p " Press Enter to close..."
