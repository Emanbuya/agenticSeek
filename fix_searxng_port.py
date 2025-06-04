#!/usr/bin/env python3
"""
Fix searxng port configuration
"""

import os
import fileinput
import sys

def fix_searxng_port():
    """Update searxng port from 8888 to 8080"""
    print("🔧 Fixing searxng port configuration...")
    
    # Find searxSearch.py
    search_file = "sources/tools/searxSearch.py"
    
    if not os.path.exists(search_file):
        print(f"❌ {search_file} not found!")
        return False
    
    # Read the file
    with open(search_file, 'r') as f:
        content = f.read()
    
    # Check current configuration
    if '8888' in content:
        print("✅ Found port 8888 in configuration")
        
        # Replace port
        new_content = content.replace(':8888', ':8080')
        new_content = new_content.replace('localhost:8888', 'localhost:8080')
        
        # Write back
        with open(search_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Updated searxng port to 8080")
        return True
    
    elif '8080' in content:
        print("✅ Port is already set to 8080")
        return True
    
    else:
        print("⚠️  Could not find port configuration")
        print("Looking for SEARXNG_URL...")
        
        # Try to find the URL configuration
        if 'SEARXNG_URL' in content or 'searxng_url' in content:
            print("Found SEARXNG_URL variable")
            # Look for the actual URL
            import re
            urls = re.findall(r'http://[^\s"\']+', content)
            print(f"Found URLs: {urls}")
        
        return False

def test_searxng():
    """Test if searxng is now accessible"""
    import requests
    
    print("\n🔍 Testing searxng on port 8080...")
    
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Searxng is accessible at http://localhost:8080")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def main():
    print("🔧 Fixing Searxng Port Configuration")
    print("="*50)
    
    # Fix the port
    if fix_searxng_port():
        # Test it
        if test_searxng():
            print("\n✅ Searxng is now properly configured!")
            print("\nYou can now use web search in AgenticSeek:")
            print("  python cli.py")
            print("\nTry: search the web for current weather in New York")
        else:
            print("\n⚠️  Searxng is running but may need additional configuration")
    else:
        print("\n❌ Could not fix configuration automatically")
        print("\nManual fix:")
        print("1. Open sources/tools/searxSearch.py")
        print("2. Find the URL configuration")
        print("3. Change port from 8888 to 8080")

if __name__ == "__main__":
    main()