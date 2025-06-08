"""
Nina Intent Detection
Determines what the user wants to do based on their command
"""


class IntentDetector:
    """Detects user intent from voice commands"""
    
    def __init__(self, personal_config):
        self.personal_config = personal_config
        
    def is_schedule_query(self, command):
        """Check if command is about schedule"""
        schedule_keywords = ["schedule", "meeting", "appointment", "calendar", "agenda"]
        return any(keyword in command.lower() for keyword in schedule_keywords)
    
    def is_vision_query(self, command):
        """Check if command is about seeing/viewing the screen"""
        vision_keywords = [
            "what screen", "what do you see", "can you see", 
            "look at", "what's on my screen", "what am i looking at",
            "help me with this", "help with current", "read the screen",
            "what window", "which application", "what app",
            "describe what", "tell me what you see"
        ]
        cmd_lower = command.lower()
        return any(keyword in cmd_lower for keyword in vision_keywords)
        
    def determine_intent(self, command):
        """Determine intent from command"""
        cmd = command.lower()
        
        # VISION QUERIES - CHECK FIRST
        if self.is_vision_query(command):
            return "vision"
        
        # Python fixing - CHECK EARLY
        if "fix" in cmd and any(word in cmd for word in ["python", "code", "indentation", "formatting"]):
            return "fix_python"
        
        # Tech/IT queries - CHECK EARLY
        tech_keywords = [
            "ping", "traceroute", "tracert", "ipconfig", "ip address", "ssid",
            "cmd", "command prompt", "powershell", "terminal", "admin",
            "bluetooth", "wifi", "network", "dns", "firewall",
            "task manager", "device manager", "services", "registry",
            "disk management", "defrag", "system info",
            "netstat", "arp", "ports", "processes",
            "msconfig", "event viewer", "defender", "updates"
        ]
        if any(keyword in cmd for keyword in tech_keywords):
            return "tech"
        
        # Quick file operations
        if "open" in cmd:
            quick_files = self.personal_config.get_quick_files()
            for name, path in quick_files.items():
                if name in cmd:
                    return "open_quick_file"
                    
        # Website operations
        if any(word in cmd for word in ["open", "go to", "visit", "show"]):
            websites = self.personal_config.get_websites()
            for name, url in websites.items():
                if name in cmd and name != "news":  # news handled separately
                    return "open_website"
        
        # Schedule queries
        if self.is_schedule_query(command):
            return "schedule"
        
        # Hardware/System queries
        if any(word in cmd for word in ["memory", "ram", "disk", "space", "storage", "gpu", 
                                        "graphics", "hardware", "system", "specs", "how much"]):
            # Make sure it's about computer hardware
            if any(word in cmd for word in ["memory", "ram", "disk", "space", "storage"]):
                return "hardware"
                
        # News queries
        if any(word in cmd for word in ["news", "headline", "headlines", "latest news", 
                                        "breaking news", "current events"]):
            return "news"
            
        # Sports - Check for team names
        sports_teams = self.personal_config.get_sports_teams()
        if any(team in cmd for team in sports_teams) or \
           (any(word in cmd for word in ["game", "score", "won", "lost", "beat", "play", "played"]) and \
            any(word in cmd for word in ["yesterday", "today", "last night", "team", "they"])):
            return "sports"
            
        # Application launching
        if any(word in cmd for word in ["open", "launch", "start", "run"]) and \
           any(app in cmd for app in ["word", "excel", "powerpoint", "notepad", "chrome", 
                                      "firefox", "edge", "calculator", "paint", "outlook"]):
            return "open_app"
            
        # Folder operations - CHECK BEFORE FILE OPERATIONS
        if "folder" in cmd and any(word in cmd for word in ["open", "show", "go to", "access"]):
            return "folder"
            
        # File OPENING operations
        if (any(word in cmd for word in ["open", "opened", "launch", "start", "run"]) and \
            any(word in cmd for word in ["resume", "pdf", "doc", "file", "document"]) and \
            "folder" not in cmd) or \
           any(ext in cmd for ext in [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".ppt"]) or \
           ("guardicore" in cmd and any(word in cmd for word in ["open", "opened"]) and "folder" not in cmd):
            return "open_file"
            
        # File SEARCH operations
        if any(word in cmd for word in ["find", "search", "look for", "locate", "where is"]) and \
           any(word in cmd for word in ["file", "document", "resume", "pdf", "doc", ".txt", ".docx"]):
            return "files"
            
        # Code writing
        if any(word in cmd for word in ["write", "create", "make", "build"]) and \
           any(word in cmd for word in ["code", "script", "program", "calculator", "function", "app"]):
            return "code"
        
        # LLM management commands
        if any(phrase in cmd for phrase in ["switch model", "use model", "launch model", 
                                   "list models", "current model", "install model",
                                   "switch to", "activate"]) and \
           any(word in cmd for word in ["model", "llm", "coder", "deepseek", "codellama", "default"]):
           return "llm_management"
            
        # Weather
        if "weather" in cmd or "temperature" in cmd or "forecast" in cmd:
            return "weather"
            
        # Time
        if "time" in cmd and any(word in cmd for word in ["what", "current", "tell"]):
            return "time"
            
        # Web search
        if any(phrase in cmd for phrase in ["who is", "what is", "search for", "look up", "tell me about"]):
            return "search"
            
        # Default
        return "general"