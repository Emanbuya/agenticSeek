# test_nina_voice.py
"""
Quick test script for Nina's voice
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sources.nina_jarvis_voice import Speech

# Test Nina's voice
print("Testing Nina's voice system...")

# Create speech instance
nina = Speech(enable=True, language="en", voice_idx=1)

# Test different phrases
test_phrases = [
    "Hello, this is Nina testing the voice system.",
    "Activating web search mode.",
    "I found 5 files matching your search.",
    "Processing your request...",
    "Task completed successfully!"
]

for phrase in test_phrases:
    print(f"\nTesting: {phrase}")
    nina.speak(phrase)
    
    # Wait a bit between phrases
    import time
    time.sleep(2)

print("\nVoice test complete!")