#!/usr/bin/env python3
"""
Nina + Agentic Seek Integration
Combines Nina's responsive voice interface with Agentic Seek's computer control
"""

import os
import sys
import asyncio
import configparser
import time
import threading
import pygame
from datetime import datetime
from pathlib import Path

# Add Agentic Seek to path
AGENTIC_SEEK_PATH = Path(__file__).parent / "Agentic_Seek"
sys.path.insert(0, str(AGENTIC_SEEK_PATH))

# Import Agentic Seek components
from sources.llm_provider import Provider
from sources.interaction import Interaction
from sources.agents import CasualAgent, CoderAgent, FileAgent, PlannerAgent, BrowserAgent
from sources.browser import Browser, create_driver
from sources.utility import pretty_print

# Import Nina components
import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import edge_tts
import io
from silero_live_vad import vad_stream

# Initialize pygame for audio
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

class NinaIntegration:
    """Enhanced Nina with Agentic Seek integration"""
    
    def __init__(self):
        # Load configs
        self.config = configparser.ConfigParser()
        self.config.read(AGENTIC_SEEK_PATH / 'config.ini')
        
        # Nina settings
        self.nina_config = {
            "wake_word": "nina",
            "wake_patterns": ['nina', 'nena', 'mina', 'lina'],
            "voice": "en-US-JennyNeural",
            "whisper_model": "tiny",
            "awake": True,
            "last_wake_time": 0,
            "is_speaking": False,
        }
        
        # Load Whisper
        print("📦 Loading Whisper...")
        self.whisper_model = whisper.load_model(self.nina_config["whisper_model"])
        
        # Initialize Agentic Seek components
        self.setup_agentic_seek()
        
        # Override Agentic Seek's voice methods
        self.patch_voice_methods()
        
        # Stop event for interruptions
        self.stop_speaking = threading.Event()
        
    def setup_agentic_seek(self):
        """Initialize Agentic Seek components"""
        print("🤖 Setting up Agentic Seek...")
        
        # Update config for Nina
        self.config.set('MAIN', 'agent_name', 'Nina')
        self.config.set('MAIN', 'provider_model', 'phi3:mini')  # Use faster model
        
        # Initialize provider
        self.provider = Provider(
            provider_name=self.config["MAIN"]["provider_name"],
            model=self.config["MAIN"]["provider_model"],
            server_address=self.config["MAIN"]["provider_server_address"],
            is_local=self.config.getboolean('MAIN', 'is_local')
        )
        
        # Initialize browser
        languages = self.config["MAIN"]["languages"].split(' ')
        self.browser = Browser(
            create_driver(
                headless=self.config.getboolean('BROWSER', 'headless_browser'),
                stealth_mode=self.config.getboolean('BROWSER', 'stealth_mode'),
                lang=languages[0]
            ),
            anticaptcha_manual_install=self.config.getboolean('BROWSER', 'stealth_mode')
        )
        
        # Initialize agents with Nina personality
        personality_folder = "nina"  # We'll create this
        self.agents = [
            NinaCasualAgent(
                name="Nina",
                prompt_path=f"prompts/{personality_folder}/casual_agent.txt",
                provider=self.provider,
                verbose=False
            ),
            CoderAgent(
                name="Coder",
                prompt_path=f"prompts/{personality_folder}/coder_agent.txt",
                provider=self.provider,
                verbose=False
            ),
            FileAgent(
                name="File Agent",
                prompt_path=f"prompts/{personality_folder}/file_agent.txt",
                provider=self.provider,
                verbose=False
            ),
            BrowserAgent(
                name="Browser",
                prompt_path=f"prompts/{personality_folder}/browser_agent.txt",
                provider=self.provider,
                verbose=False,
                browser=self.browser
            ),
            PlannerAgent(
                name="Planner",
                prompt_path=f"prompts/{personality_folder}/planner_agent.txt",
                provider=self.provider,
                verbose=False,
                browser=self.browser
            )
        ]
        
        # Initialize interaction
        self.interaction = Interaction(
            self.agents,
            tts_enabled=False,  # We'll use Nina's TTS
            stt_enabled=False,  # We'll use Nina's STT
            recover_last_session=self.config.getboolean('MAIN', 'recover_last_session'),
            langs=languages
        )
        
        print("✅ Agentic Seek ready!")
        
    def patch_voice_methods(self):
        """Override Agentic Seek's voice methods with Nina's"""
        # Override get_user to use Nina's voice detection
        self.interaction.get_user = self.nina_get_user
        
        # Override speak to use Nina's TTS
        self.interaction.speak_answer = self.nina_speak_answer
        
    async def nina_speak(self, text):
        """Nina's fast TTS with interruption support"""
        self.nina_config["is_speaking"] = True
        self.stop_speaking.clear()
        
        try:
            # Generate speech
            communicate = edge_tts.Communicate(
                text, 
                self.nina_config["voice"], 
                rate="+10%"
            )
            
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            # Play with interruption check
            audio_stream = io.BytesIO(audio_data)
            pygame.mixer.music.load(audio_stream)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if self.stop_speaking.is_set():
                    pygame.mixer.music.stop()
                    break
                await asyncio.sleep(0.01)
                
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            self.nina_config["is_speaking"] = False
            
    def nina_speak_answer(self):
        """Wrapper for Agentic Seek's speak method"""
        if self.interaction.current_agent and self.interaction.current_agent.last_answer:
            asyncio.run(self.nina_speak(self.interaction.current_agent.last_answer))
            
    def nina_get_user(self):
        """Get user input through voice - this replaces Agentic Seek's input method"""
        # This will be called by VAD callback
        return self.last_user_input if hasattr(self, 'last_user_input') else ""
        
    def is_wake_word(self, text):
        """Check for wake word"""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.nina_config["wake_patterns"])
        
    def remove_wake_word(self, text):
        """Remove wake word from text"""
        text_lower = text.lower()
        for pattern in ['nina', 'hey nina', 'hi nina', 'hello nina', 'ok nina']:
            text_lower = text_lower.replace(pattern, '').strip()
        return text_lower if text_lower else text
        
    async def process_voice_command(self, text):
        """Process voice command through Agentic Seek"""
        # Check wake word
        current_time = time.time()
        
        if self.is_wake_word(text):
            self.nina_config["awake"] = True
            self.nina_config["last_wake_time"] = current_time
            
            # Extract command
            command = self.remove_wake_word(text)
            if command and len(command) > 2:
                text = command
            else:
                await self.nina_speak("Yes? How can I help?")
                return
                
        # Check if awake
        if not self.nina_config["awake"]:
            print("😴 (Not awake, say 'Nina')")
            return
            
        # Set the user input for Agentic Seek
        self.last_user_input = text
        
        # Process through Agentic Seek
        print(f"👤 You: {text}")
        
        try:
            # Let Agentic Seek handle it
            success = await self.interaction.think()
            
            if success:
                # Show and speak the answer
                self.interaction.show_answer()
                self.nina_speak_answer()
            else:
                await self.nina_speak("I had trouble understanding that.")
                
        except Exception as e:
            print(f"Error: {e}")
            await self.nina_speak("Sorry, I encountered an error.")
            
    def on_speech_detected(self, audio_data):
        """Callback for VAD detection"""
        # Interrupt if speaking
        if self.nina_config["is_speaking"]:
            self.stop_speaking.set()
            pygame.mixer.music.stop()
            time.sleep(0.1)
            
        # Transcribe
        sf.write("temp.wav", audio_data, 16000)
        
        try:
            result = self.whisper_model.transcribe(
                "temp.wav",
                language='en',
                fp16=False
            )
            text = result["text"].strip()
            
            if len(text) < 2:
                return
                
            # Process the command
            asyncio.run(self.process_voice_command(text))
            
        except Exception as e:
            print(f"Transcription error: {e}")
            
    def run(self):
        """Main run loop"""
        print("\n" + "="*60)
        print("🚀 Nina + Agentic Seek - AI Assistant with Computer Control")
        print("="*60)
        print("🎤 Say 'Nina' followed by your command")
        print("\n📋 Examples:")
        print("   • 'Nina, open Google and search for Python tutorials'")
        print("   • 'Nina, create a new Python file with a hello world script'")
        print("   • 'Nina, what files are in my Documents folder?'")
        print("   • 'Nina, take a screenshot'")
        print("\n✅ Listening...")
        print("="*60 + "\n")
        
        try:
            # Start VAD with callback
            vad_stream(
                callback_on_speech=self.on_speech_detected,
                min_speech_duration=0.3,
                max_silence_duration=0.5
            )
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            if self.config.getboolean('MAIN', 'save_session'):
                self.interaction.save_session()
            sys.exit(0)


class NinaCasualAgent(CasualAgent):
    """Nina's personality layer on top of Casual Agent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.personality_traits = {
            "friendly": True,
            "helpful": True,
            "concise": True,
            "proactive": True
        }
        
    async def think(self, query=None):
        """Enhanced think method with Nina's personality"""
        # Add personality to responses
        if query:
            # Quick responses for common queries
            query_lower = query.lower()
            
            if "time" in query_lower:
                self.last_answer = datetime.now().strftime("It's %I:%M %p")
                return True
                
            if "hello" in query_lower or "hi" in query_lower:
                self.last_answer = "Hello! How can I help you today?"
                return True
                
        # For complex queries, use parent's think method
        return await super().think(query)


def create_nina_prompts():
    """Create Nina personality prompts"""
    nina_prompts_dir = AGENTIC_SEEK_PATH / "prompts" / "nina"
    nina_prompts_dir.mkdir(parents=True, exist_ok=True)
    
    # Casual agent prompt
    casual_prompt = """You are Nina, a friendly and helpful AI assistant with computer control capabilities.

Your personality traits:
- Friendly and warm, but professional
- Concise and to-the-point
- Proactive in offering help
- Technically capable but explains things simply

When responding:
1. Be conversational but efficient
2. If asked to do something on the computer, confirm what you're about to do
3. Provide brief status updates during tasks
4. If something fails, explain simply and offer alternatives

Remember: You can control the computer, browse the web, manage files, and write code. Always be helpful and friendly."""
    
    (nina_prompts_dir / "casual_agent.txt").write_text(casual_prompt)
    
    # Copy other prompts from base
    base_prompts = AGENTIC_SEEK_PATH / "prompts" / "base"
    if base_prompts.exists():
        for prompt_file in base_prompts.glob("*.txt"):
            if prompt_file.name != "casual_agent.txt":
                (nina_prompts_dir / prompt_file.name).write_text(prompt_file.read_text())
    
    print("✅ Nina prompts created!")


if __name__ == "__main__":
    # Create Nina prompts if they don't exist
    create_nina_prompts()
    
    # Run Nina with Agentic Seek
    nina = NinaIntegration()
    nina.run()