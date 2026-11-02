@echo off
title KABU Events - first-time setup
cd /d "%~dp0backend"
echo Installing the Python packages (one time only)...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Installation failed. See the message above.
  pause
  exit /b 1
)
echo.
echo Creating the database with demonstration accounts...
py scripts\seed.py
echo.
echo Setup complete. From now on, just double-click start.bat.
pause
