# enhanced_file_finder.py
"""
Enhanced File Finder with wildcard drive support
Place this in sources/tools/ directory
"""

import os
import glob
import fnmatch
from pathlib import Path
import configparser
from typing import List, Dict

class EnhancedFileFinder:
    """Enhanced file finder with wildcard and multi-drive support"""
    
    def __init__(self, config_path="nina_personal.ini"):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        
        # Load config if exists
        if os.path.exists(config_path):
            self.config.read(config_path)
            
        # Default search paths
        self.default_paths = [
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Desktop"),
        ]
        
    def get_search_drives(self, drive_group="all_drives"):
        """Get drives to search from config"""
        if self.config.has_option('SEARCH_DRIVES', drive_group):
            drives_str = self.config.get('SEARCH_DRIVES', drive_group)
            return [d.strip() + ":" for d in drives_str.split(',')]
        
        # Default to C drive if not configured
        return ["C:"]
        
    def expand_wildcard_paths(self, pattern, drives=None):
        """Expand wildcard paths across multiple drives"""
        if drives is None:
            drives = self.get_search_drives()
            
        expanded_paths = []
        
        # Check if pattern has {drive} placeholder
        if "{drive}" in pattern:
            for drive in drives:
                expanded_pattern = pattern.replace("{drive}", drive)
                # Use glob to expand wildcards
                try:
                    matches = glob.glob(expanded_pattern, recursive=True)
                    expanded_paths.extend(matches)
                except:
                    pass
        else:
            # No drive placeholder, use pattern as-is
            try:
                matches = glob.glob(pattern, recursive=True)
                expanded_paths.extend(matches)
            except:
                pass
                
        return expanded_paths
        
    def search_files(self, filename_pattern, search_type="all_drives", max_results=50):
        """Search for files across configured drives"""
        results = []
        drives = self.get_search_drives(search_type)
        
        print(f"🔍 Searching for '{filename_pattern}' across drives: {drives}")
        
        # Common search locations from config
        search_paths = []
        
        # Add configured search paths
        if self.config.has_section('SEARCH_PATHS'):
            for key, pattern in self.config.items('SEARCH_PATHS'):
                expanded = self.expand_wildcard_paths(pattern, drives)
                search_paths.extend(expanded)
                
        # Add default paths for each drive
        for drive in drives:
            # Common locations
            common_paths = [
                f"{drive}\\",
                f"{drive}\\Users\\*\\Documents",
                f"{drive}\\Users\\*\\Downloads",
                f"{drive}\\Users\\*\\Desktop",
                f"{drive}\\Users\\*\\OneDrive\\Documents",
                f"{drive}\\*\\Projects",
                f"{drive}\\Projects",
            ]
            
            for path_pattern in common_paths:
                try:
                    # Expand wildcards in path
                    for base_path in glob.glob(path_pattern):
                        if os.path.isdir(base_path):
                            search_paths.append(base_path)
                except:
                    pass
                    
        # Remove duplicates
        search_paths = list(set(search_paths))
        
        # Search in each path
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
                
            try:
                # Walk through directory
                for root, dirs, files in os.walk(search_path):
                    # Skip system directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and 
                              d not in ['Windows', 'Program Files', '$Recycle.Bin']]
                    
                    for file in files:
                        if fnmatch.fnmatch(file.lower(), filename_pattern.lower()):
                            full_path = os.path.join(root, file)
                            results.append(full_path)
                            
                            if len(results) >= max_results:
                                return results
                                
            except PermissionError:
                continue
            except Exception as e:
                print(f"Error searching {search_path}: {e}")
                
        return results
        
    def search_folders(self, folder_pattern, search_type="all_drives", max_results=20):
        """Search for folders across configured drives"""
        results = []
        drives = self.get_search_drives(search_type)
        
        print(f"📁 Searching for folder '{folder_pattern}' across drives: {drives}")
        
        for drive in drives:
            # Common folder locations
            search_roots = [
                f"{drive}\\",
                f"{drive}\\Users",
                f"{drive}\\Program Files",
                f"{drive}\\Program Files (x86)",
            ]
            
            for root_path in search_roots:
                if not os.path.exists(root_path):
                    continue
                    
                try:
                    for root, dirs, files in os.walk(root_path):
                        # Check current directory name
                        if fnmatch.fnmatch(os.path.basename(root).lower(), folder_pattern.lower()):
                            results.append(root)
                            if len(results) >= max_results:
                                return results
                                
                        # Check subdirectories
                        for dir_name in dirs:
                            if fnmatch.fnmatch(dir_name.lower(), folder_pattern.lower()):
                                full_path = os.path.join(root, dir_name)
                                results.append(full_path)
                                
                                if len(results) >= max_results:
                                    return results
                                    
                        # Don't go too deep
                        if root.count(os.sep) > 5:
                            dirs.clear()
                            
                except PermissionError:
                    continue
                except Exception:
                    continue
                    
        return results
        
    def quick_search(self, query):
        """Quick search based on query type"""
        query_lower = query.lower()
        
        # Determine what to search for
        if any(ext in query_lower for ext in ['.pdf', '.doc', '.txt', '.xlsx']):
            # File search
            pattern = f"*{query}*" if not any(c in query for c in ['*', '?']) else query
            return self.search_files(pattern)
            
        elif "folder" in query_lower or "directory" in query_lower:
            # Folder search
            # Extract folder name from query
            words = query_lower.replace("folder", "").replace("directory", "").strip().split()
            if words:
                pattern = f"*{words[0]}*"
                return self.search_folders(pattern)
                
        else:
            # Try both files and folders
            pattern = f"*{query}*"
            files = self.search_files(pattern, max_results=25)
            folders = self.search_folders(pattern, max_results=10)
            return files + folders