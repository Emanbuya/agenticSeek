#!/usr/bin/env python3
"""
Most basic test - no imports, just prints
"""

print("Test 1: Basic print works")

import os
print(f"Test 2: Current directory: {os.getcwd()}")
print(f"Test 3: Directory contents: {os.listdir('.')}")

# Check if agentic_seek exists
if os.path.exists('agentic_seek'):
    print("Test 4: Found agentic_seek directory")
else:
    print("Test 4: agentic_seek directory NOT found")

print("Test 5: Script completed successfully")