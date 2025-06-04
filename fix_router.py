#!/usr/bin/env python3
"""
Fix the LLMRouterWrapper issue in router.py
"""

import os
import shutil

def fix_router():
    """Fix the predict method issue in router.py"""
    print("🔧 Fixing router.py...")
    
    router_path = "sources/router.py"
    
    if not os.path.exists(router_path):
        print("❌ router.py not found!")
        return False
    
    # Backup original
    shutil.copy(router_path, router_path + ".backup")
    print("✅ Backed up original router.py")
    
    # Read the file
    with open(router_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the LLMRouterWrapper class
    fix = """
            class LLMRouterWrapper:
                def classify(self, text):
                    prompt = f"Classify this text into one of these categories: code, web, files, talk, mcp. Text: '{text}'. Return only the category name."
                    return llm_router.query_llama3(prompt)
                
                def predict(self, text):
                    # Predict method for compatibility
                    result = self.classify(text)
                    # Parse the result to extract category
                    category = result.lower().strip()
                    
                    # Default predictions if parsing fails
                    if "code" in category:
                        return [("code", 0.8), ("files", 0.1), ("talk", 0.1)]
                    elif "web" in category:
                        return [("web", 0.8), ("talk", 0.1), ("files", 0.1)]
                    elif "files" in category:
                        return [("files", 0.8), ("code", 0.1), ("talk", 0.1)]
                    elif "mcp" in category:
                        return [("mcp", 0.8), ("web", 0.1), ("talk", 0.1)]
                    else:
                        return [("talk", 0.8), ("web", 0.1), ("files", 0.1)]
                
                def add_examples(self, texts, labels):
                    # Dummy method for compatibility
                    pass
"""
    
    # Replace the LLMRouterWrapper class
    if "class LLMRouterWrapper:" in content:
        # Find the class and replace it
        import re
        pattern = r'class LLMRouterWrapper:.*?return LLMRouterWrapper\(\)'
        replacement = fix + '\n            return LLMRouterWrapper()'
        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write back
        with open(router_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Fixed router.py!")
        return True
    else:
        print("⚠️  LLMRouterWrapper class not found in expected format")
        return False

def create_simple_router():
    """Create a simple router that works"""
    print("\n📝 Creating simple router...")
    
    simple_router = '''#!/usr/bin/env python3
"""
Simple router for Agentic Seek - bypasses complex routing
"""

import random
from sources.agents.agent import Agent

class SimpleRouter:
    def __init__(self, agents):
        self.agents = agents
        self.casual_agent = None
        
        # Find casual agent
        for agent in agents:
            if agent.type == "casual_agent":
                self.casual_agent = agent
                break
                
    def select_agent(self, text):
        """Simple selection - just use casual agent for most things"""
        text_lower = text.lower()
        
        # Simple keyword matching
        if any(word in text_lower for word in ['browse', 'search', 'google', 'web', 'find online']):
            for agent in self.agents:
                if agent.type == "browser_agent":
                    return agent
                    
        if any(word in text_lower for word in ['code', 'script', 'program', 'function', 'debug']):
            for agent in self.agents:
                if agent.type == "code_agent":
                    return agent
                    
        if any(word in text_lower for word in ['file', 'folder', 'directory', 'find', 'locate']):
            for agent in self.agents:
                if agent.type == "file_agent":
                    return agent
        
        # Default to casual agent
        return self.casual_agent

# Monkey patch the import
import sys
sys.modules['sources.router'] = sys.modules[__name__]
AgentRouter = SimpleRouter
'''
    
    with open('simple_router.py', 'w') as f:
        f.write(simple_router)
    
    print("✅ Created simple_router.py")

def main():
    print("🔧 Router Fix Utility")
    print("="*50)
    
    # Try to fix the existing router
    if fix_router():
        print("\n✅ Router fixed! Try running Nina again.")
    else:
        print("\n⚠️  Could not fix router automatically.")
    
    # Create simple router as backup
    create_simple_router()
    
    print("\n💡 If issues persist, you can:")
    print("   1. Run: python nina_working.py")
    print("   2. Or manually edit sources/router.py")

if __name__ == "__main__":
    main()