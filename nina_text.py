#!/usr/bin/env python3
"""
Nina Text Mode - Test without voice complications
"""

import os
import sys
import configparser
import subprocess

def setup_nina_text_mode():
    """Configure Nina for text-only mode"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Nina configuration
    config['MAIN']['agent_name'] = 'Nina'
    config['MAIN']['speak'] = 'False'  # No TTS for now
    config['MAIN']['listen'] = 'False'  # No STT for now
    config['MAIN']['provider_model'] = 'phi3:mini'
    
    # GPU settings
    config['MAIN']['provider_server_address'] = '127.0.0.1:11434'
    
    with open('config.ini', 'w') as f:
        config.write(f)
    
    print("✅ Nina configured for text mode")

def main():
    print("🎯 Nina - Text Mode (Testing)")
    print("="*50)
    
    if not os.path.exists('cli.py'):
        print("❌ Run from agentic_seek directory!")
        return
    
    setup_nina_text_mode()
    
    # Set GPU vars
    os.environ['OLLAMA_GPU_LAYERS'] = '999'
    
    print("\n💬 Type your commands (Nina is ready):")
    print("="*50 + "\n")
    
    subprocess.run([sys.executable, 'cli.py'])

if __name__ == "__main__":
    main()