# nina_voice_simple.py
"""
Nina Voice Mode - Simplified but fully functional
No complex dependencies, just working voice interaction
"""

import asyncio
import time
import numpy as np
import pyaudio
import threading
import queue
from datetime import datetime

# Agentic Seek imports
from sources.speech_to_text import Transcript
from sources.text_to_speech import Speech
from sources.router import AgentRouter
from sources.utility import pretty_print


class SimpleNinaVoice:
    """Simplified Nina voice system that actually works"""
    
    def __init__(self, agents, languages=['en']):
        # Core components
        self.agents = agents
        self.router = AgentRouter(agents, supported_language=languages)
        self.transcript = Transcript()
        self.speech = Speech(enable=True, language='en', voice_idx=1)
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.sample_rate = 16000
        self.chunk_size = 1024
        
        # State
        self.is_active = False
        self.is_listening = True
        self.wake_word = "nina"
        self.is_speaking = False  # Track when Nina is speaking
        
        # Queues
        self.audio_queue = queue.Queue()
        
        # Current context
        self.current_agent = None
        self.last_query = None
        self.last_answer = None
        
        # Voice activity detection parameters
        self.energy_threshold = 1000  # Increased from 500
        self.silence_chunks_needed = 8  # Reduced from 10 for faster response
        self.min_speech_chunks = 15  # Minimum chunks for valid speech
        
    def start(self):
        """Start the voice system"""
        print("""
        ╔══════════════════════════════════════════════════╗
        ║           Nina Voice Assistant                   ║
        ╟──────────────────────────────────────────────────╢
        ║  • Say "Nina" to activate                        ║
        ║  • Speak your command                            ║  
        ║  • No confirmation words needed                  ║
        ║  • Say "Nina stop" or "Nina shutdown" to exit   ║
        ║  • Press Ctrl+C to force quit                    ║
        ╚══════════════════════════════════════════════════╝
        """)
        
        # Initial greeting
        self.speech.speak("Nina ready. Say my name when you need me.")
        
        # Start threads
        audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        process_thread = threading.Thread(target=self._process_loop, daemon=True)
        
        audio_thread.start()
        process_thread.start()
        
        # Install signal handler for Ctrl+C
        import signal
        
        def signal_handler(sig, frame):
            print("\n\n🛑 Interrupt received! Shutting down...")
            self.is_listening = False
            self.speech.speak("Emergency shutdown. Goodbye!")
            # Force exit after speech
            import os
            os._exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep alive with better interrupt handling
        try:
            while self.is_listening:
                time.sleep(0.1)  # Shorter sleep for more responsive shutdown
                
                # Check if threads are still alive
                if not audio_thread.is_alive() or not process_thread.is_alive():
                    print("⚠️ Thread died, shutting down...")
                    break
                    
        except KeyboardInterrupt:
            print("\n✋ Keyboard interrupt - shutting down...")
            self.is_listening = False
            self.speech.speak("Shutting down. Goodbye!")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.is_listening = False
        finally:
            # Ensure cleanup
            self.is_listening = False
            print("👋 Nina has shut down.")
            # Force exit to ensure all threads stop
            import os
            os._exit(0)
    
    def _audio_loop(self):
        """Capture audio continuously with echo cancellation"""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        buffer = []
        silence_count = 0
        speech_detected = False
        
        while self.is_listening:
            try:
                # Don't capture when Nina is speaking
                if self.is_speaking:
                    time.sleep(0.1)
                    continue
                
                # Read chunk
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                
                # Calculate energy
                energy = np.sqrt(np.mean(chunk**2))
                
                # Voice activity detection
                if energy > self.energy_threshold:
                    # Speech detected
                    if not speech_detected:
                        print("🎙️ Speech detected...")
                        speech_detected = True
                    buffer.append(chunk)
                    silence_count = 0
                else:
                    # Silence
                    if speech_detected:
                        buffer.append(chunk)
                        silence_count += 1
                        
                        # End of speech detection
                        if silence_count >= self.silence_chunks_needed:
                            if len(buffer) >= self.min_speech_chunks:
                                # Valid speech segment
                                audio_data = np.concatenate(buffer)
                                self.audio_queue.put(audio_data)
                                print(f"📊 Captured {len(buffer)} chunks")
                            else:
                                print("🔇 Too short, ignoring...")
                            
                            # Reset
                            buffer = []
                            silence_count = 0
                            speech_detected = False
                
                # Prevent buffer overflow
                if len(buffer) > 160:  # ~10 seconds
                    print("⚠️ Buffer overflow, resetting...")
                    buffer = []
                    silence_count = 0
                    speech_detected = False
                    
            except Exception as e:
                print(f"Audio error: {e}")
        
        stream.stop_stream()
        stream.close()
    
    def _process_loop(self):
        """Process audio queue with faster response"""
        wake_detected_time = 0
        
        while self.is_listening:
            try:
                # Get audio with shorter timeout for faster response
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # Skip if Nina is speaking
                if self.is_speaking:
                    continue
                
                # Transcribe
                start_time = time.time()
                text = self.transcript.transcript_job(audio_data, sample_rate=self.sample_rate)
                transcribe_time = time.time() - start_time
                
                if text and len(text.strip()) > 0:
                    print(f"📝 Heard: {text} (in {transcribe_time:.1f}s)")
                    
                    # Ignore common Nina responses to prevent self-processing
                    nina_phrases = [
                        "quality is acceptable",
                        "i'm sensitive",
                        "yes, i'm listening",
                        "nina ready",
                        "goodbye"
                    ]
                    
                    if any(phrase in text.lower() for phrase in nina_phrases):
                        print("🔇 Ignoring Nina's own speech")
                        continue
                    
                    # Check for wake word
                    if self.wake_word in text.lower():
                        self.is_active = True
                        wake_detected_time = time.time()
                        
                        # Extract command after wake word
                        text_lower = text.lower()
                        wake_index = text_lower.find(self.wake_word)
                        command_part = text[wake_index + len(self.wake_word):].strip()
                        
                        if command_part and len(command_part) > 2:
                            # Command in same utterance - process immediately
                            print(f"⚡ Quick command: {command_part}")
                            asyncio.run(self._process_command(command_part))
                            self.is_active = False
                        else:
                            # Just wake word - quick response
                            self.is_speaking = True
                            self.speech.speak("Yes?")
                            self.is_speaking = False
                    
                    # If active, process as command
                    elif self.is_active and (time.time() - wake_detected_time < 5):
                        # Process command immediately
                        asyncio.run(self._process_command(text.strip()))
                        self.is_active = False
                    
            except queue.Empty:
                # Check for timeout
                if self.is_active and time.time() - wake_detected_time > 5:
                    print("⏰ Timeout - deactivating")
                    self.is_active = False
            except Exception as e:
                print(f"Process error: {e}")
    
    async def _process_command(self, command: str):
        """Process a voice command with faster response"""
        print(f"🤖 Processing: {command}")
        
        # Set speaking flag to prevent echo
        self.is_speaking = True
        
        try:
            # Check for exit commands - more variations
            exit_words = ['goodbye', 'bye', 'exit', 'quit', 'shutdown', 'stop', 'turn off', 'shut down']
            if any(word in command.lower() for word in exit_words):
                print("🛑 Exit command detected!")
                self.speech.speak("Shutting down. Goodbye!")
                self.is_listening = False
                # Force exit after a short delay
                import os
                time.sleep(2)
                os._exit(0)
                return
            
            # Quick responses for common queries
            quick_responses = {
                "how are you": "I'm doing great, thank you for asking!",
                "hello": "Hello! How can I help you?",
                "hi": "Hi there! What can I do for you?",
                "thank you": "You're welcome!",
                "thanks": "Happy to help!"
            }
            
            for trigger, response in quick_responses.items():
                if trigger in command.lower():
                    self.speech.speak(response)
                    self.is_speaking = False
                    return
            
            # Select agent
            agent = self.router.select_agent(command)
            if not agent:
                self.speech.speak("I'm not sure how to help with that.")
                self.is_speaking = False
                return
            
            self.current_agent = agent
            self.last_query = command
            
            # Process with agent
            pretty_print(f"Agent: {agent.agent_name}", color="info")
            
            # Quick acknowledgment for longer tasks
            if agent.type == "browser_agent":
                self.speech.speak("Let me search for that...")
            elif agent.type == "coder_agent":
                self.speech.speak("Writing code...")
            
            # Mock speech module for agent
            class MockSpeech:
                def speak(self, text):
                    pass
            
            mock_speech = MockSpeech()
            
            # Get response
            answer, reasoning = await agent.process(command, mock_speech)
            self.last_answer = answer
            
            if answer:
                # Clean up response for speech
                clean_answer = self._clean_for_speech(answer)
                
                # Speak response
                self.speech.speak(clean_answer)
            else:
                self.speech.speak("I couldn't process that request.")
                
        except Exception as e:
            print(f"Agent error: {e}")
            self.speech.speak("I encountered an error.")
        finally:
            # Always reset speaking flag
            self.is_speaking = False
    
    def _clean_for_speech(self, text: str) -> str:
        """Clean text for speech output"""
        # Remove code blocks
        if "```" in text:
            parts = text.split("```")
            text = parts[0].strip()
            if not text:
                text = "I've written the code for you. Check the screen for details."
        
        # Limit length
        if len(text) > 300:
            # Find a good breaking point
            sentences = text.split('. ')
            result = ""
            for sentence in sentences:
                if len(result) + len(sentence) < 280:
                    result += sentence + ". "
                else:
                    break
            text = result.strip() + ".."
        
        # Remove URLs
        import re
        text = re.sub(r'http[s]?://\S+', 'a web link', text)
        
        return text


async def launch_nina_voice():
    """Launch Nina with voice interaction"""
    import configparser
    from sources.llm_provider import Provider
    from sources.agents import CasualAgent, CoderAgent, FileAgent, BrowserAgent, PlannerAgent
    from sources.browser import Browser, create_driver
    
    # Load config
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    print("🚀 Initializing Nina Voice Mode...")
    
    # Initialize provider
    provider = Provider(
        provider_name=config["MAIN"]["provider_name"],
        model=config["MAIN"]["provider_model"],
        server_address=config["MAIN"]["provider_server_address"],
        is_local=config.getboolean('MAIN', 'is_local')
    )
    
    # Initialize browser
    languages = config["MAIN"]["languages"].split(' ')
    browser = Browser(
        create_driver(headless=True, stealth_mode=False, lang=languages[0]),
        anticaptcha_manual_install=False
    )
    
    # Initialize agents
    personality_folder = "jarvis" if config.getboolean('MAIN', 'jarvis_personality') else "base"
    
    agents = [
        CasualAgent(
            name="Nina",
            prompt_path=f"prompts/{personality_folder}/casual_agent.txt",
            provider=provider,
            verbose=False
        ),
        CoderAgent(
            name="coder",
            prompt_path=f"prompts/{personality_folder}/coder_agent.txt",
            provider=provider,
            verbose=False
        ),
        FileAgent(
            name="File Agent",
            prompt_path=f"prompts/{personality_folder}/file_agent.txt",
            provider=provider,
            verbose=False
        ),
        BrowserAgent(
            name="Browser",
            prompt_path=f"prompts/{personality_folder}/browser_agent.txt",
            provider=provider,
            verbose=False,
            browser=browser
        ),
        PlannerAgent(
            name="Planner",
            prompt_path=f"prompts/{personality_folder}/planner_agent.txt",
            provider=provider,
            verbose=False,
            browser=browser
        ),
    ]
    
    # Create and start Nina
    nina = SimpleNinaVoice(agents, languages)
    nina.start()


if __name__ == "__main__":
    asyncio.run(launch_nina_voice())