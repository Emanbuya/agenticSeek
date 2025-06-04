#!/usr/bin/env python3
"""
Simple Nina - Direct agent approach without complex routing
"""

import asyncio
import os
import sys
from pathlib import Path

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent))

from sources.llm_provider import Provider
from sources.agents import CasualAgent
from sources.browser import Browser, create_driver
from sources.utility import pretty_print
import configparser

class SimpleNina:
    def __init__(self):
        # Load config
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        # Set up provider
        self.provider = Provider(
            provider_name=self.config["MAIN"]["provider_name"],
            model=self.config["MAIN"]["provider_model"],
            server_address=self.config["MAIN"]["provider_server_address"],
            is_local=self.config.getboolean('MAIN', 'is_local')
        )
        
        # Create Nina's agent
        self.nina = CasualAgent(
            name="Nina",
            prompt_path="prompts/base/casual_agent.txt",
            provider=self.provider,
            verbose=True
        )
        
        # Add Nina's personality to the agent
        nina_personality = """You are Nina, a friendly and helpful AI assistant.
Be warm, concise, and helpful. You can control the computer, browse the web, and help with various tasks."""
        
        # Prepend personality to agent's system prompt
        self.nina.memory.system_prompt = nina_personality + "\n\n" + self.nina.memory.system_prompt
        
        print("✅ Nina is ready!")
        
    async def chat(self):
        """Simple chat loop"""
        print("\n💬 Chat with Nina (type 'exit' to quit)")
        print("="*50 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nNina: Goodbye! Have a great day! 👋")
                    break
                
                # Process with Nina
                success = await self.nina.think(user_input)
                
                if success and self.nina.last_answer:
                    print(f"\nNina: {self.nina.last_answer}\n")
                else:
                    print("\nNina: I'm sorry, I couldn't process that. Could you try again?\n")
                    
            except KeyboardInterrupt:
                print("\n\nNina: Goodbye! 👋")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Nina: I encountered an error. Let me try to recover...\n")

def main():
    print("🎤 Simple Nina - Direct Chat Mode")
    print("="*50)
    
    # Set GPU environment
    os.environ['OLLAMA_GPU_LAYERS'] = '999'
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            print("⚠️  Ollama not responding properly")
            return
    except:
        print("⚠️  Ollama not running! Start it with: ollama serve")
        return
    
    # Update config for Nina
    config = configparser.ConfigParser()
    config.read('config.ini')
    config['MAIN']['agent_name'] = 'Nina'
    config['MAIN']['provider_model'] = 'phi3:mini'  # Use faster model
    
    with open('config.ini', 'w') as f:
        config.write(f)
    
    # Run Nina
    nina = SimpleNina()
    asyncio.run(nina.chat())

if __name__ == "__main__":
    main()