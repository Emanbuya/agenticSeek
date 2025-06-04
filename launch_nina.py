#!/usr/bin/env python3
"""
Launch Nina with agentic seek
Simple launcher that ensures everything is set up correctly
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    issues = []
    
    # Check Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            issues.append("❌ Ollama is not responding properly")
    except:
        issues.append("❌ Ollama is not running. Start it with: ollama serve")
    
    # Check Agentic Seek directory
    if not Path("agentic_seek").exists():
        issues.append("❌ agentic_seek directory not found")
    
    # Check Python packages
    required_packages = [
        "whisper", "edge-tts", "pygame", "sounddevice", 
        "soundfile", "configparser", "fastapi"
    ]
    
    for pkg in required_packages:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            issues.append(f"❌ Missing package: {pkg}")
    
    return issues

def setup_nina_config():
    """Update agentic seek config for Nina"""
    config_path = Path("agentic_seek/config.ini")
    
    if not config_path.exists():
        print("❌ agentic_seek/config.ini not found!")
        return False
    
    # Read current config
    import configparser
    config = configparser.ConfigParser()
    config.read(config_path)
    
    # Update for Nina
    config['MAIN']['agent_name'] = 'Nina'
    config['MAIN']['provider_model'] = 'phi3:mini'  # Faster model
    config['MAIN']['speak'] = 'False'  # We use Nina's TTS
    config['MAIN']['listen'] = 'False'  # We use Nina's STT
    
    # Save updated config
    with open(config_path, 'w') as f:
        config.write(f)
    
    print("✅ Updated agentic seek config for Nina")
    return True

def main():
    print("🚀 Nina + agentic seek Launcher")
    print("="*40)
    
    # Check requirements
    print("\n📋 Checking requirements...")
    issues = check_requirements()
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  {issue}")
        print("\nPlease fix these issues and try again.")
        sys.exit(1)
    
    print("✅ All requirements met!")
    
    # Setup config
    print("\n🔧 Setting up configuration...")
    if not setup_nina_config():
        sys.exit(1)
    
    # Launch Nina
    print("\n🎤 Launching Nina...")
    print("="*40)
    
    try:
        # Run the integration
        subprocess.run([sys.executable, "nina_agentic_integration.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Nina shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()