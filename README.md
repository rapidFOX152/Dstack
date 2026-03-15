# DStacks 🎮

A two-player physics stacking game. Take turns dropping character tiles onto a bar — stack them as high as you can without falling off!

---

## ▶ Quick Start (No terminal needed)

### Windows
1. Double-click **`Install DStacks.bat`** — sets everything up automatically
2. Double-click **`Play DStacks.bat`** — launches the game

### macOS
1. Double-click **`Install DStacks.command`**
   > First time only: right-click → **Open** to bypass Gatekeeper
2. Double-click **`Play DStacks.command`** — launches the game

### Linux
```bash
bash install_linux.sh   # one-time setup
bash play_dstacks.sh    # play
```
Or right-click each `.sh` file → **Run as Program** in your file manager.

---

## Controls

| Action | Keyboard | Mouse |
|---|---|---|
| Move tile left/right | ← → | Drag |
| Rotate tile | Shift | ROTATE button |
| Drop tile | Space | DROP button |
| Toggle debug view | D | — |
| Toggle music | M | — |
| Restart (game over) | Enter | — |

---

## Requirements

- Python 3.9 or newer — [python.org](https://www.python.org/downloads/)
- The installers handle everything else automatically

Manual install (if you prefer):
```bash
pip install -r requirements.txt
python main.py
```

---

## Project Structure

```
DStacks/
├── main.py                    # Game (run this)
├── requirements.txt           # Python dependencies
│
├── Install DStacks.bat        # Windows installer
├── Play DStacks.bat           # Windows launcher
├── Install DStacks.command    # macOS installer
├── Play DStacks.command       # macOS launcher
├── install_linux.sh           # Linux installer
├── play_dstacks.sh            # Linux launcher
│
└── assets/
    ├── data/tiles.json        # Tile collision shapes
    └── images/tiles/          # Character PNG cutouts
```

---

## Adding New Tiles

Drop any PNG with a black background into `assets/images/tiles/`, then regenerate the collision data:

```bash
python generate_tiles.py
```

---

*Built with pygame + pymunk*
