#!/usr/bin/env python3
"""
Nina Voice Assistant - Main Entry Point
Handles voice recognition, speech synthesis, and command processing
"""

import json
import pyaudio
import asyncio
import time
import os
import sys
import pygame
import tempfile
from vosk import Model, KaldiRecognizer
import configparser
from datetime import datetime
from pathlib import Path

# Local imports
from nina_config import PersonalConfig
from nina_agents import HardwareAgent, DirectFileSearchAgent
from nina_handlers import CommandHandlers
from nina_utils import quiet, clean_for_speech, animate_thinking, pretty_print

# Import Agentic Seek components
with quiet():
    from sources.llm_provider import Provider
    from sources.agents.casual_agent import CasualAgent
    from sources.agents.code_agent import CoderAgent
    from sources.agents.file_agent import FileAgent
    from sources.agents.browser_agent import BrowserAgent
    from sources.agents.planner_agent import PlannerAgent
    from sources.browser import Browser, create_driver
    from sources.router import AgentRouter


class Nina:
    """Main Nina Voice Assistant class"""
    
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
        os.makedirs(self.work_dir, exist_ok=True)
        
        # Initialize handlers
        self.handlers = CommandHandlers(self)
        
        # Fix agent types
        self._fix_agent_types()
        
        print("🎙️ Setting up speech recognition...")
        self._init_speech_recognition()
        
        print("🔊 Setting up natural voice...")
        self.voice = "en-US-AriaNeural"
        
        # State
        self.is_running = True
        self.command_buffer = []
        self.last_command_time = 0
        self.last_code = None
        
        # Initialize pygame for audio
        pygame.mixer.init()
        
    def _fix_agent_types(self):
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
                    
    def _init_speech_recognition(self):
        """Initialize Vosk speech recognition"""
        model_path = "vosk-model-en-us-0.22"
        
        if not os.path.exists(model_path):
            print(f"❌ Please download Vosk model to: {model_path}/")
            sys.exit(1)
            
        with quiet():
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            
    def speak(self, text):
        """Speak text using Edge TTS"""
        if not text:
            return
            
        text = clean_for_speech(text, self)
        print(f"💬 Nina: {text}")
        
        # Edge TTS
        import edge_tts
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
        
    def start(self):
        """Start Nina main loop"""
        self._show_welcome()
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
            
    def _show_welcome(self):
        """Show welcome message"""
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
║  • "Ping google.com"                                  ║
║  • "Open admin command prompt"                        ║
║  • "What's my IP address?"                           ║
║                                                        ║
║  Say "goodbye" to exit                                ║
╚════════════════════════════════════════════════════════╝
        """)
        
    def process_command(self, command):
        """Process voice command - delegates to handlers"""
        # Let handlers process the command
        self.handlers.process_command(command)
        
    def get_agent_by_name(self, agent_name):
        """Get agent by name"""
        for agent in self.agents:
            if hasattr(agent, 'agent_name') and agent.agent_name == agent_name:
                return agent
        return None


def main():
    """Launch Nina"""
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
        nina = Nina(agents, config)
        nina.start()

        # Optional: LLM switcher
        try:
            from nina_llm_switcher import add_llm_switching_to_nina
            add_llm_switching_to_nina(nina)
            print("✅ LLM switcher initialized")
        except ImportError as e:
            print(f"⚠️ LLM switcher not available: {e}")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()

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