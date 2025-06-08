# enhanced_file_agent.py
"""
Enhanced File Agent that can open Windows Explorer and show files
"""

import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
import asyncio

from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent
from sources.tools.fileFinder import FileFinder
from sources.logger import Logger
from sources.memory import Memory

class FileAgent(Agent):
    """
    Enhanced File Agent that can find files and show them in Explorer
    """
    def __init__(self, name, prompt_path, provider, verbose=False):
        super().__init__(name, prompt_path, provider, verbose, None)
        self.tools = {
            "file_finder": FileFinder()
        }
        self.role = "files"
        self.type = "file_agent"
        self.logger = Logger("file_agent.log")
        self.memory = Memory(self.load_prompt(prompt_path),
                        recover_last_session=False,
                        memory_compression=False,
                        model_provider=provider.get_model_name())
    
    def open_in_explorer(self, file_path):
        """Open Windows Explorer and highlight the specific file"""
        try:
            if platform.system() == "Windows":
                # Open Explorer and select the file
                subprocess.run(['explorer', '/select,', str(file_path)])
                return True, f"Opened Explorer showing: {file_path}"
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', '-R', str(file_path)])
                return True, f"Opened Finder showing: {file_path}"
            else:  # Linux
                # Try to open file manager (works for most distros)
                parent_dir = os.path.dirname(file_path)
                subprocess.run(['xdg-open', parent_dir])
                return True, f"Opened file manager at: {parent_dir}"
        except Exception as e:
            return False, f"Could not open file manager: {str(e)}"
    
    def find_most_recent_file(self, files):
        """Find the most recently modified file from a list"""
        if not files:
            return None
        
        most_recent = None
        latest_time = 0
        
        for file_path in files:
            try:
                mod_time = os.path.getmtime(file_path)
                if mod_time > latest_time:
                    latest_time = mod_time
                    most_recent = file_path
            except:
                continue
        
        return most_recent
    
    def extract_search_params(self, prompt):
        """Extract search parameters from user prompt"""
        search_params = {
            "pattern": None,
            "show_in_explorer": False,
            "find_recent": False
        }
        
        prompt_lower = prompt.lower()
        
        # Check if user wants to see in explorer
        explorer_keywords = ["show", "open", "explorer", "finder", "locate", "where"]
        search_params["show_in_explorer"] = any(kw in prompt_lower for kw in explorer_keywords)
        
        # Check if user wants most recent
        recent_keywords = ["recent", "latest", "newest", "last"]
        search_params["find_recent"] = any(kw in prompt_lower for kw in recent_keywords)
        
        # Extract file pattern
        if "resume" in prompt_lower:
            search_params["pattern"] = ["*resume*", "*cv*", "*curriculum*"]
        elif "document" in prompt_lower or "doc" in prompt_lower:
            search_params["pattern"] = ["*.doc*", "*.pdf", "*.txt"]
        elif "image" in prompt_lower or "photo" in prompt_lower:
            search_params["pattern"] = ["*.jpg", "*.png", "*.jpeg", "*.gif", "*.bmp"]
        elif "video" in prompt_lower:
            search_params["pattern"] = ["*.mp4", "*.avi", "*.mov", "*.mkv"]
        else:
            # Try to extract filename from prompt
            words = prompt.split()
            for word in words:
                if "." in word or len(word) > 3:
                    search_params["pattern"] = [f"*{word}*"]
                    break
        
        return search_params
    
    async def process(self, prompt, speech_module) -> str:
        """Process file-related requests with Explorer integration"""
        animate_thinking("Analyzing your file request...", color="status")
        self.status_message = "Analyzing request..."
        
        # Extract search parameters
        params = self.extract_search_params(prompt)
        
        if not params["pattern"]:
            self.status_message = "Ready"
            return "I need more specific information about what file you're looking for. Could you specify the file name or type?", ""
        
        # Announce search via Nina
        if speech_module:
            search_announcement = f"Searching for {params['pattern'][0].replace('*', '')} files..."
            if params["find_recent"]:
                search_announcement = f"Looking for your most recent {params['pattern'][0].replace('*', '')}..."
            # This will be spoken by Nina through the Speech integration
        
        animate_thinking("Searching for files...", color="status")
        self.status_message = "Searching files..."
        
        # Search for files
        found_files = []
        for pattern in params["pattern"]:
            self.memory.push('user', f"Find files matching {pattern}")
            answer, reasoning = await self.llm_request()
            
            # Execute file search
            if "```" in answer:
                exec_success, result = self.execute_modules(answer)
                if exec_success and result:
                    # Extract file paths from result
                    if isinstance(result, list):
                        found_files.extend(result)
                    elif isinstance(result, str):
                        # Parse file paths from string output
                        lines = result.strip().split('\n')
                        for line in lines:
                            if os.path.exists(line.strip()):
                                found_files.append(line.strip())
        
        # Remove duplicates
        found_files = list(set(found_files))
        
        if not found_files:
            self.status_message = "Ready"
            return f"I couldn't find any files matching '{params['pattern'][0]}'. Would you like me to search in a different location or with different criteria?", ""
        
        # Build response
        response = f"I found {len(found_files)} file(s):\n\n"
        
        # If user wants most recent, find it
        target_file = None
        if params["find_recent"] and len(found_files) > 1:
            target_file = self.find_most_recent_file(found_files)
            if target_file:
                mod_time = datetime.fromtimestamp(os.path.getmtime(target_file))
                response = f"I found your most recent file:\n\n"
                response += f"📄 {os.path.basename(target_file)}\n"
                response += f"📍 Location: {target_file}\n"
                response += f"📅 Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        else:
            # List all files
            for i, file_path in enumerate(found_files[:10]):  # Limit to 10 files
                try:
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    size = os.path.getsize(file_path)
                    size_str = f"{size:,} bytes" if size < 1024*1024 else f"{size/(1024*1024):.1f} MB"
                    
                    response += f"{i+1}. 📄 {os.path.basename(file_path)}\n"
                    response += f"   📍 {file_path}\n"
                    response += f"   📅 Modified: {mod_time.strftime('%Y-%m-%d %H:%M')}\n"
                    response += f"   📊 Size: {size_str}\n\n"
                    
                    if i == 0:
                        target_file = file_path
                except:
                    continue
            
            if len(found_files) > 10:
                response += f"\n... and {len(found_files) - 10} more files."
        
        # Open in Explorer if requested
        if params["show_in_explorer"] and target_file:
            animate_thinking("Opening Explorer...", color="status")
            success, explorer_msg = self.open_in_explorer(target_file)
            if success:
                response += f"\n\n✅ {explorer_msg}"
                if speech_module:
                    # Nina will say this through the Speech integration
                    pass
            else:
                response += f"\n\n❌ {explorer_msg}"
        
        self.status_message = "Ready"
        self.last_answer = response
        await asyncio.sleep(0)
        
        return response, f"Found {len(found_files)} files matching the search criteria."

if __name__ == "__main__":
    pass