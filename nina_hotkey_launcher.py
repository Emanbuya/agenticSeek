# nina_hotkey_launcher.py
"""
Nina Hotkey Launcher
Press Ctrl+Shift+N to launch Nina voice assistant
"""

import keyboard
import subprocess
import os
import sys
import time
import psutil

# Path to your Nina script
NINA_PATH = r"F:\AI_Projects\Intern\Jarvis_AI_Intern_Project\agentic_seek\nina_voice_optimized.py"

# Track if Nina is running
nina_process = None

def is_nina_running():
    """Check if Nina is already running"""
    global nina_process
    
    # Check our tracked process
    if nina_process and nina_process.poll() is None:
        return True
    
    # Also check by window title
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'nina_voice_optimized.py' in ' '.join(cmdline):
                return True
        except:
            pass
    
    return False

def launch_nina():
    """Launch Nina in a new console window"""
    global nina_process
    
    # Check if already running
    if is_nina_running():
        print("⚠️  Nina is already running!")
        return
    
    print("🚀 Launching Nina...")
    
    try:
        # Check if script exists
        if not os.path.exists(NINA_PATH):
            print(f"❌ Error: Nina script not found at {NINA_PATH}")
            return
        
        # Get Python executable from current environment
        python_exe = sys.executable
        
        # Launch in new console window
        nina_process = subprocess.Popen(
            [python_exe, NINA_PATH],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=os.path.dirname(NINA_PATH)  # Set working directory
        )
        
        print("✅ Nina launched successfully!")
        
    except Exception as e:
        print(f"❌ Error launching Nina: {e}")

def kill_nina():
    """Kill Nina process (Ctrl+Shift+K)"""
    global nina_process
    
    if nina_process and nina_process.poll() is None:
        print("🛑 Shutting down Nina...")
        nina_process.terminate()
        time.sleep(1)
        if nina_process.poll() is None:
            nina_process.kill()
        nina_process = None
        print("✅ Nina shut down")
    else:
        # Try to find and kill by name
        killed = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'nina_voice_optimized.py' in ' '.join(cmdline):
                    proc.terminate()
                    killed = True
                    print("✅ Nina process terminated")
            except:
                pass
        
        if not killed:
            print("⚠️  Nina is not running")

def show_status():
    """Show Nina status (Ctrl+Shift+S)"""
    if is_nina_running():
        print("✅ Nina is RUNNING")
    else:
        print("❌ Nina is NOT running")

def exit_launcher():
    """Exit the launcher (Ctrl+Shift+Q)"""
    print("👋 Exiting Nina Launcher...")
    if nina_process and nina_process.poll() is None:
        print("🛑 Shutting down Nina first...")
        nina_process.terminate()
    sys.exit(0)

# Print banner
print("""
╔══════════════════════════════════════════════╗
║          Nina Hotkey Launcher                ║
╟──────────────────────────────────────────────╢
║  Ctrl+Shift+N  - Launch Nina                 ║
║  Ctrl+Shift+K  - Kill Nina                   ║
║  Ctrl+Shift+S  - Show Status                 ║
║  Ctrl+Shift+Q  - Quit Launcher               ║
╚══════════════════════════════════════════════╝
""")

# Check if keyboard module has required permissions
try:
    # Register hotkeys
    keyboard.add_hotkey('ctrl+shift+n', launch_nina)
    keyboard.add_hotkey('ctrl+shift+k', kill_nina)
    keyboard.add_hotkey('ctrl+shift+s', show_status)
    keyboard.add_hotkey('ctrl+shift+q', exit_launcher)
    
    print("🔒 Hotkey listener active...")
    print("💡 Tip: Run as administrator for global hotkeys\n")
    
    # Keep running
    keyboard.wait()
    
except Exception as e:
    print(f"❌ Error setting up hotkeys: {e}")
    print("\n💡 Try running as administrator for global hotkey support")
    input("\nPress Enter to exit...")