# nina_ultimate.py
"""
Nina Voice Assistant - Complete Fixed Version
- Fixed intent detection
- Actually performs tasks instead of giving instructions
- Hardware detection works
- File search works with DirectFileSearchAgent
- Schedule support
- Folder operations
"""

import json
import pyaudio
import asyncio
import threading
import time
import re
import os
import sys
import subprocess
import tempfile
from vosk import Model, KaldiRecognizer
import configparser
from datetime import datetime, date, timedelta
import pygame
import edge_tts
from pathlib import Path
import platform
import psutil
import glob  # Added for file search

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Quiet imports
import io
import contextlib

@contextlib.contextmanager
def quiet():
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

with quiet():
    from sources.llm_provider import Provider
    from sources.agents.casual_agent import CasualAgent
    from sources.agents.code_agent import CoderAgent
    from sources.agents.file_agent import FileAgent
    from sources.agents.browser_agent import BrowserAgent
    from sources.agents.planner_agent import PlannerAgent
    from sources.browser import Browser, create_driver
    from sources.router import AgentRouter
    from sources.memory import Memory


class HardwareAgent:
    """Simple hardware information agent"""
    
    def __init__(self, name, prompt_path, provider, verbose=False):
        self.agent_name = name
        self.type = "hardware_agent"
        self.role = "hardware"
        self.llm = provider
        self.memory = None
        
    def get_memory_info(self):
        """Get memory (RAM) information"""
        try:
            ram = psutil.virtual_memory()
            total_gb = ram.total / (1024**3)
            used_gb = ram.used / (1024**3)
            available_gb = ram.available / (1024**3)
            percent = ram.percent
            
            return f"You have {total_gb:.1f} GB of RAM total. Currently using {used_gb:.1f} GB ({percent:.1f}%), with {available_gb:.1f} GB available."
        except Exception as e:
            return f"Error getting memory info: {str(e)}"
            
    def get_disk_space(self):
        """Get disk space information"""
        try:
            disks_info = []
            for partition in psutil.disk_partitions():
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                    
                usage = psutil.disk_usage(partition.mountpoint)
                total_gb = usage.total / (1024**3)
                used_gb = usage.used / (1024**3)
                free_gb = usage.free / (1024**3)
                percent = usage.percent
                
                disk_info = f"{partition.device} has {total_gb:.1f} GB total, using {used_gb:.1f} GB ({percent:.1f}%), with {free_gb:.1f} GB free"
                disks_info.append(disk_info)
                
            return "Your disk space: " + ". ".join(disks_info)
        except Exception as e:
            return f"Error getting disk space: {str(e)}"
            
    def get_gpu_info(self):
        """Get GPU information"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                      capture_output=True, text=True, shell=True)
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines[1:]:
                    if line.strip() and line.strip() != "Name":
                        gpus.append(line.strip())
                return "Your graphics card: " + ', '.join(gpus) if gpus else "No GPU information found"
        except:
            return "Could not get GPU information"
            
    async def process(self, query, speech_module):
        """Process hardware queries"""
        query_lower = query.lower()
        
        if "memory" in query_lower or "ram" in query_lower:
            return self.get_memory_info(), ""
        elif "disk" in query_lower or "space" in query_lower or "storage" in query_lower:
            return self.get_disk_space(), ""
        elif "gpu" in query_lower or "graphics" in query_lower:
            return self.get_gpu_info(), ""
        else:
            # Return all info
            info = []
            info.append(self.get_memory_info())
            info.append(self.get_disk_space())
            info.append(self.get_gpu_info())
            return " ".join(info), ""


class DirectFileSearchAgent:
    """Direct file search agent that actually works"""
    
    def __init__(self, name, prompt_path, provider, verbose=False):
        self.agent_name = name
        self.type = "file_agent"  # Pretend to be file agent
        self.role = "files"
        self.llm = provider
        self.memory = None
        self.tools = {}  # Empty tools dict for compatibility
        
    def search_files_and_folders(self, search_term, search_path=None):
        """Search for files and folders containing the search term"""
        if not search_path:
            # Default search locations
            home = Path.home()
            search_paths = [
                str(home / "OneDrive" / "Documents"),
                str(home / "Documents"),
                str(home / "Desktop"),
                str(home / "Downloads"),
            ]
        else:
            search_paths = [search_path]
            
        results = {
            'files': [],
            'folders': []
        }
        
        for base_path in search_paths:
            if not os.path.exists(base_path):
                continue
                
            try:
                # Search for files and folders
                for root, dirs, files in os.walk(base_path):
                    # Don't go too deep (max 3 levels)
                    depth = root[len(base_path):].count(os.sep)
                    if depth > 3:
                        continue
                        
                    # Check folders
                    for dir_name in dirs:
                        if search_term.lower() in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            results['folders'].append(full_path)
                            
                    # Check files
                    for file_name in files:
                        if search_term.lower() in file_name.lower():
                            full_path = os.path.join(root, file_name)
                            results['files'].append(full_path)
                            
                    # Limit total results
                    if len(results['files']) + len(results['folders']) > 50:
                        return results
                        
            except PermissionError:
                continue
            except Exception as e:
                print(f"Error searching {base_path}: {e}")
                continue
                
        return results
        
    async def process(self, query, speech_module):
        """Process file/folder search queries"""
        query_lower = query.lower()
        search_term = None
        
        # Extract search term from various patterns
        patterns = [
            ("called", 1),  # "file called X"
            ("named", 1),   # "file named X"
            ("find", 1),    # "find X"
            ("search for", 2),  # "search for X"
            ("look for", 2),    # "look for X"
        ]
        
        for pattern, word_count in patterns:
            if pattern in query_lower:
                parts = query_lower.split(pattern, 1)
                if len(parts) > 1:
                    remaining = parts[1].strip()
                    # For multi-word patterns, extract more words
                    words = remaining.split()
                    if words:
                        # Take the specified number of words
                        search_words = []
                        skip_words = ["a", "an", "the", "me", "my", "file", "folder", "document", "pdf"]
                        word_count_found = 0
                        for word in words:
                            if word not in skip_words:
                                search_words.append(word)
                                word_count_found += 1
                                if word_count_found >= word_count:
                                    break
                        if search_words:
                            search_term = " ".join(search_words)
                            break
                            
        # Special case for "resume"
        if not search_term and "resume" in query_lower:
            search_term = "resume"
            
        if not search_term:
            return "I need to know what to search for. Please specify a file or folder name.", ""
            
        print(f"🔍 Searching for: '{search_term}'")
        
        # Perform search
        results = self.search_files_and_folders(search_term)
        
        # Format response
        total_found = len(results['files']) + len(results['folders'])
        
        if total_found == 0:
            searched_locations = "Documents, Desktop, and Downloads"
            return f"I couldn't find any files or folders containing '{search_term}' in your {searched_locations} folders.", ""
            
        # Build response
        response_parts = []
        response_parts.append(f"I found {total_found} items containing '{search_term}':")
        
        # Show folders (limit to 3)
        if results['folders']:
            folder_count = len(results['folders'])  # Define variable first
            response_parts.append(f"\n📁 FOLDERS ({folder_count}):")
            for i, folder_path in enumerate(results['folders'][:3]):
                folder_name = os.path.basename(folder_path)
                parent_dir = os.path.basename(os.path.dirname(folder_path))
                response_parts.append(f"  • {folder_name} (in {parent_dir})")
            if folder_count > 3:
                more_folders = folder_count - 3  # Calculate first
                response_parts.append(f"  ... and {more_folders} more folders")
        
        # Show files (limit to 5)
        if results['files']:
            file_count = len(results['files'])  # Define variable first
            response_parts.append(f"\n📄 FILES ({file_count}):")
            for i, file_path in enumerate(results['files'][:5]):
                file_name = os.path.basename(file_path)
                parent_dir = os.path.basename(os.path.dirname(file_path))
                response_parts.append(f"  • {file_name} (in {parent_dir})")
            if file_count > 5:
                more_files = file_count - 5  # Calculate first
                response_parts.append(f"  ... and {more_files} more files")
                
        return "\n".join(response_parts), ""


class PersonalConfig:
    """Load and manage personal configuration"""
    
    def __init__(self, config_path="nina_personal.ini"):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        
        if not os.path.exists(config_path):
            self.create_default_config()
        
        self.config.read(config_path)
        
    def create_default_config(self):
        """Create default config"""
        username = os.environ.get('USERNAME', 'User')
        default_config = f"""# nina_personal.ini
# Personal configuration for Nina - customize this with your folders and preferences

[FOLDERS]
# Add your frequently accessed folders here
# Format: nickname = full_path
documents = C:\\Users\\{username}\\OneDrive\\Documents
downloads = C:\\Users\\{username}\\Downloads
desktop = C:\\Users\\{username}\\Desktop
employment = C:\\Users\\{username}\\OneDrive\\Documents\\Employment
employer = C:\\Users\\{username}\\OneDrive\\Documents\\Employment

[QUICK_FILES]
# Add frequently accessed files
resume = C:\\Users\\{username}\\OneDrive\\Documents\\Resume.pdf

[APPLICATIONS]
# Add your preferred applications
calculator = calc.exe
notepad = notepad.exe
browser = C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
vscode = C:\\Program Files\\Microsoft VS Code\\Code.exe
outlook = outlook.exe

[WEBSITES]
# Add your frequently visited websites
email = https://outlook.com
calendar = https://calendar.google.com
weather = https://weather.com
news = https://news.google.com

[SCHEDULE]
# Simple schedule entries
# Format: day = activity1 | time1, activity2 | time2
monday = No meetings scheduled
tuesday = No meetings scheduled
wednesday = No meetings scheduled
thursday = Code review | 11:00 AM, Planning meeting | 2:00 PM
friday = Team sync | 9:00 AM, Weekly report | 4:00 PM

[PREFERENCES]
# Personal preferences
default_browser = chrome
default_editor = vscode
preferred_news_source = google
location = San Marcos, Texas
news_source = https://www.foxnews.com
news_politics = https://www.foxnews.com/politics
news_business = https://www.foxnews.com/business
news_tech = https://www.foxnews.com/tech
news_breaking = https://www.foxnews.com/breaking-news

[SPORTS_TEAMS]
# Your favorite sports teams
team1 = Dodgers
team2 = Lakers
team3 = Rams
team4 = Cowboys

[SOCIAL_MEDIA]
# Social media platforms
platform1 = twitter|https://twitter.com
platform2 = linkedin|https://linkedin.com
platform3 = facebook|https://facebook.com
"""
        
        with open(self.config_path, 'w') as f:
            f.write(default_config)
            
    def get_folder(self, nickname):
        """Get folder path by nickname"""
        if self.config.has_option('FOLDERS', nickname):
            return self.config.get('FOLDERS', nickname)
        return None
        
    def get_all_folders(self):
        """Get all configured folders"""
        if self.config.has_section('FOLDERS'):
            return dict(self.config.items('FOLDERS'))
        return {}
        
    def get_schedule(self, day=None):
        """Get schedule for a specific day"""
        if not self.config.has_section('SCHEDULE'):
            return None
            
        if day is None:
            day = date.today().strftime("%A").lower()
        else:
            day = day.lower()
            
        if self.config.has_option('SCHEDULE', day):
            schedule_str = self.config.get('SCHEDULE', day)
            if schedule_str.lower() == "no meetings scheduled":
                return None
            
            entries = []
            for entry in schedule_str.split(','):
                if '|' in entry:
                    parts = entry.strip().split('|')
                    if len(parts) == 2:
                        entries.append({
                            'activity': parts[0].strip(),
                            'time': parts[1].strip()
                        })
            return entries if entries else None
        return None
        
    def get_quick_files(self):
        """Get configured quick access files"""
        files = {}
        if self.config.has_section('QUICK_FILES'):
            for key, value in self.config.items('QUICK_FILES'):
                files[key] = value
        return files
        
    def get_websites(self):
        """Get configured websites"""
        sites = {}
        if self.config.has_section('WEBSITES'):
            for key, value in self.config.items('WEBSITES'):
                sites[key] = value
        return sites
        
    def get_applications(self):
        """Get configured applications"""
        apps = {}
        if self.config.has_section('APPLICATIONS'):
            for key, value in self.config.items('APPLICATIONS'):
                apps[key] = value
        return apps
        
    def get_preference(self, key, default=None):
        """Get a preference value"""
        if self.config.has_option('PREFERENCES', key):
            return self.config.get('PREFERENCES', key)
        return default
        
    def get_sports_teams(self):
        """Get configured sports teams"""
        teams = []
        if self.config.has_section('SPORTS_TEAMS'):
            for key, value in self.config.items('SPORTS_TEAMS'):
                teams.append(value.lower())
        return teams if teams else ["dodgers", "lakers", "rams", "cowboys"]
        
    def get_social_media(self):
        """Get configured social media platforms"""
        platforms = {}
        if self.config.has_section('SOCIAL_MEDIA'):
            for key, value in self.config.items('SOCIAL_MEDIA'):
                if '|' in value:
                    name, url = value.split('|', 1)
                    platforms[name.lower()] = url
        return platforms if platforms else {
            "twitter": "https://twitter.com",
            "linkedin": "https://linkedin.com"
        }


class NinaFixed:
    """Fixed Nina with better intent detection"""
    
    def __init__(self, agents, config):
        self.agents = agents
        self.config = config
        
        # Load personal configuration
        self.personal_config = PersonalConfig()
        print("✅ Personal configuration loaded")
        
        # Initialize router (but we'll override its decisions)
        with quiet():
            self.router = AgentRouter(agents, supported_language=['en'])
        
        # Set paths
        self.work_dir = config.get('MAIN', 'work_dir')
        self.documents_path = str(Path.home() / "OneDrive" / "Documents")
        
        # Create directories
        os.makedirs(self.work_dir, exist_ok=True)
        
        # Fix agents
        self.fix_agent_types()
        
        print("🎙️ Setting up speech recognition...")
        self.init_speech_recognition()
        
        print("🔊 Setting up natural voice...")
        self.voice = "en-US-AriaNeural"
        
        # State
        self.is_running = True
        self.command_buffer = []
        self.last_command_time = 0
        self.last_code = None
        
        # Initialize pygame
        pygame.mixer.init()
        
    def fix_agent_types(self):
        """Ensure agents have correct types"""
        for agent in self.agents:
            if hasattr(agent, 'agent_name'):
                if agent.agent_name == "Alice":
                    agent.type = "coder_agent"
                    agent.role = "code"
                elif agent.agent_name == "HAL":
                    agent.type = "hardware_agent"
                    agent.role = "hardware"
                elif agent.agent_name == "Charlie":
                    agent.type = "file_agent"
                    agent.role = "files"
                elif agent.agent_name == "Bob":
                    agent.type = "browser_agent"
                    agent.role = "web"
                    
    def init_speech_recognition(self):
        """Initialize Vosk"""
        model_path = "vosk-model-en-us-0.22"
        
        if not os.path.exists(model_path):
            print(f"❌ Please download Vosk model to: {model_path}/")
            sys.exit(1)
            
        with quiet():
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            
    def speak(self, text):
        """Speak with Edge TTS"""
        if not text:
            return
            
        text = self.clean_for_speech(text)
        print(f"💬 Nina: {text}")
        
        # Edge TTS
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def generate_and_play():
            try:
                communicate = edge_tts.Communicate(text, self.voice)
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_path = temp_file.name
                temp_file.close()
                
                await communicate.save(temp_path)
                
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                    
                # Cleanup
                await asyncio.sleep(0.1)
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"TTS error: {e}")
                
        loop.run_until_complete(generate_and_play())
        loop.close()
        
    def clean_for_speech(self, text):
        """Clean text for speech"""
        if not text:
            return ""
            
        # Remove code blocks
        if "```" in text:
            code_match = re.search(r'```(?:python)?\n?(.*?)```', text, re.DOTALL)
            if code_match:
                self.last_code = code_match.group(1)
            text = re.sub(r'```[\s\S]*?```', 'I\'ve written the code for you.', text).strip()
            
        # Clean paths
        text = re.sub(r'[A-Z]:\\[^\s]+', 'in the folder', text)
        text = re.sub(r'https?://\S+', '', text)
        
        # Replacements
        replacements = {
            "TX": "Texas",
            ".py": " dot py",
            "GB": "gigabytes",
            "...": ".",
            "  ": " "
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        # Limit length
        if len(text) > 250:
            sentences = text.split('. ')
            text = '. '.join(sentences[:2]) + '.' if sentences else text[:250]
                
        return text.strip()
        
    def start(self):
        """Start Nina"""
        folders = self.personal_config.get_all_folders()
        folder_list = "\n".join([f"║  • \"{name}\" → {path[:40]}..." 
                                for name, path in list(folders.items())[:3]])
        
        print(f"""
╔════════════════════════════════════════════════════════╗
║          Nina - Your Personal Assistant                ║
╟────────────────────────────────────────────────────────╢
║  🎤 Voice Recognition: Active                          ║
║  🔊 Natural Voice: Edge TTS                           ║
║  📁 Personal Config: nina_personal.ini                ║
║                                                        ║
║  📂 Quick Folders:                                     ║
{folder_list}
║                                                        ║
║  Commands:                                             ║
║  • "Open the employment folder"                       ║
║  • "Find resume in documents"                        ║
║  • "How much memory do I have?"                      ║
║  • "How much disk space do I have?"                  ║
║  • "What's my schedule today?"                        ║
║  • "Write a Python calculator"                        ║
║  • "What's the weather?"                              ║
║  • "Who won the Dodgers game?"                       ║
║                                                        ║
║  Say "goodbye" to exit                                ║
╚════════════════════════════════════════════════════════╝
        """)
        
        self.speak("Hello! I'm Nina. I can help you find files, check your hardware, open folders, and more. What can I do for you?")
        
        # Audio setup
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=4096
        )
        
        print("\n🎤 Listening...\n")
        
        try:
            while self.is_running:
                data = stream.read(4096, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()
                    
                    if text and len(text) > 2:
                        print(f"\r👤 You: {text}")
                        self.command_buffer.append(text)
                        self.last_command_time = time.time()
                        
                if (self.command_buffer and 
                    time.time() - self.last_command_time > 1.5):
                    
                    command = " ".join(self.command_buffer)
                    self.command_buffer = []
                    self.process_command(command)
                    print("\n🎤 Listening...\n")
                    
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            self.is_running = False
            self.speak("Goodbye! Have a great day!")
            time.sleep(2)
            pygame.mixer.quit()
            
    def is_schedule_query(self, command):
        """Check if command is about schedule"""
        schedule_keywords = ["schedule", "meeting", "appointment", "calendar", "agenda"]
        return any(keyword in command.lower() for keyword in schedule_keywords)
        
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
        schedule = self.personal_config.get_schedule(day)
        
        if schedule:
            response = f"Your schedule for {day.capitalize()}: "
            for entry in schedule:
                response += f"{entry['activity']} at {entry['time']}. "
            self.speak(response)
        else:
            self.speak(f"You have no scheduled meetings for {day.capitalize()}.")
            
    def convert_spoken_symbols(self, text):
        """Convert spoken symbols to actual symbols"""
        conversions = {
            " underscore ": "_",
            " dot ": ".",
            " dash ": "-",
            " slash ": "/",
            " backslash ": "\\",
            " at ": "@",
            " hashtag ": "#",
            " dollar sign ": "$",
            " percent ": "%",
            " ampersand ": "&",
            " asterisk ": "*",
            " plus ": "+",
            " equals ": "=",
        }
        
        for spoken, symbol in conversions.items():
            text = text.replace(spoken, symbol)
            
        return text
            
    def fix_voice_recognition_errors(self, text):
        """Fix common voice recognition errors"""
        fixes = {
            # Company names - all variations
            "guarded core": "guardicore",
            "guard corps": "guardicore", 
            "guardian core": "guardicore",
            "garden core": "guardicore",
            "guard a core": "guardicore",
            "guard a corps": "guardicore",
            
            # Common misheard words
            "my ass this": "maestas",
            "my estus": "maestas",
            "my estas": "maestas",
            
            # File types
            "dot pdf": ".pdf",
            "dot doc": ".doc",
            "dot docx": ".docx"
        }
        
        text_lower = text.lower()
        for wrong, right in fixes.items():
            if wrong in text_lower:
                # Case-insensitive replacement
                text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
                
        return text
            
    def process_command(self, command):
        """Process command with FIXED intent detection"""
        # Speech-to-text conversions
        command = self.convert_spoken_symbols(command)
        command = self.fix_voice_recognition_errors(command)
        
        # Exit check
        if any(word in command.lower() for word in ["stop", "exit", "goodbye", "quit", "bye"]):
            self.is_running = False
            return
            
        # Check for schedule queries FIRST
        if self.is_schedule_query(command):
            self.handle_schedule_query(command)
            return
            
        # THEN determine intent
        intent = self.determine_intent_fixed(command)
        
        print(f"🎯 Intent: {intent} | Command: {command}")
        
        # Feedback
        feedback = {
            "hardware": "Let me check that for you...",
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
            "general": "Let me help with that..."
        }
        
        self.speak(feedback.get(intent, "Processing..."))
        
        # Handle folder operations directly
        if intent == "folder":
            self.handle_folder_operation(command)
            return
            
        # Handle file opening directly
        if intent == "open_file":
            self.handle_file_open(command)
            return
            
        # Handle application launching directly
        if intent == "open_app":
            self.handle_app_launch(command)
            return
            
        # Handle quick file opening
        if intent == "open_quick_file":
            self.handle_quick_file(command)
            return
            
        # Handle website opening
        if intent == "open_website":
            self.handle_website(command)
            return
            
        # Handle weather queries directly
        if intent == "weather":
            self.handle_weather_query(command)
            return
            
        # Handle time queries directly
        if intent == "time":
            self.handle_time_query(command)
            return
            
        # Handle sports queries directly (when browser agent not available)
        if intent == "sports":
            # Try browser agent first
            agent = self.get_agent_by_intent_fixed(intent)
            if agent and hasattr(agent, 'browser') and agent.browser is not None:
                # Browser agent is available, use it
                pass  # Continue to normal agent processing
            else:
                # Browser not available, use direct method
                self.handle_sports_query(command)
                return
                
        # Handle news queries directly
        if intent == "news":
            self.handle_news_query(command)
            return
            
        # Get the RIGHT agent
        agent = self.get_agent_by_intent_fixed(intent)
        
        if not agent:
            self.speak("I'm having trouble with that request.")
            return
            
        print(f"🤖 Using agent: {agent.agent_name} (type: {agent.type})")
        
        # Process with agent
        try:
            # Special handling for browser agent when browser might not be available
            if agent.type == "browser_agent" and intent == "sports":
                # Check if browser is actually working
                if not hasattr(agent, 'browser') or agent.browser is None:
                    self.speak("I can't access sports scores right now because the web browser isn't available. You could check ESPN.com or your favorite sports site for the latest Dodgers results.")
                    return
                    
            # Special setup for file agent
            if agent.type == "file_agent":
                # Enhance the command for file agent
                cmd_lower = command.lower()
                
                # Extract the actual filename from common patterns
                enhanced = command
                if "called" in cmd_lower or "named" in cmd_lower:
                    # Pattern: "file called X" or "file named X"
                    parts = cmd_lower.split("called" if "called" in cmd_lower else "named")
                    if len(parts) > 1:
                        filename = parts[1].strip()
                        # Remove common words
                        filename = filename.replace("it's a", "").replace("file", "").replace("folder", "").strip()
                        if filename:
                            enhanced = f"find {filename}"
                            
                elif "resume" in cmd_lower:
                    enhanced = "find resume"
                elif "search for" in cmd_lower:
                    # Pattern: "search for X"
                    parts = cmd_lower.split("search for")
                    if len(parts) > 1:
                        what = parts[1].strip().split()[0]  # Get first word after "search for"
                        enhanced = f"find {what}"
                
                # Add documents path if mentioned
                if "documents" in cmd_lower and self.documents_path not in enhanced:
                    enhanced = f"{enhanced} in {self.documents_path}"
                    
                command = enhanced
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
                self.speak("I couldn't complete that task.")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            self.speak("I encountered an error. Please try again.")
            
    def determine_intent_fixed(self, command):
        """PROPERLY determine intent from command"""
        cmd = command.lower()
        
        # Quick file operations - CHECK EARLY
        if any(word in cmd for word in ["open", "show", "launch"]):
            quick_files = self.personal_config.get_quick_files()
            for name, path in quick_files.items():
                if name in cmd:
                    return "open_quick_file"
                    
        # Website operations
        if any(word in cmd for word in ["open", "go to", "visit", "show"]):
            websites = self.personal_config.get_websites()
            for name, url in websites.items():
                if name in cmd and name != "news":  # news handled separately
                    return "open_website"
        
        # Schedule queries - CHECK FIRST
        if self.is_schedule_query(command):
            return "schedule"
        
        # Hardware/System queries
        if any(word in cmd for word in ["memory", "ram", "disk", "space", "storage", "gpu", 
                                        "graphics", "hardware", "system", "specs", "how much"]):
            # Make sure it's about computer hardware
            if any(word in cmd for word in ["memory", "ram", "disk", "space", "storage"]):
                return "hardware"
                
        # News queries - CHECK EARLY
        if any(word in cmd for word in ["news", "headline", "headlines", "latest news", "breaking news", "current events"]):
            return "news"
            
        # Sports - Check early for team names (configurable)
        sports_teams = self.personal_config.get_sports_teams()
        if any(team in cmd for team in sports_teams) or \
           (any(word in cmd for word in ["game", "score", "won", "lost", "beat", "play", "played"]) and \
            any(word in cmd for word in ["yesterday", "today", "last night", "team", "they"])):
            return "sports"
            
        # Application launching
        if any(word in cmd for word in ["open", "launch", "start", "run"]) and \
           any(app in cmd for app in ["word", "excel", "powerpoint", "notepad", "chrome", "firefox", "edge", "calculator", "paint", "outlook"]):
            return "open_app"
            
        # Folder operations - CHECK BEFORE FILE OPERATIONS
        if "folder" in cmd and any(word in cmd for word in ["open", "show", "go to", "access"]):
            return "folder"
            
        # File OPENING operations - CHECK EARLY (more forgiving patterns)
        if (any(word in cmd for word in ["open", "opened", "launch", "start", "run"]) and \
            any(word in cmd for word in ["resume", "pdf", "doc", "file", "document"]) and \
            "folder" not in cmd) or \
           any(ext in cmd for ext in [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".ppt"]) or \
           ("guardicore" in cmd and any(word in cmd for word in ["open", "opened"]) and "folder" not in cmd):
            return "open_file"
            
        # File SEARCH operations
        if any(word in cmd for word in ["find", "search", "look for", "locate", "where is"]) and \
           any(word in cmd for word in ["file", "document", "resume", "pdf", "doc", ".txt", ".docx"]):
            return "files"
            
        # Code writing
        if any(word in cmd for word in ["write", "create", "make", "build"]) and \
           any(word in cmd for word in ["code", "script", "program", "calculator", "function", "app"]):
            return "code"
            
        # Weather
        if "weather" in cmd or "temperature" in cmd or "forecast" in cmd:
            return "weather"
            
        # Time
        if "time" in cmd and any(word in cmd for word in ["what", "current", "tell"]):
            return "time"
            
        # Web search
        if any(phrase in cmd for phrase in ["who is", "what is", "search for", "look up", "tell me about"]):
            return "search"
            
        # Default
        return "general"
            
    def get_agent_by_intent_fixed(self, intent):
        """Get the CORRECT agent for the intent"""
        # Direct mapping
        intent_to_agent_name = {
            "hardware": "HAL",
            "files": "Charlie",
            "folder": "Charlie",
            "open_file": "Charlie",  # File agent handles file operations
            "code": "Alice",
            "weather": "Bob",
            "time": "Bob",
            "sports": "Bob",
            "search": "Bob",
            "general": "Nina"
        }
        
        agent_name = intent_to_agent_name.get(intent, "Nina")
        
        # Find agent by name
        for agent in self.agents:
            if hasattr(agent, 'agent_name') and agent.agent_name == agent_name:
                return agent
                
        # Fallback
        print(f"⚠️ Could not find agent {agent_name}, using default")
        return self.agents[0]
            
    def handle_folder_operation(self, command):
        """Handle folder opening"""
        cmd_lower = command.lower()
        
        # Check if it's a resume folder request
        if "resume" in cmd_lower and "folder" in cmd_lower:
            # Search for Resume folder
            search_agent = None
            for agent in self.agents:
                if hasattr(agent, 'agent_name') and agent.agent_name == "Charlie":
                    search_agent = agent
                    break
                    
            if search_agent:
                results = search_agent.search_files_and_folders("resume")
                if results['folders']:
                    # Open the first Resume folder found
                    folder_path = results['folders'][0]
                    try:
                        if platform.system() == "Windows":
                            subprocess.Popen(['explorer', folder_path])
                        elif platform.system() == "Darwin":  # macOS
                            subprocess.Popen(['open', folder_path])
                        else:  # Linux
                            subprocess.Popen(['xdg-open', folder_path])
                            
                        self.speak(f"I've opened the Resume folder for you.")
                        print(f"📂 Opened: {folder_path}")
                        return
                    except Exception as e:
                        print(f"Error opening folder: {e}")
                        self.speak(f"I found the Resume folder but couldn't open it.")
                        return
                else:
                    self.speak("I couldn't find a Resume folder in your documents.")
                    return
        
        # Check configured folders
        folders = self.personal_config.get_all_folders()
        
        folder_path = None
        folder_name = None
        
        for nickname, path in folders.items():
            if nickname in cmd_lower:
                folder_path = path
                folder_name = nickname
                break
                
        if folder_path and os.path.exists(folder_path):
            try:
                if platform.system() == "Windows":
                    subprocess.Popen(['explorer', folder_path])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(['open', folder_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', folder_path])
                    
                self.speak(f"I've opened the {folder_name} folder for you.")
                print(f"📂 Opened: {folder_path}")
            except Exception as e:
                print(f"Error opening folder: {e}")
                self.speak(f"I found the folder but couldn't open it.")
        else:
            self.speak("I couldn't find that folder. Check your nina_personal.ini file.")
            
    def handle_file_open(self, command):
        """Handle file opening requests"""
        cmd_lower = command.lower()
        
        # Replace spoken "underscore" with actual underscore
        cmd_lower = cmd_lower.replace(" underscore ", "_")
        cmd_lower = cmd_lower.replace(" dot ", ".")
        
        # Fix common voice recognition errors
        cmd_lower = cmd_lower.replace("my ass this", "maestas")
        cmd_lower = cmd_lower.replace("my estus", "maestas")
        cmd_lower = cmd_lower.replace("my estas", "maestas")
        
        # Simple approach - if they mention "resume", just search for resume files
        if "resume" in cmd_lower:
            print(f"🔍 Searching for resume files...")
            
            # Check if they specified a particular resume
            specific_resume = None
            if "guardicore" in cmd_lower:
                specific_resume = "guardicore"
            elif "security" in cmd_lower:
                specific_resume = "security"
            elif "manager" in cmd_lower or "mgr" in cmd_lower:
                specific_resume = "mgr"
            elif "vp" in cmd_lower or "vice president" in cmd_lower:
                specific_resume = "vp"
            
            # Get the file search agent
            search_agent = None
            for agent in self.agents:
                if hasattr(agent, 'agent_name') and agent.agent_name == "Charlie":
                    search_agent = agent
                    break
                    
            if search_agent:
                results = search_agent.search_files_and_folders("resume")
                
                if results['files']:
                    # If specific resume requested, filter for it
                    if specific_resume:
                        matching_files = []
                        for f in results['files']:
                            if specific_resume.lower() in f.lower():
                                matching_files.append(f)
                        
                        if matching_files:
                            results['files'] = matching_files
                            print(f"📎 Found {len(matching_files)} files matching '{specific_resume}'")
                    
                    # Take the first matching file
                    file_path = results['files'][0]
                    
                    try:
                        print(f"📄 Opening: {file_path}")
                        if platform.system() == "Windows":
                            # Try different methods to open the file
                            try:
                                # Method 1: Direct os.startfile
                                os.startfile(file_path)
                                print(f"✅ Opened with os.startfile")
                            except Exception as e1:
                                print(f"❌ os.startfile failed: {e1}")
                                try:
                                    # Method 2: Use subprocess with start command
                                    subprocess.run(['start', '', file_path], shell=True, check=True)
                                    print(f"✅ Opened with start command")
                                except Exception as e2:
                                    print(f"❌ start command failed: {e2}")
                                    # Method 3: Open with specific browser for PDFs
                                    if file_path.lower().endswith('.pdf'):
                                        try:
                                            # Try Edge
                                            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                                            if os.path.exists(edge_path):
                                                subprocess.Popen([edge_path, file_path])
                                                print(f"✅ Opened PDF with Edge")
                                            else:
                                                # Try Chrome
                                                chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                                                if os.path.exists(chrome_path):
                                                    subprocess.Popen([chrome_path, file_path])
                                                    print(f"✅ Opened PDF with Chrome")
                                                else:
                                                    raise Exception("No browser found for PDF")
                                        except Exception as e3:
                                            print(f"❌ Browser open failed: {e3}")
                                            raise e3
                                    else:
                                        raise e2
                        elif platform.system() == "Darwin":  # macOS
                            subprocess.Popen(["open", file_path])
                        else:  # Linux
                            subprocess.Popen(["xdg-open", file_path])
                            
                        self.speak(f"I've opened {os.path.basename(file_path)} for you.")
                        return
                    except Exception as e:
                        print(f"❌ Error opening file: {e}")
                        print(f"📁 File path: {file_path}")
                        print(f"📁 File exists: {os.path.exists(file_path)}")
                        self.speak(f"I found the file but couldn't open it. The file is located at {file_path}")
                        return
                else:
                    self.speak("I couldn't find any resume files in your Documents, Desktop, or Downloads folders.")
                    return
            else:
                self.speak("I'm having trouble with the file search system.")
                return
        
        # For other files, try to extract filename
        filename = None
        
        # Look for file extensions
        extensions = [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".ppt", ".pptx"]
        for ext in extensions:
            if ext in cmd_lower:
                # Extract filename around the extension
                parts = cmd_lower.split(ext)
                if parts[0]:
                    # Get the last word before extension
                    words = parts[0].split()
                    if words:
                        # Handle cases like "maestas_resume.pdf" or "maestas resume.pdf"
                        if "_" in words[-1] or "-" in words[-1]:
                            filename = words[-1] + ext
                        else:
                            # Take last few words that might be the filename
                            potential_name = []
                            for word in reversed(words):
                                if word in ["open", "launch", "start", "file", "the", "a", "called", "named"]:
                                    break
                                potential_name.insert(0, word)
                            if potential_name:
                                filename = "_".join(potential_name) + ext
                break
        
        if not filename:
            # Try to extract from patterns like "open file called X"
            patterns = ["called", "named", "file"]
            for pattern in patterns:
                if pattern in cmd_lower:
                    parts = cmd_lower.split(pattern)
                    if len(parts) > 1:
                        remaining = parts[1].strip()
                        words = remaining.split()
                        if words:
                            filename = words[0]
                            break
        
        if filename:
            print(f"🔍 Searching for file to open: {filename}")
            
            # First, search for the file using DirectFileSearchAgent
            search_agent = None
            for agent in self.agents:
                if hasattr(agent, 'agent_name') and agent.agent_name == "Charlie":
                    search_agent = agent
                    break
                    
            if search_agent:
                # Remove extension for search
                search_term = filename.replace("_", " ")
                for ext in extensions:
                    search_term = search_term.replace(ext, "")
                
                results = search_agent.search_files_and_folders(search_term)
                
                if results['files']:
                    # Find exact match or closest match
                    file_path = None
                    
                    # Look for exact match first
                    for path in results['files']:
                        if filename.lower() in path.lower():
                            file_path = path
                            break
                    
                    # If no exact match, take first result
                    if not file_path and results['files']:
                        file_path = results['files'][0]
                    
                    if file_path:
                        try:
                            if platform.system() == "Windows":
                                os.startfile(file_path)
                            elif platform.system() == "Darwin":  # macOS
                                subprocess.Popen(["open", file_path])
                            else:  # Linux
                                subprocess.Popen(["xdg-open", file_path])
                                
                            self.speak(f"I've opened {os.path.basename(file_path)} for you.")
                            print(f"📄 Opened: {file_path}")
                        except Exception as e:
                            print(f"Error opening file: {e}")
                            self.speak("I found the file but couldn't open it.")
                    else:
                        self.speak(f"I couldn't find {filename} in your common folders.")
                else:
                    self.speak(f"I couldn't find {filename}. Make sure it's in your Documents, Desktop, or Downloads folder.")
            else:
                self.speak("I'm having trouble with the file search system.")
        else:
            self.speak("I couldn't understand which file you want to open. Please specify the filename with its extension.")
            
    def handle_response(self, answer, intent, original_command):
        """Handle response appropriately"""
        # Check if answer is empty or just whitespace
        if not answer or not answer.strip():
            self.speak("I completed the task but didn't get a response to share.")
            return
            
        # Code responses
        if intent == "code" and (self.last_code or "```" in answer):
            if "```" in answer and not self.last_code:
                code_match = re.search(r'```(?:python)?\n?(.*?)```', answer, re.DOTALL)
                if code_match:
                    self.last_code = code_match.group(1)
                    
            if self.last_code:
                self.speak("I've written the code for you. Let me open it in an editor.")
                self.display_code(self.last_code, original_command)
                self.last_code = None
            else:
                self.speak(self.clean_for_speech(answer))
            return
            
        # Weather responses - extract temperature
        if intent == "weather" and "degrees" in answer:
            # Extract key weather info
            temp_match = re.search(r'(\d+)\s*degrees', answer, re.IGNORECASE)
            if temp_match:
                temp = temp_match.group(1)
                response = f"The temperature is {temp} degrees"
                
                # Add conditions if found
                conditions = ["sunny", "cloudy", "rainy", "clear", "partly cloudy"]
                for cond in conditions:
                    if cond in answer.lower():
                        response += f" and {cond}"
                        break
                        
                response += " in San Marcos, Texas."
                self.speak(response)
                return
                
        # Default - speak the answer
        self.speak(self.clean_for_speech(answer))
        
    def display_code(self, code, command):
        """Save and open code"""
        try:
            # Determine filename
            if "calculator" in command.lower():
                filename = "calculator.py"
            elif "hello" in command.lower():
                filename = "hello_world.py"
            else:
                # Create filename from command
                words = command.lower().split()
                words = [w for w in words if w not in ["write", "create", "make", "a", "the", "code", "python"]]
                filename = "_".join(words[:2]) + ".py" if words else "code.py"
                
            filepath = os.path.join(self.work_dir, filename)
            with open(filepath, 'w') as f:
                f.write(code)
                
            print(f"💾 Code saved to: {filepath}")
                
            # Try editors in order of preference
            editors = [
                ("code", "VS Code"),
                ("notepad++", "Notepad++"),
                ("notepad", "Notepad")
            ]
            
            opened = False
            for cmd, name in editors:
                try:
                    subprocess.Popen([cmd, filepath])
                    self.speak(f"I've opened the code in {name} for you.")
                    opened = True
                    break
                except:
                    continue
                    
            if not opened:
                self.speak("I've saved the code but couldn't open an editor.")
                    
        except Exception as e:
            print(f"Error saving code: {e}")
            self.speak("I've written the code but couldn't save it.")
            
    def handle_quick_file(self, command):
        """Handle quick file opening from config"""
        cmd_lower = command.lower()
        quick_files = self.personal_config.get_quick_files()
        
        for name, file_path in quick_files.items():
            if name in cmd_lower:
                if os.path.exists(file_path):
                    try:
                        print(f"📄 Opening quick file: {file_path}")
                        if platform.system() == "Windows":
                            os.startfile(file_path)
                        elif platform.system() == "Darwin":
                            subprocess.Popen(["open", file_path])
                        else:
                            subprocess.Popen(["xdg-open", file_path])
                            
                        self.speak(f"I've opened your {name} file.")
                        return
                    except Exception as e:
                        print(f"Error opening file: {e}")
                        self.speak(f"I couldn't open your {name} file.")
                        return
                else:
                    self.speak(f"I couldn't find your {name} file at the configured location.")
                    return
                    
    def handle_website(self, command):
        """Handle website opening from config"""
        cmd_lower = command.lower()
        websites = self.personal_config.get_websites()
        
        for name, url in websites.items():
            if name in cmd_lower and name != "news":  # news handled separately
                try:
                    print(f"🌐 Opening website: {url}")
                    if platform.system() == "Windows":
                        subprocess.Popen(['start', '', url], shell=True)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(['open', url])
                    else:
                        subprocess.Popen(['xdg-open', url])
                        
                    self.speak(f"I'm opening {name} in your browser.")
                    return
                except Exception as e:
                    print(f"Error opening browser: {e}")
                    self.speak(f"I couldn't open {name}.")
                    return
            
    def handle_app_launch(self, command):
        """Handle application launching"""
        cmd_lower = command.lower()
        
        # Application mappings for Windows with full paths
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
            "visual studio code": ["code", "Visual Studio Code"]
        }
        
        # Find which app to launch
        app_to_launch = None
        app_name = None
        
        for app_key, (command_name, display_name) in app_commands.items():
            if app_key in cmd_lower:
                app_to_launch = command_name
                app_name = display_name
                break
                
        if app_to_launch:
            try:
                print(f"🚀 Launching {app_name}...")
                if platform.system() == "Windows":
                    # First try the full path
                    if os.path.exists(app_to_launch):
                        subprocess.Popen([app_to_launch])
                    else:
                        # If full path doesn't exist, try alternate paths
                        alternate_paths = []
                        
                        # For Office apps, try different versions
                        if "Office16" in app_to_launch:
                            alternate_paths.append(app_to_launch.replace("Office16", "Office15"))
                            alternate_paths.append(app_to_launch.replace("Office16", "Office14"))
                            alternate_paths.append(app_to_launch.replace(r"C:\Program Files", r"C:\Program Files (x86)"))
                            
                        # Try alternate paths
                        launched = False
                        for alt_path in alternate_paths:
                            if os.path.exists(alt_path):
                                subprocess.Popen([alt_path])
                                launched = True
                                break
                                
                        # If still not found, try using start command
                        if not launched:
                            subprocess.Popen(f'start "" "{app_name}"', shell=True)
                            
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", "-a", app_name])
                else:  # Linux
                    subprocess.Popen([app_to_launch])
                    
                self.speak(f"I've opened {app_name} for you.")
                print(f"✅ Launched {app_name}")
            except Exception as e:
                print(f"Error launching {app_name}: {e}")
                self.speak(f"I couldn't open {app_name}. Make sure it's installed.")
        else:
            self.speak("I'm not sure which application you want me to open.")


def main():
    """Launch Fixed Nina"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    print("🚀 Starting Nina...\n")
    
    # Check for required dependencies
    try:
        import psutil
    except ImportError:
        print("⚠️ psutil not installed. Install with: pip install psutil")
        print("   Hardware info will be limited without it.\n")
    
    try:
        # Initialize provider
        with quiet():
            provider = Provider(
                provider_name=config["MAIN"]["provider_name"],
                model=config["MAIN"]["provider_model"],
                server_address=config["MAIN"]["provider_server_address"],
                is_local=config.getboolean('MAIN', 'is_local')
            )
            
        print("✅ LLM provider initialized")
        
        # Initialize browser
        browser = None
        browser_agents_enabled = True
        try:
            with quiet():
                browser = Browser(
                    create_driver(
                        headless=config.getboolean('BROWSER', 'headless_browser'),
                        stealth_mode=config.getboolean('BROWSER', 'stealth_mode'),
                        lang='en'
                    ),
                    anticaptcha_manual_install=False
                )
            print("✅ Browser initialized")
        except Exception as e:
            print(f"⚠️ Browser initialization failed: {e}")
            print("   Web search and browser features will be disabled")
            print("   Make sure Chrome/Chromium is installed and chromedriver is available")
            browser_agents_enabled = False
        
        # Initialize agents
        personality = "base"
        agents = []
        
        # Always initialize casual agent
        try:
            agents.append(CasualAgent("Nina", f"prompts/{personality}/casual_agent.txt", provider, False))
            print("✅ Casual agent ready")
        except Exception as e:
            print(f"❌ Casual agent failed: {e}")
            
        # Browser agent (only if browser is available)
        if browser and browser_agents_enabled:
            try:
                agents.append(BrowserAgent("Bob", f"prompts/{personality}/browser_agent.txt", provider, False, browser))
                print("✅ Browser agent ready")
            except Exception as e:
                print(f"❌ Browser agent failed: {e}")
        else:
            print("⚠️ Browser agent disabled (no browser)")
                
        # File agent - Direct Search
        try:
            agents.append(DirectFileSearchAgent("Charlie", None, provider, False))
            print("✅ File agent ready (Direct Search)")
        except Exception as e:
            print(f"❌ File agent failed: {e}")
            
        # Coder agent
        try:
            agents.append(CoderAgent("Alice", f"prompts/{personality}/coder_agent.txt", provider, False))
            print("✅ Coder agent ready")
        except Exception as e:
            print(f"❌ Coder agent failed: {e}")
            
        # Hardware agent
        try:
            agents.append(HardwareAgent("HAL", None, provider, False))
            print("✅ Hardware agent ready")
        except Exception as e:
            print(f"❌ Hardware agent failed: {e}")
        
        if len(agents) < 2:
            print("\n❌ Not enough agents initialized!")
            print("   Please check your configuration and dependencies.")
            sys.exit(1)
            
        print(f"\n✅ {len(agents)} agents ready")
        print("="*50 + "\n")
        
        # Start Nina
        nina = NinaFixed(agents, config)
        nina.start()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Check Ollama is running: ollama serve")
        print("2. Check model is installed: ollama pull mistral:7b-instruct-q4_K_M")
        print("3. Check Vosk model is downloaded to: vosk-model-en-us-0.22/")
        print("4. Check your config.ini settings")


if __name__ == "__main__":
    main()