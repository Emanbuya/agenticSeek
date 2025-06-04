#!/usr/bin/env python3
"""
Setup vanilla AgenticSeek - Get it working as-is first
"""

import os
import subprocess
import sys
import configparser

def setup_vanilla_agenticseek():
    """Setup AgenticSeek with default settings"""
    print("🚀 Setting up vanilla AgenticSeek")
    print("="*50)
    
    # 1. Create default config
    config = configparser.ConfigParser()
    
    config['MAIN'] = {
        'is_local': 'True',
        'provider_name': 'ollama',
        'provider_model': 'phi3:mini',  # Start with small model
        'provider_server_address': '127.0.0.1:11434',
        'agent_name': 'Jarvis',  # Default name
        'recover_last_session': 'False',
        'save_session': 'False',
        'speak': 'False',
        'listen': 'False',
        'work_dir': os.path.join(os.getcwd(), 'workspace'),
        'jarvis_personality': 'False',
        'languages': 'en'
    }
    
    config['BROWSER'] = {
        'headless_browser': 'False',
        'stealth_mode': 'False'
    }
    
    # Create workspace
    os.makedirs(config['MAIN']['work_dir'], exist_ok=True)
    
    # Save config
    with open('config.ini', 'w') as f:
        config.write(f)
    
    print("✅ Created default config.ini")
    
    # 2. Check requirements
    print("\n📋 Checking requirements:")
    
    # Check Ollama
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True)
        print("✅ Ollama installed")
        
        # Pull phi3:mini
        print("📥 Pulling phi3:mini model...")
        subprocess.run(['ollama', 'pull', 'phi3:mini'])
    except:
        print("❌ Ollama not found. Install from https://ollama.com/download")
        return
    
    # Check Docker
    try:
        subprocess.run(['docker', '--version'], capture_output=True)
        print("✅ Docker installed")
    except:
        print("❌ Docker not found. Install Docker Desktop")
        return
    
    print("\n🎯 Setup complete! Now run AgenticSeek:")
    print("\n1. Start Ollama:")
    print("   ollama serve")
    print("\n2. Start services (in new terminal):")
    if sys.platform.startswith('win'):
        print("   start start_services.cmd")
    else:
        print("   ./start_services.sh")
    print("\n3. Run AgenticSeek CLI (in new terminal):")
    print("   python cli.py")
    print("\n4. Or for Web UI, run API instead:")
    print("   python api.py")
    print("   Then open http://localhost:3000")

def test_cli_mode():
    """Quick test of CLI mode"""
    print("\n🧪 Testing CLI mode...")
    print("="*50)
    
    # Start Ollama in background
    print("Starting Ollama...")
    ollama = subprocess.Popen(['ollama', 'serve'])
    
    import time
    time.sleep(3)
    
    print("\n✅ Ready to test!")
    print("Run: python cli.py")
    print("\nExample commands to try:")
    print("- 'Hi, who are you?'")
    print("- 'What can you do?'")
    print("- 'Show me how much disk space I have'")
    print("- 'Make a simple Python hello world script'")
    print("\nType 'goodbye' to exit")

if __name__ == "__main__":
    setup_vanilla_agenticseek()
    
    # Ask if user wants to test
    response = input("\nDo you want to test CLI mode now? (y/n): ")
    if response.lower() == 'y':
        test_cli_mode()