#!/bin/bash
# Get the directory where this script is located
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Run the game using the Python from the virtual environment
"$DIR/venv~/bin/python" "$DIR/main.py"
