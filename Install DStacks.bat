@echo off
title DStacks – Installer
color 0A
cls

echo.
echo  ██████╗ ███████╗████████╗ █████╗  ██████╗██╗  ██╗███████╗
echo  ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝██╔════╝
echo  ██║  ██║███████╗   ██║   ███████║██║     █████╔╝ ███████╗
echo  ██║  ██║╚════██║   ██║   ██╔══██║██║     ██╔═██╗ ╚════██║
echo  ██████╔╝███████║   ██║   ██║  ██║╚██████╗██║  ██╗███████║
echo  ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝
echo.
echo  ─────────────────────────────────────────────────────────
echo  Installer  —  this will set everything up automatically
echo  ─────────────────────────────────────────────────────────
echo.

:: ── Step 1: Check Python ────────────────────────────────────────────────────
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python was not found on your system.
    echo.
    echo  Please install Python 3.9 or newer from:
    echo    https://www.python.org/downloads/
    echo.
    echo  Make sure to tick "Add Python to PATH" during installation,
    echo  then double-click this installer again.
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  Found: %PY_VER%

:: ── Step 2: Create virtual environment ─────────────────────────────────────
echo.
echo [2/4] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
    echo  Created venv\
) else (
    echo  Virtual environment already exists — skipping.
)

:: ── Step 3: Install packages ─────────────────────────────────────────────
echo.
echo [3/4] Installing packages (this may take a minute)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  ERROR: Package installation failed.
    echo  Check your internet connection and try again.
    pause
    exit /b 1
)

:: ── Step 4: Done ─────────────────────────────────────────────────────────
echo.
echo [4/4] Verifying installation...
python -c "import pygame, pymunk, numpy, scipy, cv2; print('  All packages OK')"
if errorlevel 1 (
    echo  WARNING: Some packages may not have installed correctly.
)

echo.
echo  ─────────────────────────────────────────────────────────
echo  Installation complete!
echo.
echo  Double-click  "Play DStacks.bat"  to start the game.
echo  ─────────────────────────────────────────────────────────
echo.
pause
