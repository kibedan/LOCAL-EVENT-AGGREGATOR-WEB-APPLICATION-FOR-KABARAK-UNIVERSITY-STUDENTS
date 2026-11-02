@echo off
cd /d "%~dp0backend"
if not exist aggregator.db (
  echo First run: creating the database...
  py scripts\seed.py
)
set AGGREGATOR_DEBUG=0
rem Open the browser after a short pause, once the server is listening.
start "" /min cmd /c "timeout /t 4 >nul & start http://localhost:5000"
title KABU Events server - close this window to stop the system
py run.py
