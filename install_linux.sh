#!/bin/bash
# Linux: right-click → "Run as Program"  OR  bash install_linux.sh
cd "$(dirname "$0")"

clear
echo ""
echo " DStacks – Installer"
echo " ─────────────────────────────────────────────────────────"
echo ""

# ── Step 1: Find Python ────────────────────────────────────────────────────
echo "[1/4] Checking Python..."
PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$cmd" &>/dev/null; then
        OK=$("$cmd" -c "import sys; print(int(sys.version_info >= (3,9)))" 2>/dev/null)
        if [ "$OK" = "1" ]; then
            PYTHON="$cmd"
            VER=$("$cmd" --version)
            echo " Found: $VER"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo " ERROR: Python 3.9+ not found."
    echo " Install with:  sudo apt install python3  (Ubuntu/Debian)"
    echo "           or:  sudo dnf install python3  (Fedora)"
    echo ""
    read -p " Press Enter to exit..."
    exit 1
fi

# ── Step 2: Virtual environment ────────────────────────────────────────────
echo ""
echo "[2/4] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv || {
        echo " venv failed — trying with --without-pip..."
        $PYTHON -m venv venv --without-pip
        source venv/bin/activate
        curl https://bootstrap.pypa.io/get-pip.py | python
    }
    echo " Created ./venv"
else
    echo " Already exists — skipping."
fi

# ── Step 3: Install packages ───────────────────────────────────────────────
echo ""
echo "[3/4] Installing packages..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt || {
    echo " ERROR: pip install failed. Check internet connection."
    read -p " Press Enter to exit..."
    exit 1
}

# ── Step 4: Make launcher executable ──────────────────────────────────────
chmod +x "play_dstacks.sh" 2>/dev/null || true

echo ""
echo "[4/4] Verifying..."
python -c "import pygame, pymunk, numpy, scipy, cv2; print(' All packages OK')"

echo ""
echo " ─────────────────────────────────────────────────────────"
echo " Done!  Run the game with:  bash play_dstacks.sh"
echo " ─────────────────────────────────────────────────────────"
echo ""
read -p " Press Enter to close..."
