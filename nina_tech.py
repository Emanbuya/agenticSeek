"""
Nina Tech Module
Handles all technical/IT commands and queries
"""

import os
import subprocess
import platform
import socket
import psutil
import re
from pathlib import Path


class TechCommands:
    """Handles all technical commands and queries"""
    
    def __init__(self, nina):
        self.nina = nina
        self.commands = self.load_tech_commands()
        
    def load_tech_commands(self):
        """Load tech commands from config or defaults"""
        return {
            # Network commands
            "ping": self.handle_ping,
            "traceroute": self.handle_traceroute,
            "tracert": self.handle_traceroute,
            "ipconfig": self.handle_ipconfig,
            "ip address": self.handle_my_ip,
            "my ip": self.handle_my_ip,
            "ssid": self.handle_ssid,
            "wifi": self.handle_wifi_info,
            "dns": self.handle_dns,
            "flush dns": self.handle_flush_dns,
            "netstat": self.handle_netstat,
            "arp": self.handle_arp,
            
            # System commands
            "command prompt": self.handle_cmd,
            "cmd": self.handle_cmd,
            "powershell": self.handle_powershell,
            "terminal": self.handle_terminal,
            "task manager": self.handle_task_manager,
            "device manager": self.handle_device_manager,
            "services": self.handle_services,
            "event viewer": self.handle_event_viewer,
            "registry": self.handle_registry,
            "msconfig": self.handle_msconfig,
            
            # Hardware info
            "bluetooth": self.handle_bluetooth,
            "wifi status": self.handle_wifi_status,
            "battery": self.handle_battery,
            "cpu": self.handle_cpu_info,
            "temperature": self.handle_temperature,
            "processes": self.handle_processes,
            "ports": self.handle_ports,
            
            # File system
            "disk management": self.handle_disk_management,
            "defrag": self.handle_defrag,
            "system info": self.handle_system_info,
            "environment variables": self.handle_env_vars,
            
            # Security
            "firewall": self.handle_firewall,
            "windows defender": self.handle_defender,
            "updates": self.handle_updates,
        }
        
    def process_tech_command(self, command):
        """Process a technical command"""
        cmd_lower = command.lower()
        
        # Check for exact matches first
        for key, handler in self.commands.items():
            if key in cmd_lower:
                return handler(command)
                
        # Check for patterns
        if "ping" in cmd_lower:
            return self.handle_ping(command)
        elif "admin" in cmd_lower and ("cmd" in cmd_lower or "command" in cmd_lower):
            return self.handle_cmd(command, admin=True)
        elif "admin" in cmd_lower and "powershell" in cmd_lower:
            return self.handle_powershell(command, admin=True)
            
        return False
        
    # Network Commands
    def handle_ping(self, command):
        """Handle ping command"""
        # Extract target from command
        target = self.extract_target(command, "ping")
        if not target:
            # Try to find common domains in the command
            common_domains = ["google", "google.com", "8.8.8.8", "cloudflare", "1.1.1.1"]
            cmd_lower = command.lower()
            for domain in common_domains:
                if domain in cmd_lower:
                    target = domain if "." in domain else f"{domain}.com"
                    break
                    
            if not target:
                self.nina.speak("What would you like me to ping? Please specify an address or domain.")
                return True
            
        self.nina.speak(f"Opening command prompt to ping {target}...")
        
        # Open command prompt with ping command
        if platform.system() == "Windows":
            # /k keeps the window open after command completes
            subprocess.Popen(['cmd', '/k', f'ping {target}'])
        else:
            subprocess.Popen(['gnome-terminal', '--', 'ping', '-c', '4', target])
            
        return True
        
    def handle_traceroute(self, command):
        """Handle traceroute command"""
        target = self.extract_target(command, "traceroute", "tracert")
        if not target:
            self.nina.speak("What would you like me to trace? Please specify an address or domain.")
            return True
            
        self.nina.speak(f"Running traceroute to {target}. This may take a moment...")
        
        # Open command prompt with traceroute
        if platform.system() == "Windows":
            subprocess.Popen(['cmd', '/k', f'tracert {target}'])
        else:
            subprocess.Popen(['gnome-terminal', '--', 'traceroute', target])
            
        return True
        
    def handle_ipconfig(self, command):
        """Handle ipconfig command"""
        cmd_lower = command.lower()
        
        if "all" in cmd_lower:
            subprocess.Popen(['cmd', '/k', 'ipconfig /all'])
            self.nina.speak("Opening detailed network configuration.")
        elif "release" in cmd_lower:
            self.nina.speak("Releasing IP address...")
            subprocess.run(['ipconfig', '/release'], shell=True)
            self.nina.speak("IP address released.")
        elif "renew" in cmd_lower:
            self.nina.speak("Renewing IP address...")
            subprocess.run(['ipconfig', '/renew'], shell=True)
            self.nina.speak("IP address renewed.")
        else:
            # Get basic IP info
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                self.nina.speak(f"Your local IP address is {local_ip}")
            except:
                subprocess.Popen(['cmd', '/k', 'ipconfig'])
                
        return True
        
    def handle_my_ip(self, command):
        """Get IP addresses"""
        try:
            # Local IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Public IP
            import requests
            public_ip = requests.get('https://api.ipify.org', timeout=5).text
            
            self.nina.speak(f"Your local IP is {local_ip} and your public IP is {public_ip}")
        except Exception as e:
            self.nina.speak("I couldn't get your IP address. Let me open network settings.")
            subprocess.Popen(['cmd', '/k', 'ipconfig'])
            
        return True
        
    def handle_ssid(self, command):
        """Get current WiFi SSID"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                      capture_output=True, text=True)
                
                # Parse SSID from output
                for line in result.stdout.split('\n'):
                    if "SSID" in line and "BSSID" not in line:
                        ssid = line.split(":")[1].strip()
                        self.nina.speak(f"You're connected to WiFi network: {ssid}")
                        return True
                        
            self.nina.speak("I couldn't determine your WiFi network name.")
        except Exception as e:
            self.nina.speak("Error getting WiFi information.")
            
        return True
        
    def handle_wifi_info(self, command):
        """Get WiFi information"""
        subprocess.Popen(['cmd', '/k', 'netsh wlan show profiles'])
        self.nina.speak("Opening WiFi profiles and information.")
        return True
        
    def handle_dns(self, command):
        """Handle DNS queries"""
        if "flush" in command.lower():
            return self.handle_flush_dns(command)
        else:
            subprocess.Popen(['cmd', '/k', 'nslookup'])
            self.nina.speak("Opening DNS lookup tool.")
        return True
        
    def handle_flush_dns(self, command):
        """Flush DNS cache"""
        self.nina.speak("Flushing DNS cache...")
        try:
            subprocess.run(['ipconfig', '/flushdns'], shell=True, check=True)
            self.nina.speak("DNS cache has been flushed successfully.")
        except:
            self.nina.speak("I need administrator privileges to flush DNS. Let me open an admin command prompt.")
            self.handle_cmd(command, admin=True)
        return True
        
    def handle_netstat(self, command):
        """Show network statistics"""
        cmd_lower = command.lower()
        if "listening" in cmd_lower:
            subprocess.Popen(['cmd', '/k', 'netstat -an | findstr LISTENING'])
        else:
            subprocess.Popen(['cmd', '/k', 'netstat -an'])
        self.nina.speak("Opening network connections and statistics.")
        return True
        
    def handle_arp(self, command):
        """Show ARP table"""
        subprocess.Popen(['cmd', '/k', 'arp -a'])
        self.nina.speak("Opening ARP table showing network devices.")
        return True
        
    # System Commands
    def handle_cmd(self, command, admin=False):
        """Open command prompt"""
        if admin or "admin" in command.lower():
            self.nina.speak("Opening administrator command prompt...")
            subprocess.run(['powershell', 'Start-Process', 'cmd', '-Verb', 'RunAs'], shell=True)
        else:
            self.nina.speak("Opening command prompt...")
            subprocess.Popen(['cmd'])
        return True
        
    def handle_powershell(self, command, admin=False):
        """Open PowerShell"""
        if admin or "admin" in command.lower():
            self.nina.speak("Opening administrator PowerShell...")
            subprocess.run(['powershell', 'Start-Process', 'powershell', '-Verb', 'RunAs'], shell=True)
        else:
            self.nina.speak("Opening PowerShell...")
            subprocess.Popen(['powershell'])
        return True
        
    def handle_terminal(self, command):
        """Open terminal (alias for cmd)"""
        return self.handle_cmd(command)
        
    def handle_task_manager(self, command):
        """Open Task Manager"""
        self.nina.speak("Opening Task Manager...")
        subprocess.Popen(['taskmgr'])
        return True
        
    def handle_device_manager(self, command):
        """Open Device Manager"""
        self.nina.speak("Opening Device Manager...")
        subprocess.Popen(['devmgmt.msc'])
        return True
        
    def handle_services(self, command):
        """Open Services"""
        self.nina.speak("Opening Windows Services...")
        subprocess.Popen(['services.msc'])
        return True
        
    def handle_event_viewer(self, command):
        """Open Event Viewer"""
        self.nina.speak("Opening Event Viewer...")
        subprocess.Popen(['eventvwr.msc'])
        return True
        
    def handle_registry(self, command):
        """Open Registry Editor"""
        self.nina.speak("Opening Registry Editor. Please be careful with any changes.")
        subprocess.Popen(['regedit'])
        return True
        
    def handle_msconfig(self, command):
        """Open System Configuration"""
        self.nina.speak("Opening System Configuration...")
        subprocess.Popen(['msconfig'])
        return True
        
    # Hardware Info
    def handle_bluetooth(self, command):
        """Check Bluetooth status"""
        try:
            # Check if Bluetooth service is running
            result = subprocess.run(['sc', 'query', 'bthserv'], 
                                  capture_output=True, text=True, shell=True)
            
            if "RUNNING" in result.stdout:
                self.nina.speak("Bluetooth is enabled and running.")
            else:
                self.nina.speak("Bluetooth appears to be disabled or not running.")
                
            # Open Bluetooth settings
            if "settings" in command.lower() or "open" in command.lower():
                subprocess.Popen(['ms-settings:bluetooth'])
                
        except:
            self.nina.speak("I couldn't check Bluetooth status. Let me open Bluetooth settings.")
            subprocess.Popen(['ms-settings:bluetooth'])
            
        return True
        
    def handle_wifi_status(self, command):
        """Check WiFi status"""
        try:
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                  capture_output=True, text=True)
            
            if "State" in result.stdout and "connected" in result.stdout.lower():
                self.nina.speak("WiFi is connected.")
            else:
                self.nina.speak("WiFi appears to be disconnected.")
                
        except:
            self.nina.speak("I couldn't check WiFi status.")
            
        return True
        
    def handle_battery(self, command):
        """Check battery status"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = "plugged in" if battery.power_plugged else "on battery"
                
                if battery.secsleft != psutil.POWER_TIME_UNLIMITED:
                    time_left = battery.secsleft // 60
                    hours = time_left // 60
                    minutes = time_left % 60
                    self.nina.speak(f"Battery is at {percent}%, {plugged}, with about {hours} hours and {minutes} minutes remaining.")
                else:
                    self.nina.speak(f"Battery is at {percent}% and {plugged}.")
            else:
                self.nina.speak("No battery detected. This might be a desktop computer.")
        except:
            self.nina.speak("I couldn't get battery information.")
            
        return True
        
    def handle_cpu_info(self, command):
        """Get CPU information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            response = f"CPU usage is {cpu_percent}% across {cpu_count} cores"
            if cpu_freq:
                response += f", running at {cpu_freq.current:.0f} MHz"
                
            self.nina.speak(response)
        except:
            self.nina.speak("I couldn't get CPU information.")
            
        return True
        
    def handle_temperature(self, command):
        """Get system temperature"""
        # Note: Temperature sensors are very platform-specific
        self.nina.speak("Temperature monitoring requires specialized tools. Let me open Task Manager where you can see performance metrics.")
        subprocess.Popen(['taskmgr'])
        return True
        
    def handle_processes(self, command):
        """Show running processes"""
        subprocess.Popen(['cmd', '/k', 'tasklist'])
        self.nina.speak("Opening list of running processes.")
        return True
        
    def handle_ports(self, command):
        """Show open ports"""
        subprocess.Popen(['cmd', '/k', 'netstat -an | findstr LISTENING'])
        self.nina.speak("Opening list of listening ports.")
        return True
        
    # File System
    def handle_disk_management(self, command):
        """Open Disk Management"""
        self.nina.speak("Opening Disk Management...")
        subprocess.Popen(['diskmgmt.msc'])
        return True
        
    def handle_defrag(self, command):
        """Open Defragment tool"""
        self.nina.speak("Opening disk defragmentation tool...")
        subprocess.Popen(['dfrgui'])
        return True
        
    def handle_system_info(self, command):
        """Show system information"""
        subprocess.Popen(['cmd', '/k', 'systeminfo'])
        self.nina.speak("Gathering system information...")
        return True
        
    def handle_env_vars(self, command):
        """Open Environment Variables"""
        self.nina.speak("Opening Environment Variables...")
        subprocess.Popen(['rundll32.exe', 'sysdm.cpl,EditEnvironmentVariables'])
        return True
        
    # Security
    def handle_firewall(self, command):
        """Open Windows Firewall"""
        self.nina.speak("Opening Windows Firewall settings...")
        subprocess.Popen(['wf.msc'])
        return True
        
    def handle_defender(self, command):
        """Open Windows Defender"""
        self.nina.speak("Opening Windows Security...")
        subprocess.Popen(['ms-settings:windowsdefender'])
        return True
        
    def handle_updates(self, command):
        """Open Windows Update"""
        self.nina.speak("Opening Windows Update...")
        subprocess.Popen(['ms-settings:windowsupdate'])
        return True
        
    # Utility methods
    def extract_target(self, command, *keywords):
        """Extract target (domain/IP) from command"""
        cmd_lower = command.lower()
        
        # Fix common speech patterns for IP addresses
        number_words = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
        }
        
        # Replace number words with digits
        for word, digit in number_words.items():
            cmd_lower = cmd_lower.replace(word, digit)
        
        # Fix patterns like "8.8 the 8 da 8" -> "8.8.8.8"
        cmd_lower = cmd_lower.replace(" the ", ".")
        cmd_lower = cmd_lower.replace(" da ", ".")
        cmd_lower = cmd_lower.replace(" to ", ".")
        cmd_lower = cmd_lower.replace("dot", ".")
        
        # Clean up multiple spaces
        cmd_lower = ' '.join(cmd_lower.split())
        
        # Common DNS servers
        if "8.8.8.8" in cmd_lower or "8.8.8" in cmd_lower:
            return "8.8.8.8"
        if "1.1.1.1" in cmd_lower or "1.1.1" in cmd_lower:
            return "1.1.1.1"
        
        # Check for IP addresses (pattern like X.X.X.X)
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        ip_match = re.search(ip_pattern, cmd_lower)
        if ip_match:
            return ip_match.group(1)
        
        # Common domains
        if "google" in cmd_lower:
            return "google.com"
        if "cloudflare" in cmd_lower:
            return "cloudflare.com"
            
        # Extract target after keyword
        for keyword in keywords:
            if keyword in cmd_lower:
                # Split by the keyword and get everything after it
                parts = cmd_lower.split(keyword, 1)
                if len(parts) > 1 and parts[1].strip():
                    # Get the target, handling various formats
                    remaining = parts[1].strip()
                    # Remove common filler words
                    for filler in ["to", "the", "at", "address", "ip"]:
                        remaining = remaining.replace(f" {filler} ", " ").strip()
                        if remaining.startswith(f"{filler} "):
                            remaining = remaining[len(filler)+1:].strip()
                    
                    # Get the first word/domain
                    target_words = remaining.split()
                    if target_words:
                        # Try to reconstruct IP if it looks like one
                        if all(part.replace('.', '').isdigit() for part in target_words[:4]):
                            return '.'.join(target_words[:4])
                        else:
                            return target_words[0]
        return None
        
    def is_tech_command(self, command):
        """Check if this is a tech command"""
        cmd_lower = command.lower()
        
        # Tech keywords
        tech_keywords = [
            "ping", "traceroute", "tracert", "ipconfig", "ip address", "ssid",
            "cmd", "command prompt", "powershell", "terminal", "admin",
            "bluetooth", "wifi", "network", "dns", "firewall",
            "task manager", "device manager", "services", "registry",
            "disk management", "defrag", "system info",
            "netstat", "arp", "ports", "processes",
            "msconfig", "event viewer", "defender", "updates"
        ]
        
        return any(keyword in cmd_lower for keyword in tech_keywords)