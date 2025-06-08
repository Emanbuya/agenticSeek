# nina_paths.py
# Custom path configuration for Nina

from pathlib import Path

# User-specific paths
USER_PATHS = {
    "documents": [
        r"C:\Users\erm72\OneDrive\Documents",
        r"F:\Documents",  # Add your F drive documents path
        r"D:\Documents",  # Add your D drive documents path
    ],
    "projects": [
        r"F:\AI_Projects",
        r"F:\Projects",
    ],
    "downloads": [
        Path.home() / "Downloads",
        r"F:\Downloads",  # If you have downloads on F drive
    ]
}

# Quick access drives
SEARCH_DRIVES = {
    "main": ["C:", "F:", "D:"],
    "external": ["E:", "G:"],  # Add any external drives
    "all": ["C:", "D:", "E:", "F:", "G:"]
}

# File type patterns
FILE_PATTERNS = {
    "documents": ["*.pdf", "*.doc", "*.docx", "*.txt", "*.odt"],
    "images": ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.svg"],
    "videos": ["*.mp4", "*.avi", "*.mkv", "*.mov", "*.wmv"],
    "audio": ["*.mp3", "*.wav", "*.flac", "*.m4a", "*.ogg"],
    "code": ["*.py", "*.js", "*.java", "*.cpp", "*.c", "*.html", "*.css"],
    "data": ["*.csv", "*.xlsx", "*.json", "*.xml", "*.sql"],
}