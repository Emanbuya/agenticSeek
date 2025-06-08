# nina_hotkey_ultimate.py
"""
Nina Ultimate Hotkey Launcher
One hotkey to rule them all!
"""

import keyboard
import subprocess
import os
import sys

# Paths
PROJECT_PATH = r"F:\AI_Projects\Intern\Jarvis_AI_Intern_Project\agentic_seek"
LAUNCHER_SCRIPT = os.path.join(PROJECT_PATH, "nina_launcher.ps1")

def launch_everything():
    """Launch the entire Nina development environment"""
    print("🚀 Launching Nina Ultimate Environment...")
    
    # Use PowerShell to run our ultimate launcher
    cmd = [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", LAUNCHER_SCRIPT
    ]
    
    subprocess.Popen(cmd, cwd=PROJECT_PATH)
    print("✅ Environment launching... Check your screen!")

def quick_nina():
    """Just launch Nina voice (Ctrl+Shift+V)"""
    print("🎤 Quick launching Nina Voice only...")
    cmd = [
        "wt", "-w", "0",
        "new-tab", "--title", "Nina Voice Quick",
        "-d", PROJECT_PATH,
        "cmd", "/k",
        f"call C:\\Users\\erm72\\.conda\\envs\\agenticseek_env\\Scripts\\activate.bat && python nina_voice_optimized.py"
    ]
    subprocess.Popen(cmd)

def stop_all():
    """Stop all Nina services (Ctrl+Shift+X)"""
    print("🛑 Stopping all services...")
    
    # Kill Python processes running Nina
    os.system('taskkill /F /IM python.exe /FI "WINDOWTITLE eq Nina*" 2>nul')
    
    # Stop Ollama
    os.system('taskkill /F /IM ollama.exe 2>nul')
    
    # Stop Docker containers
    os.system('docker stop searxng 2>nul')
    
    print("✅ All services stopped")

print("""
╔══════════════════════════════════════════════════════╗
║           Nina Ultimate Hotkey Launcher              ║
╟──────────────────────────────────────────────────────╢
║  Ctrl+Shift+N : Launch EVERYTHING                    ║
║  Ctrl+Shift+V : Quick launch Nina Voice only         ║
║  Ctrl+Shift+X : Stop all services                    ║
║  Ctrl+Shift+Q : Quit this launcher                   ║
╚══════════════════════════════════════════════════════╝

🔒 Hotkeys active... Waiting for your command!
""")

# Register hotkeys
keyboard.add_hotkey('ctrl+shift+n', launch_everything)
keyboard.add_hotkey('ctrl+shift+v', quick_nina)
keyboard.add_hotkey('ctrl+shift+x', stop_all)
keyboard.add_hotkey('ctrl+shift+q', lambda: sys.exit(0))

# Keep running
try:
    keyboard.wait()
except KeyboardInterrupt:
    print("\n👋 Exiting hotkey launcher...")
    sys.exit(0)