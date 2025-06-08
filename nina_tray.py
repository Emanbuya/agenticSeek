# nina_tray.py
"""
Nina System Tray Icon
Click to launch, right-click for menu
"""

import sys
import os
import subprocess
import webbrowser
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
import threading

# Paths
PROJECT_PATH = r"F:\AI_Projects\Intern\Jarvis_AI_Intern_Project\agentic_seek"
LAUNCHER_PS1 = os.path.join(PROJECT_PATH, "nina_launcher.ps1")
NINA_VOICE_PY = os.path.join(PROJECT_PATH, "nina_voice_optimized.py")

class NinaTray:
    def __init__(self):
        self.icon = None
        self.nina_process = None
        self.create_icon()
        
    def create_icon(self):
        """Create the Nina icon"""
        # Create an icon image (or load existing)
        icon_path = os.path.join(PROJECT_PATH, "nina_icon.png")
        
        if not os.path.exists(icon_path):
            # Create a simple Nina icon
            self.create_nina_icon(icon_path)
        
        # Load the icon
        self.image = Image.open(icon_path)
        
        # Create the menu
        menu = pystray.Menu(
            item('🚀 Launch Everything', self.launch_all, default=True),
            item('🎤 Quick Voice Only', self.launch_voice),
            item('💻 Open VS Code', self.open_vscode),
            item('📊 API Dashboard', self.open_api),
            pystray.Menu.SEPARATOR,
            item('⚙️ Settings', self.open_settings),
            item('📁 Open Project', self.open_project),
            pystray.Menu.SEPARATOR,
            item('🛑 Stop All Services', self.stop_all),
            item('❌ Exit Nina', self.quit_nina)
        )
        
        # Create the system tray icon
        self.icon = pystray.Icon(
            "Nina AI Assistant",
            self.image,
            "Nina - Click to launch",
            menu
        )
    
    def create_nina_icon(self, path):
        """Create a simple Nina icon"""
        # Create 64x64 icon
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a stylized "N" with a circle
        # Background circle
        draw.ellipse([4, 4, size-4, size-4], fill='#FF1493', outline='#C71585', width=2)
        
        # Draw "N"
        try:
            # Try to use a nice font
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        # Center the N
        text = "N"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - 4
        
        draw.text((x, y), text, fill='white', font=font)
        
        # Add a small voice wave at bottom
        draw.arc([size//2-10, size-20, size//2+10, size-10], 0, 180, fill='white', width=2)
        
        img.save(path, 'PNG')
    
    def launch_all(self, icon=None, item=None):
        """Launch everything with PowerShell script"""
        print("🚀 Launching Nina Environment...")
        subprocess.Popen([
            "powershell", "-ExecutionPolicy", "Bypass", 
            "-File", LAUNCHER_PS1
        ], cwd=PROJECT_PATH)
        
        # Show notification
        self.icon.notify("Nina Environment Launching!", "All systems starting...")
    
    def launch_voice(self, icon=None, item=None):
        """Quick launch just Nina voice"""
        print("🎤 Launching Nina Voice...")
        
        cmd = [
            "cmd", "/c",
            "start", "Nina Voice",
            "cmd", "/k",
            f"cd /d {PROJECT_PATH} && "
            f"call C:\\Users\\erm72\\.conda\\envs\\agenticseek_env\\Scripts\\activate.bat && "
            f"python nina_voice_optimized.py"
        ]
        
        self.nina_process = subprocess.Popen(cmd, shell=True)
        self.icon.notify("Nina Voice Started", "Say 'Nina' to activate")
    
    def open_vscode(self, icon=None, item=None):
        """Open VS Code in project"""
        subprocess.Popen(["code", PROJECT_PATH])
    
    def open_api(self, icon=None, item=None):
        """Open API dashboard in browser"""
        webbrowser.open("http://localhost:8000")
    
    def open_settings(self, icon=None, item=None):
        """Open settings/config"""
        config_path = os.path.join(PROJECT_PATH, "config.ini")
        subprocess.Popen(["notepad", config_path])
    
    def open_project(self, icon=None, item=None):
        """Open project folder"""
        os.startfile(PROJECT_PATH)
    
    def stop_all(self, icon=None, item=None):
        """Stop all Nina services"""
        print("🛑 Stopping all services...")
        
        # Stop Python processes
        os.system('taskkill /F /IM python.exe /FI "WINDOWTITLE eq Nina*" 2>nul')
        
        # Stop Ollama
        os.system('taskkill /F /IM ollama.exe 2>nul')
        
        # Stop Docker containers
        os.system('docker stop searxng 2>nul')
        
        self.icon.notify("Services Stopped", "All Nina services have been stopped")
    
    def quit_nina(self, icon=None, item=None):
        """Quit the tray application"""
        self.stop_all()
        self.icon.stop()
    
    def run(self):
        """Run the system tray icon"""
        self.icon.run()


def main():
    """Main entry point"""
    print("""
    ╔══════════════════════════════════════════════╗
    ║         Nina System Tray Starting...         ║
    ╚══════════════════════════════════════════════╝
    
    Look for the Nina icon in your system tray!
    """)
    
    # Create and run tray icon
    tray = NinaTray()
    tray.run()


if __name__ == "__main__":
    main()