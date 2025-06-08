# test_nina_setup.py
import os
import sys

print("=== Nina Setup Diagnostic ===\n")

# Check current directory
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path[0]}\n")

# Check if files exist
files_to_check = [
    'nina_vision.py',
    'nina_intern_mode.py', 
    'nina_python_fixer.py',
    'nina_tech.py',
    'nina_utils.py'
]

print("File check:")
for f in files_to_check:
    exists = "✅" if os.path.exists(f) else "❌"
    print(f"{exists} {f}")

print("\nPackage check:")
packages = [
    ('pyautogui', 'pyautogui'),
    ('pytesseract', 'pytesseract'),
    ('cv2', 'opencv-python'),
    ('mss', 'mss'),
    ('win32gui', 'pywin32'),
    ('PIL', 'pillow'),
    ('mouse', 'mouse'),
    ('keyboard', 'keyboard')
]

for module, package in packages:
    try:
        __import__(module)
        print(f"✅ {package}")
    except ImportError:
        print(f"❌ {package} - install with: pip install {package}")

# Test Tesseract
print("\nTesseract check:")
try:
    import pytesseract
    # Try to run tesseract
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
    except Exception as e:
        print(f"❌ Tesseract not found: {e}")
        print("   Download from: https://github.com/UB-Mannheim/tesseract/wiki")
except ImportError:
    print("❌ pytesseract not installed")

# Check if running in correct environment
print(f"\nPython executable: {sys.executable}")
print(f"Virtual env: {'Yes' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'No'}")