#!/usr/bin/env python3
"""
Check all AgenticSeek services are running correctly
"""

import subprocess
import requests
import time
import sys

def check_docker_containers():
    """Check which containers are running"""
    print("🐳 Checking Docker containers...")
    
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                              capture_output=True, text=True)
        print(result.stdout)
        
        # Check for specific containers
        containers = result.stdout.lower()
        
        services = {
            'searxng': 'searxng' in containers,
            'redis': 'redis' in containers,
            'frontend': 'frontend' in containers
        }
        
        for service, running in services.items():
            if running:
                print(f"✅ {service} is running")
            else:
                print(f"❌ {service} is NOT running")
                
        return all(services.values())
        
    except Exception as e:
        print(f"❌ Error checking containers: {e}")
        return False

def test_services():
    """Test if services are accessible"""
    print("\n🔍 Testing service endpoints...")
    
    services = [
        ("Searxng", "http://localhost:8888", "search engine"),
        ("Frontend", "http://localhost:3000", "web UI"),
        ("Redis", "localhost:6379", "cache")
    ]
    
    for name, url, desc in services:
        if name == "Redis":
            # Redis needs special check
            try:
                result = subprocess.run(['docker', 'exec', 'agentic_seek-redis-1', 'redis-cli', 'ping'], 
                                      capture_output=True, text=True)
                if 'PONG' in result.stdout:
                    print(f"✅ {name} ({desc}) is responding")
                else:
                    print(f"❌ {name} ({desc}) is not responding")
            except:
                print(f"⚠️  {name} ({desc}) - unable to test")
        else:
            try:
                response = requests.get(url, timeout=5)
                print(f"✅ {name} ({desc}) is accessible at {url}")
            except:
                print(f"❌ {name} ({desc}) is NOT accessible at {url}")

def restart_services():
    """Restart Docker services"""
    print("\n🔄 Restarting services...")
    
    # Stop services
    print("Stopping services...")
    subprocess.run(['docker-compose', 'down'], capture_output=True)
    
    time.sleep(2)
    
    # Start services
    print("Starting services...")
    result = subprocess.run(['docker-compose', 'up', '-d'], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Services restarted")
        time.sleep(10)  # Wait for services to start
        return True
    else:
        print("❌ Failed to restart services")
        print(result.stderr)
        return False

def test_without_web():
    """Test AgenticSeek without web search"""
    print("\n💡 You can test AgenticSeek without web search:")
    print("\nTry these commands in CLI:")
    print("  - what files are in my current directory")
    print("  - create a file called test.txt with hello world")
    print("  - show me disk usage")
    print("  - write a Python script to calculate fibonacci numbers")

def main():
    print("🔧 AgenticSeek Services Check")
    print("="*50)
    
    # Check containers
    if not check_docker_containers():
        print("\n⚠️  Some services are not running")
        
        # Try to restart
        response = input("\nDo you want to restart services? (y/n): ")
        if response.lower() == 'y':
            if restart_services():
                check_docker_containers()
            else:
                print("\n❌ Failed to restart. Try manually:")
                print("  docker-compose down")
                print("  docker-compose up -d")
    
    # Test endpoints
    test_services()
    
    # Suggest alternatives
    test_without_web()
    
    print("\n📝 Summary:")
    print("If web search doesn't work, AgenticSeek can still:")
    print("  - Write and run code")
    print("  - Manage files")
    print("  - Answer questions")
    print("  - Execute system commands")

if __name__ == "__main__":
    main()