#!/usr/bin/env python3
"""
Enable web search functionality for Nina
"""

import os
import json

def check_tools_config():
    """Check if web search tool is enabled"""
    print("🔍 Checking tool configuration...")
    
    # Check if searxSearch.py exists
    tool_path = "sources/tools/searxSearch.py"
    if os.path.exists(tool_path):
        print(f"✅ Found {tool_path}")
    else:
        print(f"❌ Missing {tool_path}")
        return False
    
    # Check tools.json configuration
    tools_json = "tools.json"
    if os.path.exists(tools_json):
        print(f"\n📝 Checking {tools_json}...")
        with open(tools_json, 'r') as f:
            tools = json.load(f)
        
        # Look for searx tool
        searx_found = False
        for tool in tools:
            if 'searx' in tool.get('name', '').lower() or 'search' in tool.get('name', '').lower():
                print(f"✅ Found search tool: {tool.get('name')}")
                print(f"   Enabled: {tool.get('enabled', False)}")
                searx_found = True
        
        if not searx_found:
            print("❌ No search tool found in tools.json")
    else:
        print(f"❌ {tools_json} not found")
    
    # Check agent configs
    print("\n📁 Checking agent configurations...")
    agents_dir = "sources/agents"
    if os.path.exists(agents_dir):
        for filename in os.listdir(agents_dir):
            if filename.endswith('.yaml'):
                filepath = os.path.join(agents_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                if 'searx' in content.lower() or 'search' in content.lower():
                    print(f"✅ {filename} has search capability")
    
    return True

def fix_web_search():
    """Fix web search configuration"""
    print("\n🔧 Attempting to fix web search...")
    
    # Update main agent config to include search
    nina_agent = "sources/agents/Nina.yaml"
    
    if os.path.exists(nina_agent):
        print(f"✅ Found {nina_agent}")
        
        with open(nina_agent, 'r') as f:
            content = f.read()
        
        # Check if search is already in tools
        if 'searxSearch' not in content:
            print("⚠️  searxSearch not in Nina's tools")
            print("📝 Adding search capability...")
            
            # Add searxSearch to tools list
            if 'tools:' in content:
                # Find tools section and add searxSearch
                lines = content.split('\n')
                new_lines = []
                in_tools = False
                
                for line in lines:
                    new_lines.append(line)
                    if 'tools:' in line:
                        in_tools = True
                    elif in_tools and line.strip() and not line.startswith(' '):
                        # End of tools section, add searxSearch before
                        new_lines.insert(-1, '  - searxSearch')
                        in_tools = False
                
                content = '\n'.join(new_lines)
            else:
                # No tools section, add one
                content += '\ntools:\n  - searxSearch\n'
            
            # Save updated config
            with open(nina_agent, 'w') as f:
                f.write(content)
            
            print("✅ Added searxSearch to Nina's capabilities")
    else:
        print(f"❌ {nina_agent} not found")
        print("Creating basic Nina agent config...")
        
        nina_config = """name: Nina
description: Friendly AI assistant with web search capabilities
instructions: |
  You are Nina, a helpful AI assistant.
  When asked about current information like weather, news, or real-time data,
  use the web search tool to find accurate, up-to-date information.
  Be concise and friendly in your responses.
tools:
  - searxSearch
  - codeInterpreter
  - webBrowser
"""
        
        os.makedirs("sources/agents", exist_ok=True)
        with open(nina_agent, 'w') as f:
            f.write(nina_config)
        
        print("✅ Created Nina agent configuration")

def verify_docker():
    """Verify Docker services are running"""
    print("\n🐳 Verifying Docker services...")
    
    import subprocess
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if 'searxng' in result.stdout:
            print("✅ Searxng container is running")
        else:
            print("❌ Searxng container not found")
            print("Run: start_services.cmd")
    except:
        print("❌ Docker not accessible")

def main():
    print("🔧 Enabling Web Search for Nina")
    print("="*50)
    
    # Check current configuration
    check_tools_config()
    
    # Fix configuration
    fix_web_search()
    
    # Verify Docker
    verify_docker()
    
    print("\n✅ Configuration updated!")
    print("\n⚠️  IMPORTANT: Restart Nina for changes to take effect:")
    print("1. Press Ctrl+C in the CLI terminal")
    print("2. Restart: python cli.py")
    print("\nThen try asking about weather again!")

if __name__ == "__main__":
    main()