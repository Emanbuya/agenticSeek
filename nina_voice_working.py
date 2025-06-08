# nina_ultimate.py
"""
Nina Voice Assistant - Ultimate Version
- Personal configuration support
- Folder/directory understanding
- Schedule checking
- Fixed code agent routing
- Enhanced file/folder operations
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
from datetime import datetime, date
import pygame
import edge_tts
from pathlib import Path

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


class PersonalConfig:
    """Load and manage personal configuration"""
    
    def __init__(self, config_path="nina_personal.ini"):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        
        # Create default config if it doesn't exist
        if not os.path.exists(config_path):
            self.create_default_config()
        
        self.config.read(config_path)
        
    def create_default_config(self):
        """Create a default personal config file"""
        default_config = """[FOLDERS]
documents = C:\\Users\\{username}\\OneDrive\\Documents
downloads = C:\\Users\\{username}\\Downloads
desktop = C:\\Users\\{username}\\Desktop

[QUICK_FILES]
resume = C:\\Users\\{username}\\OneDrive\\Documents\\Resume.pdf

[SCHEDULE]
monday = No meetings scheduled
tuesday = No meetings scheduled

[PREFERENCES]
location = San Marcos, Texas
""".format(username=os.environ.get('USERNAME', 'User'))
        
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
        """Get schedule for a specific day or today"""
        if not self.config.has_section('SCHEDULE'):
            return None
            
        if day is None:
            day = date.today().strftime("%A").lower()
        else:
            day = day.lower()
            
        if self.config.has_option('SCHEDULE', day):
            schedule_str = self.config.get('SCHEDULE', day)
            # Parse schedule entries
            entries = []
            for entry in schedule_str.split(','):
                if '|' in entry:
                    activity, time = entry.strip().split('|')
                    entries.append({
                        'activity': activity.strip(),
                        'time': time.strip()
                    })
            return entries
        return None


class NinaUltimate:
    """Ultimate Nina with all features"""
    
    def __init__(self, agents, config):
        self.agents = agents
        self.config = config
        
        # Load personal configuration
        self.personal_config = PersonalConfig()
        print("✅ Personal configuration loaded")
        
        # Initialize router
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
        """Ensure agents have correct types and routing"""
        for agent in self.agents:
            # Fix coder agent type
            if hasattr(agent, 'agent_name') and agent.agent_name == "Alice":
                agent.type = "coder_agent"
                agent.role = "code"
                print(f"✅ Fixed coder agent type for {agent.agent_name}")
                
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
            
        # Extract key info for certain responses
        if "degrees" in text or "temperature" in text:
            weather_info = self.extract_weather_info(text)
            if weather_info:
                text = weather_info
        
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
        
    def extract_weather_info(self, text):
        """Extract weather information"""
        temp_match = re.search(r'(\d+)\s*degrees', text, re.IGNORECASE)
        if not temp_match:
            return None
            
        temp = temp_match.group(1)
        location = self.personal_config.config.get('PREFERENCES', 'location', fallback='your location')
        
        response = f"The current weather in {location} is {temp} degrees"
        
        # Add conditions
        conditions = ["cloudy", "sunny", "rainy", "clear", "partly cloudy"]
        for cond in conditions:
            if cond in text.lower():
                response += f" and {cond}"
                break
                
        return response + "."
        
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
            
        # Clean paths for speech
        text = re.sub(r'[A-Z]:\\[^\s]+', 'in the folder', text)
        text = re.sub(r'https?://\S+', '', text)
        
        # Replacements
        replacements = {
            "TX": "Texas",
            ".py": " dot py",
            "\\": " ",
            "/": " ",
            "...": "."
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
        # Show configured folders
        folders = self.personal_config.get_all_folders()
        folder_list = "\n".join([f"║  • \"{name}\" → {path[:40]}..." for name, path in list(folders.items())[:3]])
        
        print(f"""
╔════════════════════════════════════════════════════════╗
║          Nina - Ultimate Personal Assistant            ║
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
║  • "What's my schedule today?"                        ║
║  • "Check my meetings for tomorrow"                   ║
║  • "Write a Python calculator"                        ║
║  • "Who won the Dodgers game?"                       ║
║  • "What's the weather?"                              ║
║                                                        ║
║  Say "goodbye" to exit                                ║
╚════════════════════════════════════════════════════════╝
        """)
        
        self.speak("Hello! I'm Nina, your ultimate assistant. I can open folders, check your schedule, write code, search the web, and more. What can I help you with?")
        
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
            
    def process_command(self, command):
        """Process command with enhanced understanding"""
        # Exit check
        if any(word in command.lower() for word in ["stop", "exit", "goodbye", "quit", "bye"]):
            self.is_running = False
            return
            
        # Check for schedule queries first
        if self.is_schedule_query(command):
            self.handle_schedule_query(command)
            return
            
        # Enhance command
        enhanced_command = self.enhance_command(command)
        intent = self.determine_intent(enhanced_command, command)
        
        print(f"🎯 Intent: {intent} | Command: {enhanced_command}")
        
        # Feedback
        feedback = {
            "weather": "Let me check the weather...",
            "time": "Checking the time...",
            "files": "I'll help you with that...",
            "folder": "I'll open that folder for you...",
            "code": "I'll write that code for you...",
            "search": "Let me search for that information...",
            "sports": "Let me find the latest sports results...",
            "news": "Let me search for the latest news...",
            "general": "Let me help with that..."
        }
        
        self.speak(feedback.get(intent, "Processing..."))
        
        # Handle folder operations specially
        if intent == "folder":
            self.handle_folder_operation(command)
            return
            
        # Execute with appropriate agent
        try:
            agent = self.get_agent_by_intent(intent)
            
            if not agent:
                self.speak("I'm having trouble with that request.")
                return
                
            print(f"🤖 Using agent: {agent.agent_name} (type: {agent.type})")
            
            # Special setup
            if agent.type == "file_agent":
                if hasattr(agent, 'tools') and 'file_finder' in agent.tools:
                    agent.tools['file_finder'].work_dir = self.documents_path
                    
            with quiet():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                class DummySpeech:
                    def speak(self, text): pass
                
                answer, _ = loop.run_until_complete(
                    agent.process(enhanced_command, DummySpeech())
                )
                loop.close()
                
            # Handle response
            if answer:
                self.handle_response(answer, intent, command)
            else:
                self.speak("I couldn't complete that task. Please try again.")
                
        except Exception as e:
            print(f"Error: {e}")
            self.speak("I encountered an error. Please try again.")
            
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
            response = f"Your schedule for {day.capitalize()}:\n"
            for entry in schedule:
                response += f"{entry['activity']} at {entry['time']}. "
            self.speak(response)
        else:
            self.speak(f"You have no scheduled meetings for {day.capitalize()}.")
            
    def handle_folder_operation(self, command):
        """Handle folder opening operations"""
        cmd_lower = command.lower()
        
        # Check personal config for folder nicknames
        folders = self.personal_config.get_all_folders()
        
        folder_path = None
        folder_name = None
        
        # Check each configured folder
        for nickname, path in folders.items():
            if nickname in cmd_lower:
                folder_path = path
                folder_name = nickname
                break
                
        if folder_path and os.path.exists(folder_path):
            try:
                # Open in Windows Explorer
                subprocess.Popen(['explorer', folder_path])
                self.speak(f"I've opened the {folder_name} folder for you.")
                print(f"📂 Opened: {folder_path}")
            except Exception as e:
                print(f"Error opening folder: {e}")
                self.speak(f"I found the {folder_name} folder but couldn't open it.")
        else:
            self.speak("I couldn't find that folder. Check your nina_personal.ini file to add custom folder locations.")
            
    def get_agent_by_intent(self, intent):
        """Get agent by intent - fixed for code agent"""
        intent_to_type = {
            "weather": "browser_agent",
            "time": "browser_agent",
            "search": "browser_agent",
            "sports": "browser_agent",
            "news": "browser_agent",
            "files": "file_agent",
            "folder": "file_agent",
            "code": "coder_agent",  # This should work now
            "general": "casual_agent"
        }
        
        agent_type = intent_to_type.get(intent, "casual_agent")
        
        # Find agent by type
        for agent in self.agents:
            if hasattr(agent, 'type') and agent.type == agent_type:
                return agent
                
        # Debug: show available agents
        print(f"⚠️ No agent found for type: {agent_type}")
        print(f"Available agents: {[(a.agent_name, a.type) for a in self.agents if hasattr(a, 'type')]}")
        
        return self.agents[0]  # Default
            
    def enhance_command(self, command):
        """Enhance command for better processing"""
        cmd_lower = command.lower()
        
        # Don't enhance folder commands
        if "folder" in cmd_lower or "open" in cmd_lower:
            return command
            
        # Sports queries
        if any(word in cmd_lower for word in ["game", "score", "won", "lost", "beat"]):
            if "search" not in cmd_lower:
                command = "search for " + command
            return command
            
        # News queries
        if any(word in cmd_lower for word in ["news", "latest", "breaking"]):
            if "search" not in cmd_lower:
                command = "search for " + command
            return command
            
        # Weather
        if "weather" in cmd_lower:
            location = self.personal_config.config.get('PREFERENCES', 'location', fallback='San Marcos Texas')
            if location.lower() not in cmd_lower.lower():
                command = f"search for current weather in {location}"
                
        # Code
        elif any(word in cmd_lower for word in ["write", "create", "make"]) and \
             any(word in cmd_lower for word in ["code", "script", "program", "calculator"]):
            if "calculator" in cmd_lower:
                command = "write a Python calculator program with basic operations add, subtract, multiply, divide"
                
        # Time
        elif "time" in cmd_lower:
            command = "what is the current time"
            
        return command
        
    def determine_intent(self, enhanced_command, original_command):
        """Determine intent - enhanced version"""
        cmd = original_command.lower()
        
        # Folder operations - PRIORITY
        if any(word in cmd for word in ["folder", "directory"]) and \
           any(word in cmd for word in ["open", "show", "go to", "access"]):
            return "folder"
            
        # Sports
        if any(word in cmd for word in ["game", "score", "won", "lost", "beat", "match",
                                        "baseball", "football", "basketball", "dodgers"]):
            return "sports"
            
        # News
        if any(word in cmd for word in ["news", "headline", "breaking"]):
            return "news"
            
        # Weather
        if any(word in cmd for word in ["weather", "temperature", "forecast"]):
            return "weather"
            
        # Time
        if "time" in cmd and any(word in cmd for word in ["what", "current"]):
            return "time"
            
        # Code - IMPORTANT: Check for code-related words
        if any(word in cmd for word in ["code", "program", "script", "calculator", "function"]) and \
           any(word in cmd for word in ["write", "create", "make", "build", "develop"]):
            return "code"
            
        # Files (not folders)
        if any(word in cmd for word in ["file", "document", "resume", "pdf"]) and \
           not any(word in cmd for word in ["folder", "directory"]):
            return "files"
            
        # General search
        if any(phrase in cmd for phrase in ["who is", "what is", "search for"]):
            return "search"
            
        return "general"
            
    def handle_response(self, answer, intent, original_command):
        """Handle response appropriately"""
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
            
        # Weather
        if intent == "weather":
            self.speak(answer)
            return
            
        # Sports/News
        if intent in ["sports", "news", "search"]:
            # Extract key info
            if len(answer) > 300:
                sentences = answer.split('.')
                key_sentences = []
                for s in sentences:
                    if any(term in s.lower() for term in ["won", "beat", "score", "lead", "announce"]):
                        key_sentences.append(s.strip())
                        if len(key_sentences) >= 2:
                            break
                            
                response = ". ".join(key_sentences) + "." if key_sentences else sentences[0]
            else:
                response = answer
                
            self.speak(self.clean_for_speech(response))
            return
            
        # Default
        response = self.format_response(answer, intent, original_command)
        self.speak(response)
        
    def display_code(self, code, command):
        """Save and open code"""
        try:
            # Determine filename
            if "calculator" in command.lower():
                filename = "calculator.py"
            elif "hello" in command.lower():
                filename = "hello_world.py"
            else:
                # Extract meaningful name
                words = re.findall(r'\w+', command.lower())
                filtered = [w for w in words if w not in ["write", "create", "make", "code", "a", "the"]]
                filename = "_".join(filtered[:3]) + ".py" if filtered else "code.py"
                
            filepath = os.path.join(self.work_dir, filename)
            with open(filepath, 'w') as f:
                f.write(code)
                
            print(f"💾 Code saved to: {filepath}")
                
            # Try editors
            editors = [
                ("code", "VS Code"),
                ("notepad++", "Notepad++"),
                ("notepad", "Notepad")
            ]
            
            for cmd, name in editors:
                try:
                    subprocess.Popen([cmd, filepath])
                    self.speak(f"I've opened the code in {name} for you.")
                    break
                except:
                    continue
                    
        except Exception as e:
            print(f"Error: {e}")
            self.speak("I've written the code but couldn't open the editor.")
            
    def format_response(self, answer, intent, original_command):
        """Format response for speech"""
        if not answer:
            return "Done."
            
        if intent == "time":
            current_time = datetime.now().strftime("%I:%M %p")
            return f"It's {current_time}."
            
        elif intent == "files":
            if "couldn't find" in answer.lower():
                return "I couldn't find that file. Check your nina_personal.ini to add custom locations."
                
            if match := re.search(r'found (\d+) file', answer, re.IGNORECASE):
                count = match.group(1)
                return f"I found {count} files. Check the details on screen."
                    
        return self.clean_for_speech(answer)


def main():
    """Launch Ultimate Nina"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    print("🚀 Starting Nina Ultimate...\n")
    
    # Check for personal config
    if not os.path.exists("nina_personal.ini"):
        print("📝 Creating nina_personal.ini with default settings...")
        print("   Customize this file with your folder locations!\n")
    
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
        
        # Initialize agents with correct types
        personality = "base"
        agents = []
        
        # IMPORTANT: Initialize agents with correct properties
        agent_configs = [
            (CasualAgent, "Nina", "casual_agent", [], "talk"),
            (BrowserAgent, "Bob", "browser_agent", [browser], "web"),
            (FileAgent, "Charlie", "file_agent", [], "files"),
            (CoderAgent, "Alice", "coder_agent", [], "code"),  # Fixed
            (PlannerAgent, "Diana", "planner_agent", [browser], "planner")
        ]
        
        for AgentClass, name, agent_type, extra_args, role in agent_configs:
            try:
                with quiet():
                    prompt_path = f"prompts/{personality}/{agent_type}.txt"
                    agent = AgentClass(name, prompt_path, provider, False, *extra_args)
                    # Ensure type and role are set
                    agent.type = agent_type
                    agent.role = role
                    agents.append(agent)
                print(f"✅ {agent_type} initialized")
            except Exception as e:
                print(f"❌ Failed to initialize {agent_type}: {e}")
        
        if len(agents) < 2:
            print("\n❌ Not enough agents initialized!")
            sys.exit(1)
            
        print(f"\n✅ {len(agents)} agents ready\n")
        
        # Start Nina
        nina = NinaUltimate(agents, config)
        nina.start()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Add missing import
    from datetime import timedelta
    main()