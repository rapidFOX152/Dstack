@echo off
title DStacks
color 0A
cls

:: Auto-install if venv missing
if not exist "venv" (
    echo  First run detected — running installer...
    echo.
    call "Install DStacks.bat"
)

:: Check again after potential install
if not exist "venv\Scripts\python.exe" (
    echo  ERROR: Installation incomplete. Run "Install DStacks.bat" first.
    pause
    exit /b 1
)

:: Launch the game (window title stays, errors are visible)
call venv\Scripts\activate.bat
echo  Starting DStacks...
python main.py
if errorlevel 1 (
    echo.
    echo  The game exited with an error. See message above.
    pause
)
