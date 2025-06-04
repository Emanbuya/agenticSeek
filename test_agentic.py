#!/usr/bin/env python3
"""
Test basic Agentic Seek functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_basic():
    """Test basic agent functionality"""
    print("🧪 Testing Agentic Seek components...\n")
    
    try:
        # Import components
        from sources.llm_provider import Provider
        from sources.agents import CasualAgent
        import configparser
        
        # Load config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        print("✅ Config loaded")
        
        # Test provider
        provider = Provider(
            provider_name=config["MAIN"]["provider_name"],
            model="phi3:mini",  # Use faster model
            server_address=config["MAIN"]["provider_server_address"],
            is_local=config.getboolean('MAIN', 'is_local')
        )
        
        print("✅ Provider created")
        
        # Test creating agent
        agent = CasualAgent(
            name="TestAgent",
            prompt_path="prompts/base/casual_agent.txt",
            provider=provider,
            verbose=True
        )
        
        print("✅ Agent created")
        
        # Check Memory structure
        print("\n📝 Memory object attributes:")
        for attr in dir(agent.memory):
            if not attr.startswith('_'):
                print(f"   - {attr}")
        
        # Test simple query
        print("\n🤖 Testing simple query...")
        query = "What is 2 + 2?"
        success = await agent.think(query)
        
        if success:
            print(f"✅ Query successful!")
            print(f"📤 Answer: {agent.last_answer}")
        else:
            print("❌ Query failed")
            
        # Test another query
        print("\n🤖 Testing another query...")
        query2 = "What time is it?"
        success2 = await agent.think(query2)
        
        if success2:
            print(f"✅ Query successful!")
            print(f"📤 Answer: {agent.last_answer}")
        else:
            print("❌ Query failed")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🧪 Agentic Seek Component Test")
    print("="*50)
    
    # Set GPU environment
    os.environ['OLLAMA_GPU_LAYERS'] = '999'
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama is running")
            
            # List available models
            data = response.json()
            if 'models' in data:
                print("\n📦 Available models:")
                for model in data['models']:
                    print(f"   - {model['name']}")
                print()
        else:
            print("⚠️  Ollama not responding properly")
            return
    except Exception as e:
        print(f"⚠️  Ollama check failed: {e}")
        return
    
    # Run test
    asyncio.run(test_basic())

if __name__ == "__main__":
    main()