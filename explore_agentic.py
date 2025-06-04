#!/usr/bin/env python3
"""
Explore Agentic Seek structure to understand how to use it
"""

import asyncio
import os
import sys
from pathlib import Path

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent))

def explore_structure():
    """Explore the structure of Agentic Seek components"""
    print("🔍 Exploring Agentic Seek structure...\n")
    
    try:
        # Import components
        from sources.llm_provider import Provider
        from sources.agents import CasualAgent
        from sources.interaction import Interaction
        import configparser
        
        # Load config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Create provider
        provider = Provider(
            provider_name=config["MAIN"]["provider_name"],
            model="phi3:mini",
            server_address=config["MAIN"]["provider_server_address"],
            is_local=config.getboolean('MAIN', 'is_local')
        )
        
        # Create agent
        agent = CasualAgent(
            name="TestAgent",
            prompt_path="prompts/base/casual_agent.txt",
            provider=provider,
            verbose=True
        )
        
        # Explore agent methods and attributes
        print("📦 CasualAgent methods and attributes:")
        for attr in dir(agent):
            if not attr.startswith('_'):
                obj = getattr(agent, attr)
                if callable(obj):
                    print(f"   🔧 {attr}() - method")
                else:
                    print(f"   📝 {attr} - attribute")
        
        # Check if we need to use Interaction class
        print("\n📦 Checking Interaction class...")
        
        # Look at the CLI to see how it's used
        print("\n📄 Checking cli.py usage...")
        with open('cli.py', 'r') as f:
            lines = f.readlines()
            
        # Find how agents are used
        for i, line in enumerate(lines):
            if 'think' in line or 'ask' in line or 'process' in line:
                print(f"   Line {i+1}: {line.strip()}")
                
        # Try to find the actual method to process queries
        print("\n🔍 Looking for query processing methods...")
        
        # Check Interaction class
        print("\n📦 Interaction class methods:")
        test_agents = [agent]
        interaction = Interaction(
            test_agents,
            tts_enabled=False,
            stt_enabled=False,
            recover_last_session=False,
            langs=['en']
        )
        
        for attr in dir(interaction):
            if not attr.startswith('_'):
                obj = getattr(interaction, attr)
                if callable(obj):
                    print(f"   🔧 {attr}() - method")
                    
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 Agentic Seek Structure Explorer")
    print("="*50)
    
    explore_structure()

if __name__ == "__main__":
    main()