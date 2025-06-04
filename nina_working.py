#!/usr/bin/env python3
"""
Find and start the AgenticSeek Web UI
"""

import os
import subprocess
import sys

def find_web_ui():
    """Find the AgenticSeek web UI files"""
    print("🔍 Searching for AgenticSeek Web UI...")
    print("="*50)
    
    # Common UI file patterns
    ui_patterns = [
        "app.py",
        "web_ui.py", 
        "interface.py",
        "server.py",
        "main.py",
        "ui.py",
        "web_app.py",
        "flask_app.py",
        "streamlit_app.py"
    ]
    
    # Search in common directories
    search_dirs = [".", "web_ui", "ui", "interface", "web", "app"]
    
    found_files = []
    
    for directory in search_dirs:
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file in ui_patterns or "ui" in file.lower() or "app" in file.lower():
                    full_path = os.path.join(directory, file)
                    if os.path.isfile(full_path) and full_path.endswith('.py'):
                        found_files.append(full_path)
    
    if found_files:
        print("\n✅ Found potential web UI files:")
        for i, file in enumerate(found_files):
            print(f"{i+1}. {file}")
            
            # Check file content for Flask/Streamlit/etc
            with open(file, 'r') as f:
                content = f.read(1000)  # Read first 1000 chars
                if 'flask' in content.lower():
                    print("   └─ Flask app detected")
                elif 'streamlit' in content.lower():
                    print("   └─ Streamlit app detected")
                elif 'gradio' in content.lower():
                    print("   └─ Gradio app detected")
                elif 'fastapi' in content.lower():
                    print("   └─ FastAPI app detected")
        
        print("\n💡 To start the web UI, run:")
        print(f"   python {found_files[0]}")
        
        # Also check for package.json (might be a React/Node UI)
        if os.path.exists("package.json"):
            print("\n📦 Found package.json - might be a Node.js UI")
            print("   Try: npm install && npm start")
            
    else:
        print("\n❌ No web UI files found in the current structure")
        print("\n📝 AgenticSeek might use:")
        print("   - CLI interface (cli.py)")
        print("   - Or the web UI might be in a different location")
        
        # Check if it's using the CLI with a web wrapper
        if os.path.exists("cli.py"):
            print("\n💡 Found cli.py - AgenticSeek uses CLI interface")
            print("   You can:")
            print("   1. Run: python cli.py")
            print("   2. Or create a web UI wrapper with: python setup_nina_web_ui.py")

if __name__ == "__main__":
    find_web_ui()