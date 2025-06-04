#!/usr/bin/env python3
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
