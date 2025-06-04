import os
import platform
import subprocess
import torch

def print_header(title):
    print(f"{'='*48}")
    print(f"{title}")
    print(f"{'='*48}")

def check_pytorch():
    print_header("🎮 Checking GPU setup...")
    print(f"✅ PyTorch version: {torch.__version__}")
    cuda_available = torch.cuda.is_available()
    print(f"✅ CUDA available: {cuda_available}")
    if not cuda_available:
        print("❌ CUDA not available to PyTorch")

def check_ollama_gpu():
    print()
    print_header("🦙 Checking Ollama GPU support...")
    try:
        output = subprocess.check_output(['ollama', 'run', '--help'], stderr=subprocess.STDOUT, text=True)
        if 'gpu' in output.lower():
            print("✅ Ollama GPU support appears available")
        else:
            print("⚠️  Model may not be configured for GPU")
    except Exception as e:
        print(f"⚠️  Ollama check failed: {e}")

def configure_for_gpu():
    print()
    print_header("🔧 Configuring for GPU usage...")
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['OLLAMA_GPU_LAYERS'] = '999'
    os.environ['OLLAMA_NUM_GPU'] = '1'
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    print("✅ Environment variables set")

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

print("Launching with GPU optimization...")
print(f"   GPU layers: {os.environ.get('OLLAMA_GPU_LAYERS', 'default')}")

# Import and run cli
import cli
import asyncio
asyncio.run(cli.main())
"""

    with open("run_gpu.py", "w", encoding="utf-8") as f:
        f.write(gpu_script)

    print("✅ GPU launch script written to run_gpu.py")

def main():
    print_header("🎮 GPU Configuration for Agentic Seek")
    print(f"System: {get_gpu_info()}")
    check_pytorch()
    check_ollama_gpu()
    configure_for_gpu()

def get_gpu_info():
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            return f"{gpus[0].name} with {gpus[0].memoryTotal}MB VRAM"
        return "GPU not detected"
    except:
        return "GPU info unavailable (install GPUtil?)"

if __name__ == "__main__":
    main()
