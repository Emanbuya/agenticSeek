"""
Nina Vision Module
Gives Nina the ability to see and understand what's on your screen
"""

import pyautogui
import pytesseract
import cv2
import numpy as np
import mss
import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
import time
from datetime import datetime
import io
import base64
import platform

# Configure Tesseract path for Windows
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ScreenVision:
    """Gives Nina eyes to see your screen"""
    
    def __init__(self, nina):
        self.nina = nina
        # Auto-detect primary monitor
        with mss.mss() as sct:
            self.monitor = sct.monitors[1]  # Primary monitor
        self.sct = mss.mss()
        
        # For AI vision, we'll need to integrate with vision models
        self.vision_enabled = False
        
    def capture_screen(self, region=None):
        """Capture entire screen or specific region"""
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = self.sct.grab(self.monitor)
            screenshot = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        
        return screenshot
    
    def capture_active_window(self):
        """Capture only the active window"""
        try:
            # Get active window handle
            hwnd = win32gui.GetForegroundWindow()
            
            # Get window rect
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Capture the window
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            return screenshot, window_title
        except Exception as e:
            print(f"Error capturing active window: {e}")
            return None, None
    
    def get_text_from_screen(self, image=None):
        """Extract text from screen using OCR"""
        if image is None:
            image = self.capture_screen()
        
        # Convert PIL image to opencv format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Preprocess for better OCR
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        # Threshold to get better text recognition
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # Extract text
        text = pytesseract.image_to_string(thresh)
        
        return text.strip()
    
    def find_element_on_screen(self, element_text):
        """Find specific UI element or text on screen"""
        try:
            # Use pytesseract to get bounding boxes of text
            screenshot = self.capture_screen()
            data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
            
            # Find the text
            for i, word in enumerate(data['text']):
                if element_text.lower() in word.lower():
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    return (x + w//2, y + h//2)  # Return center point
            
            return None
        except Exception as e:
            print(f"Error finding element: {e}")
            return None
    
    def analyze_with_ai(self, prompt="What do you see on the screen?"):
        """Use AI vision model to understand screen content"""
        # Capture screen
        screenshot = self.capture_screen()
        
        # Convert to base64 for AI models
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Here you would integrate with vision AI models like:
        # - OpenAI's GPT-4 Vision
        # - Claude's vision capabilities
        # - Local models like LLaVA
        
        # For now, return OCR text analysis
        text = self.get_text_from_screen(screenshot)
        return f"I can see text on the screen: {text[:500]}..."
    
    def describe_active_window(self):
        """Describe what Nina sees in the active window"""
        screenshot, window_title = self.capture_active_window()
        
        if not screenshot:
            return "I couldn't capture the active window."
        
        # Get text content
        text = self.get_text_from_screen(screenshot)
        
        # Analyze content type
        content_type = self.identify_content_type(window_title, text)
        
        # Build description
        description = f"You have {window_title} open. "
        
        if "Word" in window_title or ".docx" in window_title:
            word_count = len(text.split())
            description += f"I can see a Word document with approximately {word_count} words. "
            if text:
                preview = ' '.join(text.split()[:20])
                description += f"It starts with: '{preview}...'"
                
        elif "Excel" in window_title or ".xlsx" in window_title:
            description += "I can see an Excel spreadsheet. "
            # Could add cell detection here
            
        elif "Chrome" in window_title or "Firefox" in window_title or "Edge" in window_title:
            description += "I can see a web browser. "
            if "youtube" in window_title.lower():
                description += "You're on YouTube. "
            elif "gmail" in window_title.lower():
                description += "You're checking Gmail. "
                
        elif "Visual Studio" in window_title or "Code" in window_title:
            description += "I can see you're coding. "
            # Detect programming language
            if "def " in text or "import " in text:
                description += "Looks like Python code. "
            elif "function" in text or "const " in text:
                description += "Looks like JavaScript code. "
                
        else:
            description += f"The window contains: {text[:200]}..." if text else "I can't read any text from this window."
            
        return description
    
    def identify_content_type(self, window_title, text):
        """Identify what type of content is on screen"""
        window_lower = window_title.lower()
        
        if any(doc in window_lower for doc in ['.docx', '.doc', 'word']):
            return 'document'
        elif any(sheet in window_lower for sheet in ['.xlsx', '.xls', 'excel']):
            return 'spreadsheet'
        elif any(browser in window_lower for browser in ['chrome', 'firefox', 'edge']):
            return 'browser'
        elif any(code in window_lower for code in ['visual studio', 'code', 'pycharm', 'intellij']):
            return 'code_editor'
        elif any(term in window_lower for term in ['command prompt', 'powershell', 'terminal']):
            return 'terminal'
        else:
            return 'unknown'
    
    def monitor_screen_changes(self, callback, interval=1.0):
        """Monitor screen for changes and notify Nina"""
        last_screenshot = None
        
        while True:
            current_screenshot = self.capture_screen()
            
            if last_screenshot is not None:
                # Compare screenshots
                diff = self.compare_screenshots(last_screenshot, current_screenshot)
                if diff > 0.1:  # Significant change threshold
                    callback("Screen content has changed significantly")
            
            last_screenshot = current_screenshot
            time.sleep(interval)
    
    def compare_screenshots(self, img1, img2):
        """Compare two screenshots and return difference score"""
        # Convert to numpy arrays
        arr1 = np.array(img1)
        arr2 = np.array(img2)
        
        # Calculate difference
        diff = np.mean(np.abs(arr1 - arr2))
        return diff / 255.0  # Normalize to 0-1
    
    def read_document_content(self):
        """Read and understand document content"""
        screenshot, window_title = self.capture_active_window()
        
        if not screenshot:
            return None
            
        text = self.get_text_from_screen(screenshot)
        
        # Structure the content
        content = {
            'window': window_title,
            'type': self.identify_content_type(window_title, text),
            'text': text,
            'word_count': len(text.split()),
            'timestamp': datetime.now().isoformat()
        }
        
        return content
    
    def help_with_current_task(self):
        """Analyze what user is doing and offer help"""
        content = self.read_document_content()
        
        if not content:
            return "I can't see what you're working on."
        
        responses = {
            'document': self.help_with_document,
            'spreadsheet': self.help_with_spreadsheet,
            'code_editor': self.help_with_code,
            'browser': self.help_with_browsing,
            'terminal': self.help_with_terminal
        }
        
        helper = responses.get(content['type'], self.generic_help)
        return helper(content)
    
    def help_with_document(self, content):
        """Provide help for document editing"""
        text = content['text']
        word_count = content['word_count']
        
        # Analyze document
        suggestions = []
        
        # Check for common issues
        if text.isupper():
            suggestions.append("The text appears to be in all caps. Would you like me to fix the capitalization?")
        
        # Grammar suggestions would go here with NLP
        
        response = f"I see you're working on a document with {word_count} words. "
        if suggestions:
            response += " ".join(suggestions)
        else:
            response += "Let me know if you need help with editing, formatting, or proofreading."
            
        return response
    
    def help_with_code(self, content):
        """Provide help for coding"""
        text = content['text']
        
        # Detect language and offer relevant help
        if "def " in text and "import " in text:
            return "I see you're writing Python code. I can help with debugging, optimization, or explaining concepts."
        elif "function" in text or "const " in text:
            return "I see you're writing JavaScript. Need help with any functions or debugging?"
        else:
            return "I see you're coding. I can help with debugging, code review, or explaining concepts."
    
    def help_with_spreadsheet(self, content):
        """Provide help for spreadsheets"""
        return "I see you're working with a spreadsheet. I can help with formulas, data analysis, or creating charts."
    
    def help_with_browsing(self, content):
        """Provide help for web browsing"""
        window = content['window']
        if "youtube" in window.lower():
            return "I see you're on YouTube. Need me to summarize the video or find related content?"
        else:
            return "I see you're browsing the web. Need me to research something or summarize the page?"
    
    def help_with_terminal(self, content):
        """Provide help for terminal/command line"""
        return "I see you're in the terminal. Need help with commands or troubleshooting?"
    
    def generic_help(self, content):
        """Generic help for unknown content"""
        return "I can see your screen. How can I help with what you're working on?"


class ScreenAutomation:
    """Automate screen interactions"""
    
    def __init__(self, vision):
        self.vision = vision
        
    def click_on_text(self, text):
        """Click on specific text on screen"""
        location = self.vision.find_element_on_screen(text)
        if location:
            pyautogui.click(location[0], location[1])
            return True
        return False
    
    def type_text(self, text, delay=0.1):
        """Type text with human-like delay"""
        pyautogui.typewrite(text, interval=delay)
    
    def read_and_respond(self):
        """Read screen content and respond appropriately"""
        content = self.vision.read_document_content()
        
        if content['type'] == 'document':
            # Could help with writing
            pass
        elif content['type'] == 'spreadsheet':
            # Could help with formulas
            pass
        # etc...


# Integration with nina_handlers.py
def add_vision_commands(handlers):
    """Add vision-related commands to Nina's handlers"""
    
    # Add new intent handlers
    def handle_screen_query(command):
        """Handle 'what do you see' type queries"""
        description = handlers.vision.describe_active_window()
        handlers.nina.speak(description)
    
    def handle_help_request(command):
        """Handle 'help me with this' requests"""
        help_response = handlers.vision.help_with_current_task()
        handlers.nina.speak(help_response)
    
    def handle_training_command(command):
        """Handle training commands"""
        cmd_lower = command.lower()
        
        if "start training" in cmd_lower or "watch me" in cmd_lower:
            # Extract task name
            task_name = "general task"
            if "for" in cmd_lower:
                parts = cmd_lower.split("for")
                if len(parts) > 1:
                    task_name = parts[1].strip()
            
            handlers.training.start_training_session(task_name)
            
        elif "stop training" in cmd_lower or "done training" in cmd_lower:
            handlers.training.stop_training_session()
            
        elif "explain" in cmd_lower or "narrate" in cmd_lower:
            # Add narration
            narration = command.replace("explain", "").replace("narrate", "").strip()
            handlers.training.add_narration(narration)
            handlers.nina.speak("Got it, I've noted that.")
    
    def handle_automation_request(command):
        """Handle automation requests"""
        cmd_lower = command.lower()
        
        if "what can you do" in cmd_lower:
            tasks = handlers.customer_automation.list_available_tasks()
            response = "I can help with these tasks: " + ", ".join(tasks)
            handlers.nina.speak(response)
            
        elif "show me" in cmd_lower or "demonstrate" in cmd_lower:
            if "form" in cmd_lower:
                response = handlers.customer_automation.demo_form_filling()
            elif "document" in cmd_lower:
                response = handlers.customer_automation.demo_document_processing()
            elif "data" in cmd_lower or "spreadsheet" in cmd_lower:
                response = handlers.customer_automation.demo_data_entry()
            else:
                response = "I can demonstrate form filling, document processing, or data entry. Which would you like to see?"
            
            handlers.nina.speak(response)
    
    # Add handlers to command processor
    handlers.handle_screen_query = handle_screen_query
    handlers.handle_help_request = handle_help_request
    handlers.handle_training_command = handle_training_command
    handlers.handle_automation_request = handle_automation_request
    
    return handlers