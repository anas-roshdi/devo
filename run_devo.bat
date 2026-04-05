@echo off
title Devo System Launcher
echo Starting Devo Business Management System...
echo Checking environment...

# This command runs your main dashboard file
python main.py

# If there is an error, the window stays open so you can read it
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] System failed to start. Check if Python is installed and file names are correct.
    pause
)