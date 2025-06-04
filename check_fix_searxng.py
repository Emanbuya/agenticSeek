#!/usr/bin/env python3
"""
Check and fix searxng configuration for web search
"""

import os
import re

def check_searxng_config():
    """Check and fix searxng configuration"""
    print("🔍 Checking searxng configuration...")
    
    # Find searxSearch.py
    search_file = "sources/tools/searxSearch.py"
    
    if not os.path.exists(search_file):
        print(f"❌ {search_file} not found!")
        return False
    
    # Read the file
    with open(search_file, 'r') as f:
        content = f.read()
    
    # Look for the URL configuration
    print("\n📝 Current configuration:")
    
    # Find URL patterns
    url_patterns = [
        r'SEARXNG_URL\s*=\s*["\']([^"\']+)["\']',
        r'url\s*=\s*["\']([^"\']+)["\']',
        r'http://[^\s"\']+',
        r'localhost:\d+'
    ]
    
    found_urls = []
    for pattern in url_patterns:
        matches = re.findall(pattern, content)
        found_urls.extend(matches)
    
    print(f"Found URLs: {set(found_urls)}")
    
    # Check if it needs fixing
    needs_fix = False
    if 'localhost:8888' in content or ':8888' in content:
        print("❌ Found incorrect port 8888")
        needs_fix = True
    elif 'localhost:8080' in content or ':8080' in content:
        print("✅ Port 8080 is already configured")
    else:
        print("⚠️  No clear port configuration found")
        needs_fix = True
    
    if needs_fix:
        print("\n🔧 Fixing configuration...")
        
        # Replace 8888 with 8080
        new_content = content.replace('8888', '8080')
        
        # If no URL found, try to add one
        if 'SEARXNG_URL' not in content and 'localhost' not in content:
            # Look for where to add it
            if 'class SearxSearch' in content:
                # Add after class definition
                new_content = content.replace(
                    'class SearxSearch',
                    'SEARXNG_URL = "http://localhost:8080"\n\nclass SearxSearch'
                )
        
        # Write back
        with open(search_file, 'w') as f:
            f.write(new_content)
        
        print("✅ Configuration updated!")
        return True
    
    return False

def test_web_search():
    """Test if web search is working"""
    print("\n🧪 Testing web search...")
    
    try:
        import requests
        response = requests.get("http://localhost:8080", timeout=3)
        if response.status_code == 200:
            print("✅ Searxng is accessible!")
        else:
            print(f"⚠️  Searxng returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to searxng: {e}")
        print("\nMake sure Docker services are running:")
        print("  docker-compose up -d")

def main():
    print("🔧 Fixing Web Search for Nina")
    print("="*50)
    
    # Check and fix config
    check_searxng_config()
    
    # Test connection
    test_web_search()
    
    print("\n✅ Configuration checked!")
    print("\nNow try asking Nina about weather again:")
    print('  "What is the weather in San Marcos Texas?"')
    print("\nIf web search still doesn't work, try:")
    print("  1. Restart Docker: docker-compose restart")
    print("  2. Check logs: docker logs agentic_seek-searxng-1")

if __name__ == "__main__":
    main()