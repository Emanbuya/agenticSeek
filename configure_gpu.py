#!/usr/bin/env python3
"""
Configure Agentic Seek to use GPU (RTX 4060 Ti)
"""

import subprocess
import sys
import os

def check_gpu():
    """Check GPU availability"""
    print("🎮 Checking GPU setup...")
    
    # Check CUDA
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        print(f"✅ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"✅ CUDA version: {torch.version.cuda}")
        else:
            print("❌ CUDA not available to PyTorch")
    except ImportError:
        print("❌ PyTorch not installed")
    
    # Check Ollama GPU support
    print("\n🦙 Checking Ollama GPU support...")
    try:
        result = subprocess.run(["ollama", "show", "--modelfile", "phi3:mini"], 
                              capture_output=True, text=True)
        if "GPU" in result.stdout:
            print("✅ Ollama model supports GPU")
        else:
            print("⚠️  Model may not be configured for GPU")
    except:
        print("⚠️  Could not check Ollama model")

def configure_for_gpu():
    """Configure system for GPU usage"""
    print("\n🔧 Configuring for GPU usage...")
    
    # Set environment variables
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['OLLAMA_GPU_LAYERS'] = '999'  # Use all GPU layers
    
    print("✅ Environment variables set")
    
    # Create GPU-optimized launch script
    gpu_script = """#!/usr/bin/env python3
'''GPU-optimized launcher for Agentic Seek'''
import os
import sys

# Force GPU usage
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['OLLAMA_GPU_LAYERS'] = '999'
os.environ['OLLAMA_NUM_GPU'] = '1'

# For whisper
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

print("🚀 Launching with GPU optimization...")
print(f"   GPU layers: {os.environ.get('OLLAMA_GPU_LAYERS', 'default')}")

# Import and run cli
import cli
import asyncio
asyncio.run(cli.main())
"""
    
    with open('run_gpu.py', 'w') as f:
        f.write(gpu_script)
    
    print("✅ Created run_gpu.py")
    
    # Create batch file for Windows
    batch_script = """@echo off
echo 🎮 Starting Agentic Seek with GPU...
set CUDA_VISIBLE_DEVICES=0
set OLLAMA_GPU_LAYERS=999
set OLLAMA_NUM_GPU=1
python cli.py
pause
"""
    
    with open('run_gpu.bat', 'w') as f:
        f.write(batch_script)
    
    print("✅ Created run_gpu.bat")

def install_gpu_packages():
    """Install GPU-optimized packages"""
    print("\n📦 GPU Package Installation")
    print("="*50)
    
    response = input("Install GPU-optimized packages? (y/n): ")
    if response.lower() != 'y':
        return
    
    packages = [
        # PyTorch with CUDA
        "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
        # Other GPU packages
        "accelerate",
        "bitsandbytes"
    ]
    
    for package in packages:
        print(f"\n📦 Installing: {package}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + package.split())

def main():
    print("🎮 GPU Configuration for Agentic Seek")
    print("="*50)
    print(f"System: RTX 4060 Ti with 8GB VRAM")
    print("="*50 + "\n")
    
    # Check current GPU setup
    check_gpu()
    
    # Configure for GPU
    configure_for_gpu()
    
    # Offer to install packages
    install_gpu_packages()
    
    print("\n✅ Configuration complete!")
    print("\n🚀 To run with GPU, use one of these:")
    print("   - python run_gpu.py")
    print("   - run_gpu.bat (double-click)")
    print("   - Set OLLAMA_GPU_LAYERS=999 before running")
    
    print("\n💡 For Ollama models to use GPU:")
    print("   1. Pull model with GPU support: ollama pull phi3:mini")
    print("   2. Or create GPU version: ollama create phi3-gpu -f Modelfile")

if __name__ == "__main__":
    main()