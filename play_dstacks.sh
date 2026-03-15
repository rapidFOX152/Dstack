#!/bin/bash
# Linux: bash play_dstacks.sh  OR  right-click → Run as Program
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "First run — running installer..."
    bash install_linux.sh
fi

source venv/bin/activate
python main.py
if [ $? -ne 0 ]; then
    echo ""
    echo "Game exited with an error."
    read -p "Press Enter to close..."
fi
