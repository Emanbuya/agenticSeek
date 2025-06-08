@echo off
REM nina_ultimate_launcher.bat
REM Launches VS Code AND Nina in terminal with single hotkey

echo ╔══════════════════════════════════════════════╗
echo ║        Nina Development Environment          ║
echo ╚══════════════════════════════════════════════╝

REM Set project path
set PROJECT_PATH=F:\AI_Projects\Intern\Jarvis_AI_Intern_Project\agentic_seek
set CONDA_ENV=agenticseek_env

REM Change to project directory
cd /d "%PROJECT_PATH%"

REM Launch VS Code in the project folder (it will open in background)
echo [1/3] Opening VS Code...
start "" "code" "%PROJECT_PATH%"

REM Wait a moment for VS Code to start
timeout /t 2 /nobreak >nul

REM Open Windows Terminal with multiple tabs/panes
echo [2/3] Setting up Terminal...

REM Create a temporary PowerShell script for Windows Terminal
echo $projectPath = '%PROJECT_PATH%' > temp_terminal.ps1
echo $condaPath = 'C:\Users\erm72\.conda\envs\%CONDA_ENV%\Scripts\activate.bat' >> temp_terminal.ps1
echo. >> temp_terminal.ps1
echo # Launch Windows Terminal with split panes >> temp_terminal.ps1
echo $wtCommand = @' >> temp_terminal.ps1
echo wt -w 0 ` >> temp_terminal.ps1
echo   new-tab --title "Nina Voice" -d "%PROJECT_PATH%" cmd /k "call C:\Users\erm72\.conda\envs\%CONDA_ENV%\Scripts\activate.bat && python nina_voice_optimized.py" `; ` >> temp_terminal.ps1
echo   split-pane -H --title "Ollama" -d "%PROJECT_PATH%" cmd /k "ollama serve" `; ` >> temp_terminal.ps1
echo   split-pane -V --title "Docker" -d "%PROJECT_PATH%" cmd /k "docker ps" `; ` >> temp_terminal.ps1
echo   focus-tab -t 0 >> temp_terminal.ps1
echo '@ >> temp_terminal.ps1
echo. >> temp_terminal.ps1
echo Invoke-Expression $wtCommand >> temp_terminal.ps1

REM Execute the PowerShell script
powershell -ExecutionPolicy Bypass -File temp_terminal.ps1

REM Clean up
del temp_terminal.ps1

REM If Windows Terminal is not installed, fall back to regular console
if %ERRORLEVEL% neq 0 (
    echo Windows Terminal not found, using standard console...
    
    REM Terminal 1: Nina
    start "Nina Voice Assistant" cmd /k "call C:\Users\erm72\.conda\envs\%CONDA_ENV%\Scripts\activate.bat && echo Nina Voice Assistant && echo ================== && python nina_voice_optimized.py"
    
    REM Terminal 2: Ollama
    start "Ollama Server" cmd /k "echo Ollama Server && echo ============= && ollama serve"
    
    REM Terminal 3: Docker status
    start "Docker Status" cmd /k "echo Docker Status && echo ============= && docker ps -a"
)

echo.
echo [3/3] All systems launched!
echo.
echo ╔══════════════════════════════════════════════╗
echo ║  VS Code    : ✓ Open                         ║
echo ║  Nina Voice : ✓ Starting...                  ║
echo ║  Ollama     : ✓ Starting...                  ║
echo ║  Docker     : ✓ Status Check                 ║
echo ╚══════════════════════════════════════════════╝
echo.
echo Press any key to close this launcher...
pause >nul