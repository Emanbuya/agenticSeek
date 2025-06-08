"""
Nina Configuration Management
Handles personal configuration file (nina_personal.ini)
"""

import os
import configparser
from datetime import date


class PersonalConfig:
    """Load and manage personal configuration"""
    
    def __init__(self, config_path="nina_personal.ini"):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        
        if not os.path.exists(config_path):
            self.create_default_config()
        
        self.config.read(config_path)
        
    def create_default_config(self):
        """Create default config"""
        username = os.environ.get('USERNAME', 'User')
        default_config = f"""# nina_personal.ini
# Personal configuration for Nina - customize this with your folders and preferences

[FOLDERS]
# Add your frequently accessed folders here
# Format: nickname = full_path
documents = C:\\Users\\{username}\\OneDrive\\Documents
downloads = C:\\Users\\{username}\\Downloads
desktop = C:\\Users\\{username}\\Desktop
employment = C:\\Users\\{username}\\OneDrive\\Documents\\Employment
employer = C:\\Users\\{username}\\OneDrive\\Documents\\Employment

[QUICK_FILES]
# Add frequently accessed files
resume = C:\\Users\\{username}\\OneDrive\\Documents\\Resume.pdf

[APPLICATIONS]
# Add your preferred applications
calculator = calc.exe
notepad = notepad.exe
browser = C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe
vscode = C:\\Program Files\\Microsoft VS Code\\Code.exe
outlook = outlook.exe

[WEBSITES]
# Add your frequently visited websites
email = https://outlook.com
calendar = https://calendar.google.com
weather = https://weather.com
news = https://news.google.com

[SCHEDULE]
# Simple schedule entries
# Format: day = activity1 | time1, activity2 | time2
monday = No meetings scheduled
tuesday = No meetings scheduled
wednesday = No meetings scheduled
thursday = Code review | 11:00 AM, Planning meeting | 2:00 PM
friday = Team sync | 9:00 AM, Weekly report | 4:00 PM

[PREFERENCES]
# Personal preferences
default_browser = chrome
default_editor = vscode
preferred_news_source = google
location = San Marcos, Texas
news_source = https://www.foxnews.com
news_politics = https://www.foxnews.com/politics
news_business = https://www.foxnews.com/business
news_tech = https://www.foxnews.com/tech
news_breaking = https://www.foxnews.com/breaking-news

[SPORTS_TEAMS]
# Your favorite sports teams
team1 = Dodgers
team2 = Lakers
team3 = Rams
team4 = Cowboys

[SOCIAL_MEDIA]
# Social media platforms
platform1 = twitter|https://twitter.com
platform2 = linkedin|https://linkedin.com
platform3 = facebook|https://facebook.com
"""
        
        with open(self.config_path, 'w') as f:
            f.write(default_config)
            
    def get_folder(self, nickname):
        """Get folder path by nickname"""
        if self.config.has_option('FOLDERS', nickname):
            return self.config.get('FOLDERS', nickname)
        return None
        
    def get_all_folders(self):
        """Get all configured folders"""
        if self.config.has_section('FOLDERS'):
            return dict(self.config.items('FOLDERS'))
        return {}
        
    def get_schedule(self, day=None):
        """Get schedule for a specific day"""
        if not self.config.has_section('SCHEDULE'):
            return None
            
        if day is None:
            day = date.today().strftime("%A").lower()
        else:
            day = day.lower()
            
        if self.config.has_option('SCHEDULE', day):
            schedule_str = self.config.get('SCHEDULE', day)
            if schedule_str.lower() == "no meetings scheduled":
                return None
            
            entries = []
            for entry in schedule_str.split(','):
                if '|' in entry:
                    parts = entry.strip().split('|')
                    if len(parts) == 2:
                        entries.append({
                            'activity': parts[0].strip(),
                            'time': parts[1].strip()
                        })
            return entries if entries else None
        return None
        
    def get_quick_files(self):
        """Get configured quick access files"""
        files = {}
        if self.config.has_section('QUICK_FILES'):
            for key, value in self.config.items('QUICK_FILES'):
                files[key] = value
        return files
        
    def get_websites(self):
        """Get configured websites"""
        sites = {}
        if self.config.has_section('WEBSITES'):
            for key, value in self.config.items('WEBSITES'):
                sites[key] = value
        return sites
        
    def get_applications(self):
        """Get configured applications"""
        apps = {}
        if self.config.has_section('APPLICATIONS'):
            for key, value in self.config.items('APPLICATIONS'):
                apps[key] = value
        return apps
        
    def get_preference(self, key, default=None):
        """Get a preference value"""
        if self.config.has_option('PREFERENCES', key):
            return self.config.get('PREFERENCES', key)
        return default
        
    def get_sports_teams(self):
        """Get configured sports teams"""
        teams = []
        if self.config.has_section('SPORTS_TEAMS'):
            for key, value in self.config.items('SPORTS_TEAMS'):
                teams.append(value.lower())
        return teams if teams else ["dodgers", "lakers", "rams", "cowboys"]
        
    def get_social_media(self):
        """Get configured social media platforms"""
        platforms = {}
        if self.config.has_section('SOCIAL_MEDIA'):
            for key, value in self.config.items('SOCIAL_MEDIA'):
                if '|' in value:
                    name, url = value.split('|', 1)
                    platforms[name.lower()] = url
        return platforms if platforms else {
            "twitter": "https://twitter.com",
            "linkedin": "https://linkedin.com"
        }