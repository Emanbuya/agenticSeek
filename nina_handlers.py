"""
Nina Command Handlers
Handles all the different types of commands and intents
"""

import os
import re
import platform
import subprocess
import asyncio
from datetime import datetime, date, timedelta
from pathlib import Path

from nina_utils import quiet, convert_spoken_symbols, fix_voice_recognition_errors
from nina_intent import IntentDetector
from nina_tech import TechCommands


class CommandHandlers:
    """Handles all command processing and execution"""
    
    def __init__(self, nina):
        self.nina = nina
        self.intent_detector = IntentDetector(nina.personal_config)
        self.tech_commands = TechCommands(nina)
        
        # Initialize vision and python_fixer to None first
        self.vision = None
        self.python_fixer = None
        
        # Initialize advanced features
        self._init_advanced_features()
        
    def _init_advanced_features(self):
        """Initialize advanced features like vision and code fixing"""
        # Try to import and initialize vision system
        try:
            from nina_vision import ScreenVision, ScreenAutomation, add_vision_commands
            from nina_intern_mode import InternTraining, CustomerTaskAutomation
            
            self.vision = ScreenVision(self.nina)
            self.automation = ScreenAutomation(self.vision)
            self.training = InternTraining(self.nina, self.vision)
            self.customer_automation = CustomerTaskAutomation(self.nina, self.vision, self.training)
            
            # Add vision commands
            add_vision_commands(self)
            
            print("✅ Vision system initialized")
        except ImportError as e:
            print(f"⚠️ Vision system not available: {e}")
            print("   Install with: pip install pyautogui pytesseract opencv-python mss pywin32")
            self.vision = None
        except Exception as e:
            print(f"❌ Vision system error: {e}")
            self.vision = None
            
        # Try to import LLaVA vision
        try:
         from nina_llava_vision import upgrade_nina_vision
         upgrade_nina_vision(self)
         print("✅ LLaVA vision system initialized")
        except ImportError as e:
         print(f"⚠️ LLaVA vision not available: {e}")    
            
        # Try to import and initialize Python fixer
        try:
            from nina_python_fixer import PythonCodeFixer, PythonCodeHelper, add_python_fixer_to_nina
            
            self.python_fixer = PythonCodeFixer(self.nina)
            self.python_helper = PythonCodeHelper(self.nina, self.python_fixer)
            
            # Add Python fixer commands
            add_python_fixer_to_nina(self)
            
            print("✅ Python code fixer initialized")
        except ImportError as e:
            print(f"⚠️ Python fixer not available: {e}")
            print("   Install with: pip install autopep8 black isort pyflakes pylint astunparse")
            self.python_fixer = None
        except Exception as e:
            print(f"❌ Python fixer error: {e}")
            self.python_fixer = None
        
    def process_command(self, command):
        """Main command processing entry point"""
        # Speech-to-text conversions
        command = convert_spoken_symbols(command)
        command = fix_voice_recognition_errors(command)
        
        # Exit check
        if any(word in command.lower() for word in ["stop", "exit", "goodbye", "quit", "bye"]):
            self.nina.is_running = False
            return
            
        # Check for vision commands
        if self._is_vision_command(command):
            if self.vision:
                self._handle_vision_command(command)
            else:
                self.nina.speak("The vision system is not available. Please install the required packages.")
            return
            
        # Check for Python fixing commands
        if self._is_python_fix_command(command):
            if self.python_fixer:
                self.handle_fix_python(command)
            else:
                self.nina.speak("The Python code fixer is not available. Please install the required packages.")
            return
            
        # Check for schedule queries FIRST
        if self.intent_detector.is_schedule_query(command):
            self.handle_schedule_query(command)
            return
            
        # Determine intent
        intent = self.intent_detector.determine_intent(command)
        
        print(f"🎯 Intent: {intent} | Command: {command}")
        
        # Feedback messages
        feedback = {
            "hardware": "Let me check that for you...",
            "llm_management": "Managing language models...",
            "weather": "Let me check the weather...",
            "time": "Checking the time...",
            "files": "I'll search for that " + ("folder..." if "folder" in command.lower() else "file..."),
            "folder": "I'll open that folder for you...",
            "open_file": "I'll open that file for you...",
            "open_quick_file": "I'll open that file for you...",
            "open_website": "I'll open that website...",
            "open_app": "I'll launch that application...",
            "code": "I'll write that code for you...",
            "search": "Let me search for that...",
            "sports": "Let me find the latest sports results...",
            "news": "I'll get the latest news for you...",
            "tech": "Processing technical command...",
            "vision": "Let me see what's on your screen...",
            "fix_python": "I'll check your Python code...",
            "general": "Let me help with that..."
        }
        
        self.nina.speak(feedback.get(intent, "Processing..."))
        
        # Direct handlers (no agent needed)
        direct_handlers = {
            "folder": self.handle_folder_operation,
            "open_file": self.handle_file_open,
            "open_app": self.handle_app_launch,
            "open_quick_file": self.handle_quick_file,
            "open_website": self.handle_website,
            "llm_management": lambda cmd: self.handle_llm_switch(cmd) if hasattr(self, 'handle_llm_switch') else self.nina.speak("LLM switching not available"),
            "weather": self.handle_weather_query,
            "time": self.handle_time_query,
            "news": self.handle_news_query,
            "sports": self.handle_sports_query,
            "tech": self.handle_tech_command,
            "vision": self._handle_vision_command,
            "fix_python": self.handle_fix_python,
        }
        
        if intent in direct_handlers:
            # Special handling for vision and fix_python
            if intent == "vision" and not self.vision:
                self.nina.speak("The vision system is not available.")
                return
            elif intent == "fix_python" and not self.python_fixer:
                self.nina.speak("The Python fixer is not available.")
                return
            
            direct_handlers[intent](command)
            return
            
        # All other intents use agents
        agent = self.get_agent_by_intent(intent)
        if agent:
            self.process_with_agent(agent, command, intent)
        else:
            self.nina.speak("I'm having trouble with that request.")
    
    def _is_vision_command(self, command):
        """Check if this is a vision-related command"""
        cmd_lower = command.lower()
        vision_keywords = [
            "what do you see", "look at", "can you see", "show me what",
            "help me with this", "help with current",
            "start training", "stop training", "watch me",
            "demonstrate", "what can you do for",
            "fix the screen", "read the screen",
            "what screen", "what's on my screen", "what am i looking at"
        ]
        return any(keyword in cmd_lower for keyword in vision_keywords)
    
    def _is_python_fix_command(self, command):
        """Check if this is a Python fixing command"""
        cmd_lower = command.lower()
        return ("fix" in cmd_lower and 
                any(word in cmd_lower for word in ["python", "code", "file", "indentation"])) or \
               ("explain" in cmd_lower and "error" in cmd_lower) or \
               any(word in cmd_lower for word in ["template", "boilerplate"])
    
    def _handle_vision_command(self, command):
        """Handle vision-related commands"""
        if not self.vision:
            self.nina.speak("The vision system is not available. Please install pyautogui, pytesseract, and opencv-python.")
            return
            
        cmd_lower = command.lower()
        
        if "what do you see" in cmd_lower or "look at" in cmd_lower or "what screen" in cmd_lower:
            self.handle_screen_query(command)
        elif "help me with this" in cmd_lower or "help with current" in cmd_lower:
            self.handle_help_request(command)
        elif "training" in cmd_lower or "watch me" in cmd_lower:
            self.handle_training_command(command)
        elif "demonstrate" in cmd_lower or "what can you do" in cmd_lower:
            self.handle_automation_request(command)
        else:
            # Default to describing what's on screen
            self.handle_screen_query(command)
            
    def get_agent_by_intent(self, intent):
        """Get the correct agent for the intent"""
        intent_to_agent_name = {
            "hardware": "HAL",
            "files": "Charlie",
            "folder": "Charlie",
            "open_file": "Charlie",
            "code": "Alice",
            "weather": "Bob",
            "time": "Bob",
            "sports": "Bob",
            "search": "Bob",
            "general": "Nina"
        }
        
        agent_name = intent_to_agent_name.get(intent, "Nina")
        return self.nina.get_agent_by_name(agent_name)
        
    def process_with_agent(self, agent, command, intent):
        """Process command with specific agent"""
        print(f"🤖 Using agent: {agent.agent_name} (type: {agent.type})")
        
        try:
            # Special setup for file agent
            if agent.type == "file_agent":
                command = self.enhance_file_command(command)
                print(f"📝 Enhanced file command: {command}")
                    
            with quiet():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                class DummySpeech:
                    def speak(self, text): pass
                
                answer, _ = loop.run_until_complete(
                    agent.process(command, DummySpeech())
                )
                loop.close()
                
            # Handle response
            if answer:
                self.handle_response(answer, intent, command)
            else:
                self.nina.speak("I couldn't complete that task.")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            self.nina.speak("I encountered an error. Please try again.")
            
    def enhance_file_command(self, command):
        """Enhance file commands for better processing"""
        cmd_lower = command.lower()
        enhanced = command
        
        if "called" in cmd_lower or "named" in cmd_lower:
            parts = cmd_lower.split("called" if "called" in cmd_lower else "named")
            if len(parts) > 1:
                filename = parts[1].strip()
                filename = filename.replace("it's a", "").replace("file", "").replace("folder", "").strip()
                if filename:
                    enhanced = f"find {filename}"
                    
        elif "resume" in cmd_lower:
            enhanced = "find resume"
        elif "search for" in cmd_lower:
            parts = cmd_lower.split("search for")
            if len(parts) > 1:
                what = parts[1].strip().split()[0]
                enhanced = f"find {what}"
        
        # Add documents path if mentioned
        if "documents" in cmd_lower and self.nina.documents_path not in enhanced:
            enhanced = f"{enhanced} in {self.nina.documents_path}"
            
        return enhanced
        
    def handle_response(self, answer, intent, original_command):
        """Handle agent responses"""
        if not answer or not answer.strip():
            self.nina.speak("I completed the task but didn't get a response to share.")
            return
            
        # Code responses
        if intent == "code" and (self.nina.last_code or "```" in answer):
            if "```" in answer and not self.nina.last_code:
                code_match = re.search(r'```(?:python)?\n?(.*?)```', answer, re.DOTALL)
                if code_match:
                    self.nina.last_code = code_match.group(1)
                    
            if self.nina.last_code:
                self.nina.speak("I've written the code for you. Let me open it in an editor.")
                self.display_code(self.nina.last_code, original_command)
                
                # Check if Python fixer is available and offer to fix
                if self.python_fixer and self.nina.last_code.strip():
                    self.nina.speak("Would you like me to check the formatting and fix any issues?")
                    
                self.nina.last_code = None
            else:
                self.nina.speak(answer)
            return
            
        # Default - speak the answer
        self.nina.speak(answer)
        
    def display_code(self, code, command):
        """Save and open code in editor"""
        try:
            # Determine filename
            if "calculator" in command.lower():
                filename = "calculator.py"
            elif "hello" in command.lower():
                filename = "hello_world.py"
            else:
                words = command.lower().split()
                words = [w for w in words if w not in ["write", "create", "make", "a", "the", "code", "python"]]
                filename = "_".join(words[:2]) + ".py" if words else "code.py"
                
            filepath = os.path.join(self.nina.work_dir, filename)
            with open(filepath, 'w') as f:
                f.write(code)
                
            print(f"💾 Code saved to: {filepath}")
            
            # Auto-fix if Python fixer is available
            if self.python_fixer and filename.endswith('.py'):
                fixed_code, issues = self.python_fixer.fix_code(code)
                if issues:
                    with open(filepath, 'w') as f:
                        f.write(fixed_code)
                    print(f"🔧 Auto-fixed {len(issues)} issues")
                
            # Try editors in order
            editors = [
                ("code", "VS Code"),
                ("notepad++", "Notepad++"),
                ("notepad", "Notepad")
            ]
            
            opened = False
            for cmd, name in editors:
                try:
                    subprocess.Popen([cmd, filepath])
                    self.nina.speak(f"I've opened the code in {name} for you.")
                    opened = True
                    break
                except:
                    continue
                    
            if not opened:
                self.nina.speak("I've saved the code but couldn't open an editor.")
                    
        except Exception as e:
            print(f"Error saving code: {e}")
            self.nina.speak("I've written the code but couldn't save it.")
    
    # Schedule handler
    def handle_schedule_query(self, command):
        """Handle schedule queries"""
        cmd_lower = command.lower()
        
        # Determine which day
        day = None
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        for d in days:
            if d in cmd_lower:
                day = d
                break
                
        if "today" in cmd_lower or day is None:
            day = date.today().strftime("%A").lower()
        elif "tomorrow" in cmd_lower:
            tomorrow = date.today() + timedelta(days=1)
            day = tomorrow.strftime("%A").lower()
            
        # Get schedule
        schedule = self.nina.personal_config.get_schedule(day)
        
        if schedule:
            response = f"Your schedule for {day.capitalize()}: "
            for entry in schedule:
                response += f"{entry['activity']} at {entry['time']}. "
            self.nina.speak(response)
        else:
            self.nina.speak(f"You have no scheduled meetings for {day.capitalize()}.")
    
    # File and folder handlers
    def handle_folder_operation(self, command):
        """Handle folder opening"""
        cmd_lower = command.lower()
        
        # Check if it's a resume folder request
        if "resume" in cmd_lower and "folder" in cmd_lower:
            search_agent = self.nina.get_agent_by_name("Charlie")
            if search_agent:
                results = search_agent.search_files_and_folders("resume")
                if results['folders']:
                    folder_path = results['folders'][0]
                    self.open_folder(folder_path, "Resume")
                    return
                else:
                    self.nina.speak("I couldn't find a Resume folder in your documents.")
                    return
        
        # Check configured folders
        folders = self.nina.personal_config.get_all_folders()
        
        for nickname, path in folders.items():
            if nickname in cmd_lower:
                if os.path.exists(path):
                    self.open_folder(path, nickname)
                else:
                    self.nina.speak(f"The {nickname} folder path doesn't exist.")
                return
                
        self.nina.speak("I couldn't find that folder. Check your nina_personal.ini file.")
        
    def open_folder(self, folder_path, folder_name):
        """Open a folder in the file explorer"""
        try:
            if platform.system() == "Windows":
                subprocess.Popen(['explorer', folder_path])
            elif platform.system() == "Darwin":
                subprocess.Popen(['open', folder_path])
            else:
                subprocess.Popen(['xdg-open', folder_path])
                
            self.nina.speak(f"I've opened the {folder_name} folder for you.")
            print(f"📂 Opened: {folder_path}")
        except Exception as e:
            print(f"Error opening folder: {e}")
            self.nina.speak(f"I found the folder but couldn't open it.")
    
    def handle_file_open(self, command):
        """Handle file opening requests"""
        cmd_lower = command.lower()
        
        # Fix voice recognition errors
        cmd_lower = cmd_lower.replace(" underscore ", "_")
        cmd_lower = cmd_lower.replace(" dot ", ".")
        
        # Handle resume files
        if "resume" in cmd_lower:
            self.handle_resume_open(cmd_lower)
            return
            
        # Handle other files
        filename = self.extract_filename(cmd_lower)
        if filename:
            self.search_and_open_file(filename)
        else:
            self.nina.speak("I couldn't understand which file you want to open.")
            
    def handle_resume_open(self, cmd_lower):
        """Handle opening resume files"""
        print(f"🔍 Searching for resume files...")
        
        # Check for specific resume type
        specific_resume = None
        resume_keywords = {
            "guardicore": "guardicore",
            "security": "security",
            "manager": "mgr",
            "mgr": "mgr",
            "vp": "vp",
            "vice president": "vp"
        }
        
        for keyword, search_term in resume_keywords.items():
            if keyword in cmd_lower:
                specific_resume = search_term
                break
        
        # Search for resumes
        search_agent = self.nina.get_agent_by_name("Charlie")
        if search_agent:
            results = search_agent.search_files_and_folders("resume")
            
            if results['files']:
                # Filter if specific resume requested
                if specific_resume:
                    matching_files = [f for f in results['files'] if specific_resume.lower() in f.lower()]
                    if matching_files:
                        results['files'] = matching_files
                        print(f"📎 Found {len(matching_files)} files matching '{specific_resume}'")
                
                # Open first matching file
                self.open_file(results['files'][0])
            else:
                self.nina.speak("I couldn't find any resume files.")
                
    def extract_filename(self, cmd_lower):
        """Extract filename from command"""
        extensions = [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".ppt", ".pptx", ".py"]
        
        for ext in extensions:
            if ext in cmd_lower:
                parts = cmd_lower.split(ext)
                if parts[0]:
                    words = parts[0].split()
                    if words:
                        # Get the filename part
                        potential_name = []
                        for word in reversed(words):
                            if word in ["open", "launch", "start", "file", "the", "a", "fix"]:
                                break
                            potential_name.insert(0, word)
                        if potential_name:
                            return "_".join(potential_name) + ext
        return None
        
    def search_and_open_file(self, filename):
        """Search for and open a file"""
        print(f"🔍 Searching for file: {filename}")
        
        search_agent = self.nina.get_agent_by_name("Charlie")
        if search_agent:
            # Remove extension for search
            search_term = filename
            for ext in [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".ppt", ".pptx", ".py"]:
                search_term = search_term.replace(ext, "")
            
            results = search_agent.search_files_and_folders(search_term)
            
            if results['files']:
                # Find best match
                file_path = None
                for path in results['files']:
                    if filename.lower() in path.lower():
                        file_path = path
                        break
                
                if not file_path:
                    file_path = results['files'][0]
                    
                self.open_file(file_path)
            else:
                self.nina.speak(f"I couldn't find {filename}.")
                
    def open_file(self, file_path):
        """Open a file with the default application"""
        try:
            print(f"📄 Opening: {file_path}")
            if platform.system() == "Windows":
                # Try multiple methods
                try:
                    os.startfile(file_path)
                    print(f"✅ Opened with os.startfile")
                except Exception as e1:
                    print(f"❌ os.startfile failed: {e1}")
                    # Try with subprocess
                    subprocess.run(['start', '', file_path], shell=True, check=True)
                    print(f"✅ Opened with start command")
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", file_path])
            else:
                subprocess.Popen(["xdg-open", file_path])
                
            self.nina.speak(f"I've opened {os.path.basename(file_path)} for you.")
        except Exception as e:
            print(f"❌ Error opening file: {e}")
            self.nina.speak(f"I found the file but couldn't open it. It's at {file_path}")
    
    # Quick file handler
    def handle_quick_file(self, command):
        """Handle quick file opening from config"""
        cmd_lower = command.lower()
        quick_files = self.nina.personal_config.get_quick_files()
        
        for name, file_path in quick_files.items():
            if name in cmd_lower:
                if os.path.exists(file_path):
                    self.open_file(file_path)
                else:
                    self.nina.speak(f"I couldn't find your {name} file at the configured location.")
                return
                
    # Application handlers
    def handle_app_launch(self, command):
        """Handle application launching"""
        cmd_lower = command.lower()
        
        # Application mappings
        app_commands = {
            "word": [r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE", "Microsoft Word"],
            "microsoft word": [r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE", "Microsoft Word"],
            "excel": [r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE", "Microsoft Excel"],
            "powerpoint": [r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE", "PowerPoint"],
            "notepad": ["notepad.exe", "Notepad"],
            "notepad++": [r"C:\Program Files\Notepad++\notepad++.exe", "Notepad++"],
            "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe", "Google Chrome"],
            "firefox": [r"C:\Program Files\Mozilla Firefox\firefox.exe", "Firefox"],
            "edge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "Microsoft Edge"],
            "calculator": ["calc.exe", "Calculator"],
            "paint": ["mspaint.exe", "Paint"],
            "outlook": [r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE", "Outlook"],
            "vscode": ["code", "Visual Studio Code"],
            "vs code": ["code", "Visual Studio Code"],
        }
        
        # Find which app to launch
        for app_key, (command_path, display_name) in app_commands.items():
            if app_key in cmd_lower:
                self.launch_application(command_path, display_name)
                return
                
        self.nina.speak("I'm not sure which application you want me to open.")
        
    def launch_application(self, app_path, app_name):
        """Launch an application"""
        try:
            print(f"🚀 Launching {app_name}...")
            
            if platform.system() == "Windows":
                if os.path.exists(app_path):
                    subprocess.Popen([app_path])
                else:
                    # Try alternate paths for Office
                    if "Office16" in app_path:
                        alt_paths = [
                            app_path.replace("Office16", "Office15"),
                            app_path.replace("Office16", "Office14"),
                            app_path.replace(r"C:\Program Files", r"C:\Program Files (x86)")
                        ]
                        
                        launched = False
                        for alt_path in alt_paths:
                            if os.path.exists(alt_path):
                                subprocess.Popen([alt_path])
                                launched = True
                                break
                        
                        if not launched:
                            # Try using start command
                            subprocess.Popen(f'start "" "{app_name}"', shell=True)
                    else:
                        subprocess.Popen(app_path, shell=True)
            else:
                subprocess.Popen([app_path])
                
            self.nina.speak(f"I've opened {app_name} for you.")
            print(f"✅ Launched {app_name}")
        except Exception as e:
            print(f"Error launching {app_name}: {e}")
            self.nina.speak(f"I couldn't open {app_name}. Make sure it's installed.")
    
    # Web handlers
    def handle_website(self, command):
        """Handle website opening from config"""
        cmd_lower = command.lower()
        websites = self.nina.personal_config.get_websites()
        
        for name, url in websites.items():
            if name in cmd_lower and name != "news":
                self.open_url(url, f"Opening {name}")
                return
                
    def handle_weather_query(self, command):
        """Handle weather queries with actual weather data"""
        import requests
        import json
        
        cmd_lower = command.lower()
        location = self.nina.personal_config.get_preference('location', 'San Marcos, Texas')
        
        # Determine what weather info they want
        if "tomorrow" in cmd_lower:
            when = "tomorrow"
        elif "week" in cmd_lower or "forecast" in cmd_lower:
            when = "week"
        elif "rain" in cmd_lower:
            when = "rain"
        else:
            when = "today"
        
        try:
            # Use wttr.in for simple weather data (no API key needed)
            # Format: ?format=j1 for JSON, ?format=4 for one-line
            url = f"https://wttr.in/{location.replace(' ', '+')}?format=j1"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                
                # Current conditions
                temp_f = current['temp_F']
                feels_like = current['FeelsLikeF']
                desc = current['weatherDesc'][0]['value']
                humidity = current['humidity']
                wind = current['windspeedMiles']
                
                # Build response based on query
                if when == "today":
                    response_text = f"It's currently {temp_f} degrees and {desc.lower()} in {location}. "
                    if abs(int(temp_f) - int(feels_like)) > 5:
                        response_text += f"It feels like {feels_like} degrees. "
                    response_text += f"Humidity is {humidity}% with {wind} mph winds."
                    
                elif when == "tomorrow":
                    tomorrow = data['weather'][1]  # Index 1 is tomorrow
                    max_temp = tomorrow['maxtempF']
                    min_temp = tomorrow['mintempF']
                    desc = tomorrow['hourly'][4]['weatherDesc'][0]['value']  # Mid-day description
                    rain_chance = max(int(h['chanceofrain']) for h in tomorrow['hourly'])
                    
                    response_text = f"Tomorrow in {location}: {desc} with temperatures between {min_temp} and {max_temp} degrees. "
                    if rain_chance > 30:
                        response_text += f"There's a {rain_chance}% chance of rain."
                        
                elif when == "rain":
                    today = data['weather'][0]
                    rain_chance = max(int(h['chanceofrain']) for h in today['hourly'])
                    precip = today.get('totalPrecip_mm', '0')
                    
                    if rain_chance > 60:
                        response_text = f"Yes, there's a {rain_chance}% chance of rain today with about {precip}mm expected."
                    elif rain_chance > 30:
                        response_text = f"There's a {rain_chance}% chance of rain today. You might want to bring an umbrella."
                    else:
                        response_text = f"No rain expected today. Only a {rain_chance}% chance."
                        
                elif when == "week":
                    response_text = f"This week in {location}: "
                    for i, day in enumerate(data['weather'][:5]):  # 5 day forecast
                        date = day['date']
                        max_t = day['maxtempF']
                        min_t = day['mintempF']
                        desc = day['hourly'][4]['weatherDesc'][0]['value']
                        response_text += f"{date}: {desc}, {min_t}-{max_t}°F. "
                
                self.nina.speak(response_text)
                
                # Only open browser if they ask for more details
                if "more" in cmd_lower or "details" in cmd_lower or "show" in cmd_lower:
                    self.open_weather_browser()
                    
            else:
                # Fallback to browser if API fails
                self.nina.speak(f"I couldn't get live weather data. Let me open the weather forecast for {location}.")
                self.open_weather_browser()
                
        except Exception as e:
            print(f"Weather API error: {e}")
            # Fallback to browser
            self.nina.speak(f"I'm having trouble getting weather data. Let me open the forecast for {location}.")
            self.open_weather_browser()
            
    def open_weather_browser(self):
        """Open weather in browser as fallback"""
        websites = self.nina.personal_config.get_websites()
        if 'weather' in websites:
            url = websites['weather']
        else:
            location = self.nina.personal_config.get_preference('location', 'San Marcos, Texas')
            location_encoded = location.replace(' ', '+').replace(',', '')
            url = f"https://www.google.com/search?q=weather+{location_encoded}"
        
        self.open_url(url, "Opening weather website")
        
    def handle_time_query(self, command):
        """Handle time queries"""
        current_time = datetime.now()
        time_str = current_time.strftime("%I:%M %p")
        day_str = current_time.strftime("%A, %B %d")
        
        # Remove leading zero
        if time_str.startswith("0"):
            time_str = time_str[1:]
            
        self.nina.speak(f"It's {time_str} on {day_str}.")
        print(f"🕐 Current time: {time_str}, {day_str}")
        
    def handle_news_query(self, command):
        """Handle news queries"""
        # Get configured news source
        preferred = self.nina.personal_config.get_preference('preferred_news_source', 'google')
        
        if self.nina.personal_config.config.has_option('WEBSITES', 'news'):
            url = self.nina.personal_config.config.get('WEBSITES', 'news')
        else:
            url = self.nina.personal_config.get_preference('news_source', 'https://news.google.com')
        
        # Extract domain for speech
        domain = url.split('/')[2].replace('www.', '').replace('.com', '')
        self.open_url(url, f"Opening {domain} news")
        
    def handle_sports_query(self, command):
        """Handle sports queries with voice responses"""
        cmd_lower = command.lower()
        
        # For now, provide informative responses and only open browser if requested
        team = None
        team_info = {
            "dodgers": "Los Angeles Dodgers",
            "lakers": "Los Angeles Lakers", 
            "rams": "Los Angeles Rams",
            "cowboys": "Dallas Cowboys"
        }
        
        for team_key, team_name in team_info.items():
            if team_key in cmd_lower:
                team = team_name
                break
                
        if not team:
            self.nina.speak("Which team are you asking about? I can check on the Dodgers, Lakers, Rams, or Cowboys.")
            return
            
        # Provide voice response based on query type
        if "score" in cmd_lower or "yesterday" in cmd_lower:
            self.nina.speak(f"Let me check the latest {team} results. For live scores and game results, I recommend checking ESPN or the team's official website. Would you like me to open that for you?")
        elif "today" in cmd_lower or "play today" in cmd_lower:
            self.nina.speak(f"Let me check if the {team} play today. For today's schedule, would you like me to open their game schedule?")
        elif "next" in cmd_lower:
            self.nina.speak(f"To see when the {team} play next, would you like me to open their schedule?")
        else:
            self.nina.speak(f"What would you like to know about the {team}? I can check if they play today, their latest results, or their upcoming games.")
            
        # Only open browser if the user's response seems affirmative or they explicitly ask
        if any(word in cmd_lower for word in ["show", "open", "yes", "details", "more"]):
            search_query = f"{team}+schedule+score"
            url = f"https://www.google.com/search?q={search_query}"
            self.open_url(url, f"Opening {team} information")
            
    def open_url(self, url, message):
        """Open URL in default browser"""
        try:
            print(f"🌐 {message}...")
            if platform.system() == "Windows":
                subprocess.Popen(['start', '', url], shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(['open', url])
            else:
                subprocess.Popen(['xdg-open', url])
                
            self.nina.speak(f"{message} in your browser.")
        except Exception as e:
            print(f"Error opening browser: {e}")
            self.nina.speak("I couldn't open the browser.")
    
    # Tech command handler
    def handle_tech_command(self, command):
        """Handle technical/IT commands"""
        # Let the tech module handle it
        handled = self.tech_commands.process_tech_command(command)
        if not handled:
            self.nina.speak("I didn't understand that technical command. Try saying things like 'ping google.com' or 'open command prompt'.")