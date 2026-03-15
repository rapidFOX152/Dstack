#!/bin/bash
# macOS: double-click to play DStacks
cd "$(dirname "$0")"

# Auto-install if venv missing
if [ ! -d "venv" ]; then
    echo " First run — running installer..."
    bash "Install DStacks.command"
fi

if [ ! -f "venv/bin/python" ]; then
    echo " ERROR: Installation incomplete."
    echo " Run 'Install DStacks.command' first."
    read -p " Press Enter to exit..."
    exit 1
fi

source venv/bin/activate
echo " Starting DStacks..."
python main.py
if [ $? -ne 0 ]; then
    echo ""
    echo " The game exited with an error. See above."
    read -p " Press Enter to close..."
fi
