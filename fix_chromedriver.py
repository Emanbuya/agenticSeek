#!/usr/bin/env python3
"""
Fix ChromeDriver installation for AgenticSeek
"""

import os
import subprocess
import sys
import urllib.request
import zipfile
import shutil

def check_chrome_version():
    """Get installed Chrome version"""
    print("🔍 Checking Chrome version...")
    
    try:
        # Windows Chrome path
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                result = subprocess.run([path, '--version'], capture_output=True, text=True)
                version = result.stdout.strip()
                print(f"✅ Found Chrome: {version}")
                
                # Extract version number
                version_num = version.split()[-1].split('.')[0]
                return version_num
    except:
        pass
    
    print("❌ Could not detect Chrome version")
    return None

def download_chromedriver_manually(version):
    """Download ChromeDriver manually"""
    print(f"\n📥 Downloading ChromeDriver for Chrome {version}...")
    
    # ChromeDriver download URL
    if int(version) >= 115:
        # New URL format for Chrome 115+
        url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}.0.0.0/win64/chromedriver-win64.zip"
    else:
        # Old URL format
        url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version}"
    
    print(f"Download URL: {url}")
    
    try:
        # Create temp directory
        temp_dir = "chromedriver_temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Download
        zip_path = os.path.join(temp_dir, "chromedriver.zip")
        
        print("Downloading...")
        # Use subprocess to download with curl/wget to avoid permission issues
        if shutil.which('curl'):
            subprocess.run(['curl', '-L', url, '-o', zip_path])
        elif shutil.which('wget'):
            subprocess.run(['wget', url, '-O', zip_path])
        else:
            # Fallback to Python
            urllib.request.urlretrieve(url, zip_path)
        
        if os.path.exists(zip_path):
            print("✅ Downloaded successfully")
            return zip_path
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
    
    return None

def install_chromedriver_to_path():
    """Add ChromeDriver to PATH or copy to current directory"""
    print("\n🔧 Installing ChromeDriver...")
    
    # Check if chromedriver exists in current directory
    if os.path.exists("chromedriver.exe"):
        print("✅ chromedriver.exe already exists in current directory")
        return True
    
    # Try to find it in common locations
    common_paths = [
        r"C:\chromedriver\chromedriver.exe",
        r"C:\Program Files\chromedriver\chromedriver.exe",
        os.path.join(os.environ.get('USERPROFILE', ''), 'chromedriver', 'chromedriver.exe')
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            print(f"✅ Found ChromeDriver at: {path}")
            # Copy to current directory
            shutil.copy(path, "chromedriver.exe")
            print("✅ Copied to current directory")
            return True
    
    return False

def quick_fix():
    """Quick fix - disable browser for testing"""
    print("\n💡 Quick Fix: Running without browser")
    print("This will disable web browsing but allow other features to work")
    
    # Create a minimal config
    config_content = """[MAIN]
is_local = True
provider_name = ollama
provider_model = phi3:mini
provider_server_address = 127.0.0.1:11434
agent_name = Jarvis
recover_last_session = False
save_session = False
speak = False
listen = False
work_dir = .
jarvis_personality = False
languages = en

[BROWSER]
headless_browser = True
stealth_mode = False
disable_browser = True
"""
    
    with open('config_no_browser.ini', 'w') as f:
        f.write(config_content)
    
    print("✅ Created config_no_browser.ini")
    print("\nTo run without browser:")
    print("  python cli.py --config config_no_browser.ini")

def main():
    print("🔧 Fixing ChromeDriver for AgenticSeek")
    print("="*50)
    
    # Check Chrome version
    version = check_chrome_version()
    
    if not version:
        print("\n❌ Chrome not detected")
        print("Please install Google Chrome first")
        return
    
    # Check if ChromeDriver exists
    if install_chromedriver_to_path():
        print("\n✅ ChromeDriver is ready!")
        print("Try running AgenticSeek again: python cli.py")
        return
    
    print("\n⚠️  ChromeDriver not found locally")
    
    # Manual download instructions
    print("\n📝 Manual Installation Instructions:")
    print(f"1. Go to: https://googlechromelabs.github.io/chrome-for-testing/")
    print(f"2. Find version {version}.x.x.x")
    print("3. Download 'chromedriver' for 'win64'")
    print("4. Extract chromedriver.exe to this directory")
    print("5. Run AgenticSeek again")
    
    # Offer quick fix
    print("\n" + "="*50)
    quick_fix()

if __name__ == "__main__":
    main()