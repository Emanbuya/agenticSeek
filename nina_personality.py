#!/usr/bin/env python3
"""
Configure Nina's personality for AgenticSeek
"""

import configparser
import os

def create_nina_personality():
    """Create Nina's personality configuration"""
    
    # Nina's system prompt
    nina_prompt = """You are Nina, a friendly and helpful AI assistant. 

Your personality traits:
- Warm, approachable, and conversational
- Direct and concise - avoid overly verbose explanations
- Professional yet personable
- Proactive in offering helpful suggestions
- Tech-savvy and knowledgeable

Communication style:
- Use natural, conversational language
- Keep responses focused and to-the-point
- When explaining technical concepts, use clear examples
- Acknowledge when you don't know something
- End complex responses with "Is there anything else I can help you with?"

Special capabilities:
- Web searching for current information
- File management and code generation
- System operations and automation
- Research and analysis

Remember: You're Nina, not Jarvis. Always introduce yourself as Nina if asked."""

    # Create personality file
    with open('nina_personality.txt', 'w') as f:
        f.write(nina_prompt)
    
    print("✅ Created nina_personality.txt")
    
    # Update config for Nina
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Update settings
    config['MAIN']['agent_name'] = 'Nina'
    config['MAIN']['provider_model'] = 'deepseek-v2:16b'
    config['MAIN']['jarvis_personality'] = 'False'  # Use custom personality
    
    # Save updated config
    with open('config_nina.ini', 'w') as f:
        config.write(f)
    
    print("✅ Created config_nina.ini")
    
    # Create a launcher script
    launcher_content = """#!/usr/bin/env python3
import subprocess
import sys

print("🤖 Starting Nina AI Assistant...")
print("="*50)

# Start CLI with Nina config
subprocess.run([sys.executable, 'cli.py'])
"""
    
    with open('start_nina.py', 'w') as f:
        f.write(launcher_content)
    
    print("✅ Created start_nina.py launcher")
    
    print("\n🎉 Nina configuration complete!")
    print("\nTo run Nina:")
    print("  python start_nina.py")
    print("\nOr manually:")
    print("  python cli.py --config config_nina.ini")

def enhance_nina_responses():
    """Additional enhancements for better responses"""
    
    print("\n💡 Tips for better Nina responses:")
    print("1. Consider using a quantized model for faster responses:")
    print("   ollama pull deepseek-v2:16b-q4_K_M")
    print("\n2. Adjust temperature in Ollama for more consistent output:")
    print("   Edit modelfile: temperature 0.7")
    print("\n3. For coding tasks, also consider:")
    print("   ollama pull deepseek-coder:15b")

if __name__ == "__main__":
    create_nina_personality()
    enhance_nina_responses()