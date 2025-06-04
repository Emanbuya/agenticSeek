#!/usr/bin/env python3
"""
Nina Simple Integration - Direct usage of Agentic Seek
Just run Agentic Seek with Nina's identity
"""

import os
import sys
import subprocess
from pathlib import Path

def update_config_for_nina():
    """Update Agentic Seek config for Nina"""
    # Try both possible paths
    possible_paths = ["agentic_seek/config.ini", "Agentic_Seek/config.ini"]
    
    config_path = None
    for path in possible_paths:
        if Path(path).exists():
            config_path = Path(path)
            break
    
    if not config_path:
        print("❌ Could not find config.ini")
        return None
    
    print(f"✅ Found config at: {config_path}")
    
    # Read and update config
    import configparser
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Just change the agent name to Nina
    config['MAIN']['agent_name'] = 'Nina'
    
    # Save
    with open(config_path, 'w') as f:
        config.write(f)
    
    return config_path.parent

def run_agentic_seek_as_nina():
    """Run Agentic Seek with Nina configuration"""
    print("\n🚀 Running Agentic Seek as Nina")
    print("="*60)
    print("💡 This uses Agentic Seek's built-in voice features")
    print("   Just say 'Nina' instead of the default wake word")
    print("="*60 + "\n")
    
    # Find Agentic Seek directory
    agentic_dir = update_config_for_nina()
    
    if not agentic_dir:
        # Try to find it
        for possible in ["agentic_seek", "Agentic_Seek"]:
            if Path(possible).exists():
                agentic_dir = Path(possible)
                break
    
    if not agentic_dir:
        print("❌ Cannot find Agentic Seek directory")
        print("   Make sure you're running this from the right directory")
        return
    
    # Change to Agentic Seek directory
    original_dir = os.getcwd()
    os.chdir(agentic_dir)
    
    try:
        # Check if Ollama is running
        print("🔍 Checking requirements...")
        
        # Check Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            print("✅ Ollama is running")
        except:
            print("⚠️  Ollama might not be running")
            print("   Run 'ollama serve' in another terminal")
            input("\nPress Enter when ready...")
        
        # Run cli.py
        print("\n🎤 Starting Nina (Agentic Seek)...")
        print("   Say 'Nina' to activate\n")
        
        subprocess.run([sys.executable, "cli.py"])
        
    except KeyboardInterrupt:
        print("\n\n👋 Nina shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        # Try running with more details
        print("\nTrying with error output...")
        subprocess.run([sys.executable, "cli.py", "--verbose"])
    finally:
        os.chdir(original_dir)

def check_and_install_requirements():
    """Check and offer to install requirements"""
    print("📋 Checking requirements...")
    
    # Find requirements.txt
    req_paths = ["agentic_seek/requirements.txt", "Agentic_Seek/requirements.txt"]
    req_file = None
    
    for path in req_paths:
        if Path(path).exists():
            req_file = path
            break
    
    if req_file:
        print(f"✅ Found requirements.txt at: {req_file}")
        response = input("\nInstall/update requirements? (y/n): ")
        if response.lower() == 'y':
            print("\n📦 Installing re