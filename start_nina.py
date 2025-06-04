#!/usr/bin/env python3
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

print("\n✅ Nina is running at http://localhost:3000")
print("Press Ctrl+C to stop")

try:
    backend.wait()
except KeyboardInterrupt:
    print("\nShutting down Nina...")
    backend.terminate()
