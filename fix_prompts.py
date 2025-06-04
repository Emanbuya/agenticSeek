#!/usr/bin/env python3
"""
Fix missing prompts for Agentic Seek
"""

import os
import shutil

def check_prompts():
    """Check what prompts exist"""
    print("📁 Checking prompts directory...")
    
    if os.path.exists('prompts'):
        print("✅ prompts/ directory exists")
        
        # List subdirectories
        for item in os.listdir('prompts'):
            path = os.path.join('prompts', item)
            if os.path.isdir(path):
                print(f"   📂 {item}/")
                # List files in subdirectory
                for file in os.listdir(path):
                    print(f"      📄 {file}")
    else:
        print("❌ prompts/ directory not found!")
        os.makedirs('prompts')
        print("✅ Created prompts/ directory")

def create_base_prompts():
    """Create the base prompts that Agentic Seek needs"""
    print("\n📝 Creating base prompts...")
    
    # Create base directory
    os.makedirs('prompts/base', exist_ok=True)
    
    # Casual Agent prompt
    casual_prompt = """You are a helpful AI assistant with computer control capabilities.

You can:
- Control the browser and navigate websites
- Create and manage files
- Execute code
- Answer questions

Always be helpful and explain what you're doing."""
    
    # Coder Agent prompt  
    coder_prompt = """You are a skilled programmer who can write and execute code.

When asked to code:
- Write clean, commented code
- Test the code before presenting it
- Explain your approach
- Handle errors gracefully"""
    
    # File Agent prompt
    file_prompt = """You are a file management specialist.

You can:
- Create, read, update, and delete files
- Navigate directories
- Search for files
- Manage file permissions

Always confirm destructive operations."""
    
    # Browser Agent prompt
    browser_prompt = """You are a web browser automation expert.

You can:
- Navigate to websites
- Click on elements
- Fill forms
- Extract information
- Take screenshots

Be careful with sensitive information."""
    
    # Planner Agent prompt
    planner_prompt = """You are a planning and coordination specialist.

Your role:
- Break down complex tasks
- Coordinate between agents
- Create step-by-step plans
- Monitor progress

Think step by step."""
    
    # Write all prompts
    prompts = {
        'casual_agent.txt': casual_prompt,
        'coder_agent.txt': coder_prompt,
        'file_agent.txt': file_prompt,
        'browser_agent.txt': browser_prompt,
        'planner_agent.txt': planner_prompt
    }
    
    for filename, content in prompts.items():
        path = f'prompts/base/{filename}'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created {path}")

def create_nina_prompts():
    """Create Nina personality prompts"""
    print("\n👤 Creating Nina personality...")
    
    # Create nina directory
    os.makedirs('prompts/nina', exist_ok=True)
    
    # Copy base prompts first
    if os.path.exists('prompts/base'):
        for file in os.listdir('prompts/base'):
            if file.endswith('.txt'):
                shutil.copy(f'prompts/base/{file}', f'prompts/nina/{file}')
    
    # Override casual agent with Nina's personality
    nina_casual = """You are Nina, a friendly and efficient AI assistant with computer control capabilities.

Personality:
- Warm, friendly, and approachable
- Professional but personable  
- Clear and concise communication
- Proactive and helpful

Capabilities:
- Control the browser and navigate websites
- Create and manage files
- Execute code
- Answer questions
- Take screenshots

When responding:
- Be conversational but efficient
- Explain what you're doing in simple terms
- Offer alternatives if something doesn't work
- Keep responses brief but complete

Remember: You're Nina, not just any AI. Be helpful and friendly!"""
    
    with open('prompts/nina/casual_agent.txt', 'w', encoding='utf-8') as f:
        f.write(nina_casual)
    
    print("✅ Nina personality created!")

def update_config_for_prompts():
    """Update config to use correct prompt folder"""
    import configparser
    
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Check if nina prompts exist, otherwise use base
    if os.path.exists('prompts/nina/casual_agent.txt'):
        print("\n🔧 Setting config to use Nina prompts...")
        # This is a bit of a hack, but it works
        config['MAIN']['jarvis_personality'] = 'False'
    else:
        print("\n🔧 Setting config to use base prompts...")
        config['MAIN']['jarvis_personality'] = 'False'
    
    with open('config.ini', 'w') as f:
        config.write(f)

def main():
    print("🔧 Fixing Agentic Seek Prompts")
    print("="*50 + "\n")
    
    # Check current state
    check_prompts()
    
    # Create base prompts
    create_base_prompts()
    
    # Create Nina prompts
    create_nina_prompts()
    
    # Update config
    update_config_for_prompts()
    
    print("\n✅ All prompts created!")
    print("\n🚀 You can now run:")
    print("   python cli.py")
    print("   or")
    print("   python nina_text.py")

if __name__ == "__main__":
    main()