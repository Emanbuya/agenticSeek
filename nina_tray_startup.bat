@echo off
REM nina_tray_startup.bat
REM Add this to Windows startup folder

cd /d "F:\AI_Projects\Intern\Jarvis_AI_Intern_Project\agentic_seek"

REM Start Nina tray icon in background
start /min "" "C:\Users\erm72\.conda\envs\agenticseek_env\python.exe" nina_tray.py

exit