"""
Nina Custom Agents
Hardware and File Search agents that don't require Agentic Seek
"""

import os
import platform
import subprocess
import psutil
from pathlib import Path


class HardwareAgent:
    """Simple hardware information agent"""
    
    def __init__(self, name, prompt_path, provider, verbose=False):
        self.agent_name = name
        self.type = "hardware_agent"
        self.role = "hardware"
        self.llm = provider
        self.memory = None
        
    def get_memory_info(self):
        """Get memory (RAM) information"""
        try:
            ram = psutil.virtual_memory()
            total_gb = ram.total / (1024**3)
            used_gb = ram.used / (1024**3)
            available_gb = ram.available / (1024**3)
            percent = ram.percent
            
            return f"You have {total_gb:.1f} GB of RAM total. Currently using {used_gb:.1f} GB ({percent:.1f}%), with {available_gb:.1f} GB available."
        except Exception as e:
            return f"Error getting memory info: {str(e)}"
            
    def get_disk_space(self):
        """Get disk space information"""
        try:
            disks_info = []
            for partition in psutil.disk_partitions():
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                    
                usage = psutil.disk_usage(partition.mountpoint)
                total_gb = usage.total / (1024**3)
                used_gb = usage.used / (1024**3)
                free_gb = usage.free / (1024**3)
                percent = usage.percent
                
                disk_info = f"{partition.device} has {total_gb:.1f} GB total, using {used_gb:.1f} GB ({percent:.1f}%), with {free_gb:.1f} GB free"
                disks_info.append(disk_info)
                
            return "Your disk space: " + ". ".join(disks_info)
        except Exception as e:
            return f"Error getting disk space: {str(e)}"
            
    def get_gpu_info(self):
        """Get GPU information"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'],
                                      capture_output=True, text=True, shell=True)
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines[1:]:
                    if line.strip() and line.strip() != "Name":
                        gpus.append(line.strip())
                return "Your graphics card: " + ', '.join(gpus) if gpus else "No GPU information found"
        except:
            return "Could not get GPU information"
            
    async def process(self, query, speech_module):
        """Process hardware queries"""
        query_lower = query.lower()
        
        if "memory" in query_lower or "ram" in query_lower:
            return self.get_memory_info(), ""
        elif "disk" in query_lower or "space" in query_lower or "storage" in query_lower:
            return self.get_disk_space(), ""
        elif "gpu" in query_lower or "graphics" in query_lower:
            return self.get_gpu_info(), ""
        else:
            # Return all info
            info = []
            info.append(self.get_memory_info())
            info.append(self.get_disk_space())
            info.append(self.get_gpu_info())
            return " ".join(info), ""


class DirectFileSearchAgent:
    """Direct file search agent that actually works"""
    
    def __init__(self, name, prompt_path, provider, verbose=False):
        self.agent_name = name
        self.type = "file_agent"  # Pretend to be file agent
        self.role = "files"
        self.llm = provider
        self.memory = None
        self.tools = {}  # Empty tools dict for compatibility
        
    def search_files_and_folders(self, search_term, search_path=None):
        """Search for files and folders containing the search term"""
        if not search_path:
            # Default search locations
            home = Path.home()
            search_paths = [
                str(home / "OneDrive" / "Documents"),
                str(home / "Documents"),
                str(home / "Desktop"),
                str(home / "Downloads"),
            ]
        else:
            search_paths = [search_path]
            
        results = {
            'files': [],
            'folders': []
        }
        
        for base_path in search_paths:
            if not os.path.exists(base_path):
                continue
                
            try:
                # Search for files and folders
                for root, dirs, files in os.walk(base_path):
                    # Don't go too deep (max 3 levels)
                    depth = root[len(base_path):].count(os.sep)
                    if depth > 3:
                        continue
                        
                    # Check folders
                    for dir_name in dirs:
                        if search_term.lower() in dir_name.lower():
                            full_path = os.path.join(root, dir_name)
                            results['folders'].append(full_path)
                            
                    # Check files
                    for file_name in files:
                        if search_term.lower() in file_name.lower():
                            full_path = os.path.join(root, file_name)
                            results['files'].append(full_path)
                            
                    # Limit total results
                    if len(results['files']) + len(results['folders']) > 50:
                        return results
                        
            except PermissionError:
                continue
            except Exception as e:
                print(f"Error searching {base_path}: {e}")
                continue
                
        return results
        
    async def process(self, query, speech_module):
        """Process file/folder search queries"""
        query_lower = query.lower()
        search_term = None
        
        # Extract search term from various patterns
        patterns = [
            ("called", 1),  # "file called X"
            ("named", 1),   # "file named X"
            ("find", 1),    # "find X"
            ("search for", 2),  # "search for X"
            ("look for", 2),    # "look for X"
        ]
        
        for pattern, word_count in patterns:
            if pattern in query_lower:
                parts = query_lower.split(pattern, 1)
                if len(parts) > 1:
                    remaining = parts[1].strip()
                    # For multi-word patterns, extract more words
                    words = remaining.split()
                    if words:
                        # Take the specified number of words
                        search_words = []
                        skip_words = ["a", "an", "the", "me", "my", "file", "folder", "document", "pdf"]
                        word_count_found = 0
                        for word in words:
                            if word not in skip_words:
                                search_words.append(word)
                                word_count_found += 1
                                if word_count_found >= word_count:
                                    break
                        if search_words:
                            search_term = " ".join(search_words)
                            break
                            
        # Special case for "resume"
        if not search_term and "resume" in query_lower:
            search_term = "resume"
            
        if not search_term:
            return "I need to know what to search for. Please specify a file or folder name.", ""
            
        print(f"🔍 Searching for: '{search_term}'")
        
        # Perform search
        results = self.search_files_and_folders(search_term)
        
        # Format response
        total_found = len(results['files']) + len(results['folders'])
        
        if total_found == 0:
            searched_locations = "Documents, Desktop, and Downloads"
            return f"I couldn't find any files or folders containing '{search_term}' in your {searched_locations} folders.", ""
            
        # Build response
        response_parts = []
        response_parts.append(f"I found {total_found} items containing '{search_term}':")
        
        # Show folders (limit to 3)
        if results['folders']:
            folder_count = len(results['folders'])  # Define variable first
            response_parts.append(f"\n📁 FOLDERS ({folder_count}):")
            for i, folder_path in enumerate(results['folders'][:3]):
                folder_name = os.path.basename(folder_path)
                parent_dir = os.path.basename(os.path.dirname(folder_path))
                response_parts.append(f"  • {folder_name} (in {parent_dir})")
            if folder_count > 3:
                more_folders = folder_count - 3  # Calculate first
                response_parts.append(f"  ... and {more_folders} more folders")
        
        # Show files (limit to 5)
        if results['files']:
            file_count = len(results['files'])  # Define variable first
            response_parts.append(f"\n📄 FILES ({file_count}):")
            for i, file_path in enumerate(results['files'][:5]):
                file_name = os.path.basename(file_path)
                parent_dir = os.path.basename(os.path.dirname(file_path))
                response_parts.append(f"  • {file_name} (in {parent_dir})")
            if file_count > 5:
                more_files = file_count - 5  # Calculate first
                response_parts.append(f"  ... and {more_files} more files")
                
        return "\n".join(response_parts), ""