"""
Nina LLaVA Vision System
Advanced vision capabilities using LLaVA multimodal model
"""

import os
import base64
import requests
import json
from PIL import Image
import io
import mss
import win32gui
import subprocess
import time


class LLaVAVision:
    """Vision system using LLaVA for better understanding"""
    
    def __init__(self, nina):
        self.nina = nina
        self.sct = mss.mss()
        
        # Check if LLaVA is installed
        self.llava_available = self.check_llava()
        
        # Ollama API endpoint
        self.api_url = "http://localhost:11434/api/generate"
        
    def check_llava(self):
        """Check if LLaVA is installed in Ollama"""
        try:
            result = subprocess.run(
                ['ollama', 'list'], 
                capture_output=True, 
                text=True
            )
            return 'llava' in result.stdout.lower()
        except:
            return False
    
    def install_llava(self):
        """Install LLaVA model"""
        self.nina.speak("Installing LLaVA vision model. This will take a few minutes...")
        try:
            subprocess.run(['ollama', 'pull', 'llava:7b'], check=True)
            self.llava_available = True
            self.nina.speak("LLaVA vision model installed successfully!")
            return True
        except Exception as e:
            self.nina.speak(f"Failed to install LLaVA: {str(e)}")
            return False
    
    def capture_active_window(self):
        """Capture the active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            
            monitor = {
                "left": left,
                "top": top,
                "width": right - left,
                "height": bottom - top
            }
            
            screenshot = self.sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            window_title = win32gui.GetWindowText(hwnd)
            
            return img, window_title
        except Exception as e:
            print(f"Error capturing window: {e}")
            return None, None
    
    def image_to_base64(self, image):
        """Convert PIL image to base64"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def analyze_screen(self, prompt="What do you see on the screen?"):
        """Use LLaVA to analyze the screen"""
        if not self.llava_available:
            return "LLaVA vision model is not installed. Would you like me to install it?"
        
        # Capture screen
        screenshot, window_title = self.capture_active_window()
        if not screenshot:
            return "I couldn't capture the screen."
        
        # Convert to base64
        image_base64 = self.image_to_base64(screenshot)
        
        # Create request
        request_data = {
            "model": "llava:7b-v1.6-mistral-q4_0",
            "prompt": prompt,
            "images": [image_base64],
            "stream": False
        }
        
        try:
            # Send to Ollama
            response = requests.post(
                self.api_url,
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response from LLaVA')
            else:
                return f"Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "LLaVA took too long to respond. The image might be too complex."
        except Exception as e:
            return f"Error analyzing screen: {str(e)}"
    
    def describe_active_window(self):
        """Describe what's in the active window using LLaVA"""
        _, window_title = self.capture_active_window()
        
        # Customize prompt based on window
        if "Visual Studio Code" in window_title or "Code" in window_title:
            prompt = """You are looking at a code editor. Please describe:
1. What programming language is shown
2. What the code appears to do
3. Any visible errors or issues
4. The current line number if visible
5. Any highlighted text

Be specific and helpful."""
        
        elif "Word" in window_title:
            prompt = "Describe the document content, formatting, and any notable elements."
        
        elif "Chrome" in window_title or "Firefox" in window_title:
            prompt = "Describe the webpage, including the site name, content, and any notable elements."
        
        else:
            prompt = "Describe what you see on the screen in detail."
        
        return self.analyze_screen(prompt)
    
    def read_code(self):
        """Specifically read and analyze code on screen"""
        prompt = """You are looking at code in an editor. Please:
1. Identify the programming language
2. Read and transcribe the visible code
3. Explain what the code does
4. Identify any potential bugs or issues
5. Note any comments or documentation

Format your response clearly with the actual code in a code block."""
        
        return self.analyze_screen(prompt)
    
    def help_with_current_task(self):
        """Analyze screen and provide contextual help"""
        prompt = """Look at the screen and determine what the user is working on. 
Then provide specific, helpful suggestions for their current task. 
Consider:
- What application they're using
- What they appear to be trying to do
- Any errors or issues visible
- Helpful next steps

Be concise and actionable."""
        
        return self.analyze_screen(prompt)
    
    def find_and_read_text(self, target_text):
        """Find specific text on screen and read around it"""
        prompt = f"""Look for '{target_text}' on the screen. If you find it:
1. Read the text around it for context
2. Describe where it appears on screen
3. Explain what it relates to

If you don't see it, say so clearly."""
        
        return self.analyze_screen(prompt)


def upgrade_nina_vision(handlers):
    """Upgrade Nina's vision to use LLaVA"""
    
    # Create LLaVA vision instance
    llava_vision = LLaVAVision(handlers.nina)
    
    # Replace or supplement existing vision
    if hasattr(handlers, 'vision'):
        handlers.vision_original = handlers.vision
    
    handlers.vision = llava_vision
    
    # Override vision command handler
    def handle_screen_query_llava(command):
        """Handle vision queries with LLaVA"""
        cmd_lower = command.lower()
        
        # Install LLaVA if needed
        if not llava_vision.llava_available:
            if "install" in cmd_lower or "yes" in cmd_lower:
                llava_vision.install_llava()
                return
            else:
                handlers.nina.speak("I need the LLaVA vision model to see your screen properly. Say 'install llava' to set it up.")
                return
        
        # Different types of vision requests
        if "read" in cmd_lower and "code" in cmd_lower:
            response = llava_vision.read_code()
        elif "help" in cmd_lower:
            response = llava_vision.help_with_current_task()
        elif "find" in cmd_lower:
            # Extract what to find
            words = cmd_lower.split("find")[-1].strip().split()
            if words:
                target = " ".join(words)
                response = llava_vision.find_and_read_text(target)
            else:
                response = llava_vision.describe_active_window()
        else:
            response = llava_vision.describe_active_window()
        
        handlers.nina.speak(response)
    
    # Replace the handler
    handlers.handle_screen_query = handle_screen_query_llava
    
    print("✅ LLaVA vision system initialized")
    
    return handlers