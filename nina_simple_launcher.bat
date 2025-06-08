@echo off
REM nina_simple_launcher.bat
REM Simple and reliable launcher for Nina

echo ===============================================
echo         Nina AI Assistant Launcher
echo ===============================================

cd /d "F:\AI_Projects\Intern\Jarvis_AI_Intern_Project\agentic_seek"

echo.
echo [1/4] Opening VS Code...
start "" "code" .

timeout /t 2 /nobreak >nul

echo [2/4] Starting Ollama Server...
start "Ollama Server" cmd /k "ollama serve"

timeout /t 2 /nobreak >nul

echo [3/4] Starting Docker/SearxNG...
start "Docker Check" cmd /k "docker ps && echo. && echo Starting SearxNG... && docker run -d -p 8080:8080 --name searxng searxng/searxng 2>nul || echo SearxNG already running"

timeout /t 2 /nobreak >nul

echo [4/4] Starting Nina Voice Assistant...
start "Nina Voice Assistant" cmd /k "call C:\Users\erm72\.conda\envs\agenticseek_env\Scripts\activate.bat && cls && echo Nina Voice Assistant && echo ================== && echo. && python nina_voice_optimized.py"

echo.
echo ===============================================
echo All systems launched successfully!
echo ===============================================
echo.
echo Window Summary:
echo - VS Code: Development Environment
echo - Ollama: Language Model Server
echo - Docker: Search Engine Container
echo - Nina: Voice Assistant
echo.
echo Close this window anytime...
timeout /t 5 >nul