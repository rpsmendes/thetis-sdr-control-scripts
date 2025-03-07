@echo off
cd /d "%~dp0"

REM Run the scripts in the background
start "" pythonw.exe thetis-midi-map.py
start "" pythonw.exe vfo-aimos.py

exit