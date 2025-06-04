#!/usr/bin/env python3
"""
Script to update Ollama model across all configuration files
"""

import configparser
import os
import fileinput
import sys

# The new model you want to use
NEW_MODEL = "mistral:7b-instruct-q4_K_M"

print(f"Updating all configurations to use: {NEW_MODEL}")
print("-" * 50)

# 1. Update config.ini
try:
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    old_model = config.get('MAIN', 'provider_model', fallback='unknown')
    print(f"Current model in config.ini: {old_model}")
    
    config['MAIN']['provider_model'] = NEW_MODEL
    
    with open('config.ini', 'w') as f:
        config.write(f)
    
    print(f"✓ Updated config.ini: provider_model = {NEW_MODEL}")
except Exception as e:
    print(f"✗ Error updating config.ini: {e}")

# 2. Update llm_router.py
try:
    llm_router_updated = False
    
    # Read the file
    with open('llm_router.py', 'r') as f:
        lines = f.readlines()
    
    # Update the OLLAMA_MODEL line
    with open('llm_router.py', 'w') as f:
        for line in lines:
            if line.strip().startswith('OLLAMA_MODEL ='):
                f.write(f'OLLAMA_MODEL = "{NEW_MODEL}"\n')
                llm_router_updated = True
                print(f"✓ Updated llm_router.py: OLLAMA_MODEL = {NEW_MODEL}")
            else:
                f.write(line)
    
    if not llm_router_updated:
        print("⚠ OLLAMA_MODEL line not found in llm_router.py")
except Exception as e:
    print(f"✗ Error updating llm_router.py: {e}")

# 3. Set environment variable (for current session)
os.environ['OLLAMA_MODEL'] = NEW_MODEL
print(f"✓ Set environment variable: OLLAMA_MODEL={NEW_MODEL}")

# 4. Create a batch file to set environment permanently (Windows)
try:
    with open('set_model_env.bat', 'w') as f:
        f.write(f'@echo off\n')
        f.write(f'setx OLLAMA_MODEL "{NEW_MODEL}"\n')
        f.write(f'echo Environment variable OLLAMA_MODEL set to {NEW_MODEL}\n')
        f.write(f'pause\n')
    print("✓ Created set_model_env.bat - run this to set environment variable permanently")
except:
    pass

print("\n" + "="*50)
print("Model update complete!")
print("\nNext steps:")
print("1. Make sure Ollama has the model:")
print(f"   ollama pull {NEW_MODEL}")
print("\n2. Restart Ollama with GPU support:")
print("   set OLLAMA_NUM_GPU=999")
print("   ollama serve")
print("\n3. Restart api.py")
print("\n4. (Optional) Run set_model_env.bat to set environment variable permanently")