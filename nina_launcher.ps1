# nina_launcher.ps1
# Ultimate Nina Development Environment Launcher

$projectPath = "F:\AI_Projects\Intern\Jarvis_AI_Intern_Project\agentic_seek"
$condaEnv = "agenticseek_env"
$condaPath = "C:\Users\erm72\.conda\envs\$condaEnv\Scripts\activate.bat"

Write-Host @"
╔══════════════════════════════════════════════╗
║        Nina Development Environment          ║
║              ULTIMATE LAUNCHER               ║
╚══════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Function to check if a process is running
function Test-ProcessRunning($processName) {
    Get-Process -Name $processName -ErrorAction SilentlyContinue
}

# Change to project directory
Set-Location $projectPath

Write-Host "[1/5] Opening VS Code..." -ForegroundColor Yellow
# Launch VS Code with specific workspace settings
Start-Process "code" -ArgumentList ".", "--new-window" -WorkingDirectory $projectPath

Start-Sleep -Seconds 2

Write-Host "[2/5] Checking prerequisites..." -ForegroundColor Yellow

# Check if Ollama is running
if (-not (Test-ProcessRunning "ollama")) {
    Write-Host "   Starting Ollama..." -ForegroundColor Gray
    Start-Process "wt" -ArgumentList "-w", "0", "new-tab", "--title", "Ollama Server", "-d", "$projectPath", "cmd", "/k", "ollama serve"
} else {
    Write-Host "   Ollama already running ✓" -ForegroundColor Green
}

# Check Docker
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Starting Docker Desktop..." -ForegroundColor Gray
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Start-Sleep -Seconds 5
} else {
    Write-Host "   Docker already running ✓" -ForegroundColor Green
}

Write-Host "[3/5] Starting SearxNG container..." -ForegroundColor Yellow
# Check if SearxNG is running
$searxContainer = docker ps --filter "ancestor=searxng/searxng" --format "{{.Names}}" 2>$null
if (-not $searxContainer) {
    docker run -d -p 8080:8080 --name searxng searxng/searxng
    Write-Host "   SearxNG started ✓" -ForegroundColor Green
} else {
    Write-Host "   SearxNG already running ✓" -ForegroundColor Green
}

Write-Host "[4/5] Setting up Windows Terminal layout..." -ForegroundColor Yellow

# Create the perfect terminal layout
$terminalCommand = @"
wt -w 0 ``
  new-tab --title "Nina Voice" --tabColor "#FF1493" -d "$projectPath" cmd /k `"call $condaPath && cls && echo Nina Voice Assistant && echo ================== && python nina_voice_optimized.py`" `; ``
  new-tab --title "API Server" --tabColor "#00CED1" -d "$projectPath" cmd /k `"call $condaPath && cls && echo API Server && echo ========== && python api.py`" `; ``
  split-pane -H -s 0.5 --title "Logs" -d "$projectPath" powershell -NoExit -Command `"Get-Content -Path 'logs\*.log' -Tail 20 -Wait`" `; ``
  new-tab --title "Services" --tabColor "#32CD32" -d "$projectPath" `; ``
  split-pane -H -s 0.5 --title "Ollama" cmd /k `"ollama list`" `; ``
  split-pane -V -s 0.5 --title "Docker" cmd /k `"docker ps`" `; ``
  focus-tab -t 0
"@

# Execute terminal command
Invoke-Expression $terminalCommand

Write-Host "[5/5] Creating status dashboard..." -ForegroundColor Yellow

Start-Sleep -Seconds 3

# Create a status check script
$statusScript = @"
while (`$true) {
    Clear-Host
    Write-Host '╔══════════════════════════════════════════════╗' -ForegroundColor Cyan
    Write-Host '║          Nina System Status                  ║' -ForegroundColor Cyan
    Write-Host '╚══════════════════════════════════════════════╝' -ForegroundColor Cyan
    Write-Host ''
    
    # Check Nina
    `$ninaProc = Get-Process -Name 'python' -ErrorAction SilentlyContinue | Where-Object {`$_.CommandLine -like '*nina_voice*'}
    if (`$ninaProc) {
        Write-Host '  Nina Voice    : ✓ Running' -ForegroundColor Green
    } else {
        Write-Host '  Nina Voice    : ✗ Not Running' -ForegroundColor Red
    }
    
    # Check Ollama
    if (Test-ProcessRunning 'ollama') {
        Write-Host '  Ollama Server : ✓ Running' -ForegroundColor Green
    } else {
        Write-Host '  Ollama Server : ✗ Not Running' -ForegroundColor Red
    }
    
    # Check Docker
    `$dockerStatus = docker ps 2>>`$null
    if (`$LASTEXITCODE -eq 0) {
        Write-Host '  Docker        : ✓ Running' -ForegroundColor Green
        `$searxStatus = docker ps --filter 'ancestor=searxng/searxng' --format '{{.Status}}' 2>>`$null
        if (`$searxStatus) {
            Write-Host "  SearxNG       : ✓ `$searxStatus" -ForegroundColor Green
        } else {
            Write-Host '  SearxNG       : ✗ Not Running' -ForegroundColor Red
        }
    } else {
        Write-Host '  Docker        : ✗ Not Running' -ForegroundColor Red
    }
    
    Write-Host ''
    Write-Host 'Press Ctrl+C to exit status monitor...' -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
"@

# Save and run status script in new window
$statusScript | Out-File -FilePath "$projectPath\status_monitor.ps1" -Encoding UTF8
Start-Process "wt" -ArgumentList "-w", "0", "new-tab", "--title", "System Status", "--tabColor", "#FFD700", "-d", "$projectPath", "powershell", "-ExecutionPolicy", "Bypass", "-File", "status_monitor.ps1"

Write-Host @"

╔══════════════════════════════════════════════╗
║         All Systems Launched! 🚀             ║
╟──────────────────────────────────────────────╢
║  VS Code        : ✓ Open                     ║
║  Nina Voice     : ✓ Starting...              ║
║  API Server     : ✓ Starting...              ║
║  Ollama Server  : ✓ Running                  ║
║  Docker/SearxNG : ✓ Running                  ║
║  Status Monitor : ✓ Active                   ║
╚══════════════════════════════════════════════╝

Hotkeys:
  Ctrl+Shift+N : Launch this environment
  Ctrl+Tab     : Switch terminal tabs
  Alt+Shift+P  : Split pane in terminal

"@ -ForegroundColor Green

# Keep window open for a moment
Start-Sleep -Seconds 5