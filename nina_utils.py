"""
Nina Utility Functions
Shared utilities for text processing, output, etc.
"""

import io
import sys
import re
import contextlib
import time

# Simple color codes using ANSI escape sequences
COLOR_MAP = {
    "info": "\033[36m",      # Cyan
    "success": "\033[32m",   # Green
    "warning": "\033[33m",   # Yellow
    "failure": "\033[31m",   # Red
    "status": "\033[35m",    # Magenta
    "output": "\033[37m"     # White
}
RESET = "\033[0m"


@contextlib.contextmanager
def quiet():
    """Suppress stdout and stderr"""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def clean_for_speech(text, nina_instance=None):
    """Clean text for speech synthesis"""
    if not text:
        return ""
        
    # Remove code blocks
    if "```" in text:
        code_match = re.search(r'```(?:python)?\n?(.*?)```', text, re.DOTALL)
        if code_match and nina_instance:
            nina_instance.last_code = code_match.group(1)
        text = re.sub(r'```[\s\S]*?```', 'I\'ve written the code for you.', text).strip()
        
    # Clean paths
    text = re.sub(r'[A-Z]:\\[^\s]+', 'in the folder', text)
    text = re.sub(r'https?://\S+', '', text)
    
    # Replacements
    replacements = {
        "TX": "Texas",
        ".py": " dot py",
        "GB": "gigabytes",
        "...": ".",
        "  ": " "
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
        
    # Limit length
    if len(text) > 250:
        sentences = text.split('. ')
        text = '. '.join(sentences[:2]) + '.' if sentences else text[:250]
            
    return text.strip()


def convert_spoken_symbols(text):
    """Convert spoken symbols to actual symbols"""
    conversions = {
        " underscore ": "_",
        " dot ": ".",
        " dash ": "-",
        " slash ": "/",
        " backslash ": "\\",
        " at ": "@",
        " hashtag ": "#",
        " dollar sign ": "$",
        " percent ": "%",
        " ampersand ": "&",
        " asterisk ": "*",
        " plus ": "+",
        " equals ": "=",
    }
    
    for spoken, symbol in conversions.items():
        text = text.replace(spoken, symbol)
        
    return text


def fix_voice_recognition_errors(text):
    """Fix common voice recognition errors"""
    # Fix spoken numbers to digits for IP addresses and technical contexts
    if any(word in text.lower() for word in ["ping", "ip", "address", "traceroute", "ssh", "telnet"]):
        text = convert_spoken_numbers_to_digits(text)
    
    fixes = {
        # Company names - all variations
        "guarded core": "guardicore",
        "guard corps": "guardicore", 
        "guardian core": "guardicore",
        "garden core": "guardicore",
        "guard a core": "guardicore",
        "guard a corps": "guardicore",
        
        # Common misheard words
        "my ass this": "maestas",
        "my estus": "maestas",
        "my estas": "maestas",
        
        # File types
        "dot pdf": ".pdf",
        "dot doc": ".doc",
        "dot docx": ".docx",
        
        # Common DNS servers
        "eight.eight.eight.eight": "8.8.8.8",
        "eight dot eight dot eight dot eight": "8.8.8.8",
        "one.one.one.one": "1.1.1.1",
        "one dot one dot one dot one": "1.1.1.1",
    }
    
    text_lower = text.lower()
    for wrong, right in fixes.items():
        if wrong in text_lower:
            # Case-insensitive replacement
            text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
            
    return text


def convert_spoken_numbers_to_digits(text):
    """Convert spoken numbers to digits, especially for IP addresses"""
    # Number word to digit mapping
    number_words = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
        "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
        "eighteen": "18", "nineteen": "19", "twenty": "20"
    }
    
    # Replace number words with digits
    words = text.split()
    new_words = []
    
    for word in words:
        # Check if word (without punctuation) is a number word
        clean_word = word.lower().strip('.,!?;:')
        if clean_word in number_words:
            # Preserve any punctuation
            prefix = ""
            suffix = ""
            if word[0] in '.,!?;:':
                prefix = word[0]
                word = word[1:]
            if word and word[-1] in '.,!?;:':
                suffix = word[-1]
                word = word[:-1]
            
            new_words.append(prefix + number_words[clean_word] + suffix)
        else:
            new_words.append(word)
    
    text = ' '.join(new_words)
    
    # Fix common patterns like "eight got eight" -> "8.8"
    text = re.sub(r'(\d+)\s*got\s*(\d+)', r'\1.\2', text)
    
    # Fix patterns like "8 to 8" -> "8.8"
    text = re.sub(r'(\d+)\s*to\s*(\d+)', r'\1.\2', text)
    
    return text


def pretty_print(text, color="info", no_newline=False):
    """Print with color formatting"""
    selected_color = COLOR_MAP.get(color, COLOR_MAP["output"])
    
    if no_newline:
        print(selected_color + text + RESET, end='')
    else:
        print(selected_color + text + RESET)


def animate_thinking(message="Thinking...", color="status", duration=0.5):
    """Show animated thinking message"""
    pretty_print(message, color=color)
    # In a real implementation, this could show a spinner
    time.sleep(duration)