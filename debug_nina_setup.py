#!/usr/bin/env python3
"""
Setup Nina with AgenticSeek Web UI
"""

import os
import subprocess
import sys
import configparser

def setup_nina():
    """Setup Nina with AgenticSeek's existing web UI"""
    print("🎤 Setting up Nina with AgenticSeek Web UI")
    print("="*50)
    
    # 1. Update config.ini for Nina
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Update main settings
    config['MAIN']['agent_name'] = 'Nina'
    config['MAIN']['provider_model'] = 'phi3:mini'  # Change to deepseek-r1:14b for better performance
    
    # Create workspace for Nina
    nina_workspace = os.path.join(os.getcwd(), 'nina_workspace')
    os.makedirs(nina_workspace, exist_ok=True)
    config['MAIN']['work_dir'] = nina_workspace
    
    # Save updated config
    with open('config.ini', 'w') as f:
        config.write(f)
    
    print("✅ Updated config.ini for Nina")
    
    # 2. Check if services are running
    print("\n📦 Checking services...")
    
    # 3. Start the services if not running
    if sys.platform.startswith('win'):
        print("💡 On Windows, run: start start_services.cmd")
    else:
        print("💡 Starting services...")
        subprocess.run(['sudo', './start_services.sh'], check=False)
    
    print("\n🚀 To run Nina with Web UI:")
    print("1. Make sure Ollama is running: ollama serve")
    print("2. Start the backend: python3 api.py")
    print("3. Open your browser to: http://localhost:3000")
    print("\n✨ Nina will be available in the web interface!")

def create_nina_launcher():
    """Create a launcher script for Nina"""
    launcher = """#!/usr/bin/env python3
import subprocess
import webbrowser
import time
import os

print("🎤 Starting Nina AI Assistant...")
print("="*50)

# Set environment
os.environ['OLLAMA_GPU_LAYERS'] = '999'

# Start backend
print("Starting backend...")
backend = subprocess.Popen(['python3', 'api.py'])

# Wait for backend to start
time.sleep(3)

# Open browser
print("Opening web interface...")
webbrowser.open('http://localhost:3000')

print("\\n✅ Nina is running at http://localhost:3000")
print("Press Ctrl+C to stop")

try:
    backend.wait()
except KeyboardInterrupt:
    print("\\nShutting down Nina...")
    backend.terminate()
"""
    
    with open('start_nina.py', 'w', encoding='utf-8') as f:
        f.write(launcher)
    
    os.chmod('start_nina.py', 0o755)
    print("✅ Created start_nina.py launcher")

if __name__ == "__main__":
    setup_nina()
    create_nina_launcher()
    
    print("\n🎉 Nina setup complete!")
    print("\n📝 Quick start:")
    print("   python3 start_nina.py")
    print("\nThis will start the backend and open the web UI automatically.")