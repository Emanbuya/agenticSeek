import asyncio
import os
from pathlib import Path
from typing import List, Dict, Tuple

from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent
from sources.tools.fileFinder import FileFinder
from sources.tools.BashInterpreter import BashInterpreter
from sources.memory import Memory
from sources.logger import Logger


class FileAgent(Agent):
    """
    Nina's File Management Module - Safe Version
    Always asks for confirmation before any destructive operations
    Can search multiple directories and understands natural language paths
    """
    
    def __init__(self, name, prompt_path, provider, verbose=False):
        """Initialize Nina's file management capabilities"""
        super().__init__(name, prompt_path, provider, verbose, None)
        
        # Initialize tools
        self.tools = {
            "file_finder": FileFinder(),
            "bash": BashInterpreter()
        }
        
        # Set up directories
        self.work_dir = self.tools["file_finder"].get_work_dir()
        self.role = "files"
        self.type = "file_agent"
        self.logger = Logger("nina_files.log")
        
        # Initialize memory
        self.memory = Memory(
            self.load_prompt(prompt_path),
            recover_last_session=False,
            memory_compression=False,
            model_provider=provider.get_model_name()
        )
        
        # Safety settings
        self.require_confirmation = True
        self.pending_operation = None
        self.destructive_commands = [
            'rm', 'del', 'delete', 'move', 'mv', 'copy', 'cp', 
            'rename', 'mkdir', 'rmdir', 'touch', 'write', '>', '>>'
        ]
        
        # Common directory mappings
        self.directory_aliases = self._setup_directory_aliases()
    
    def _setup_directory_aliases(self) -> Dict[str, str]:
        """Set up common directory aliases for natural language understanding"""
        home = str(Path.home())
        
        aliases = {
            "my documents": str(Path(home) / "Documents"),
            "documents": str(Path(home) / "Documents"),
            "downloads": str(Path(home) / "Downloads"),
            "desktop": str(Path(home) / "Desktop"),
            "pictures": str(Path(home) / "Pictures"),
            "videos": str(Path(home) / "Videos"),
            "music": str(Path(home) / "Music"),
            "home": home,
            "workspace": self.work_dir,
            "nina_workspace": self.work_dir
        }
        
        # Add Windows-specific paths if on Windows
        if os.name == 'nt':
            aliases.update({
                "program files": "C:\\Program Files",
                "program files x86": "C:\\Program Files (x86)",
                "appdata": str(Path(home) / "AppData"),
                "temp": str(Path(home) / "AppData" / "Local" / "Temp")
            })
        
        return aliases
    
    def resolve_directory_path(self, user_input: str) -> str:
        """Resolve natural language directory references to actual paths"""
        input_lower = user_input.lower()
        
        # Check for aliases
        for alias, path in self.directory_aliases.items():
            if alias in input_lower:
                self.logger.info(f"Resolved '{alias}' to '{path}'")
                return input_lower.replace(alias, path)
        
        return user_input
    
    def is_destructive_operation(self, command: str) -> bool:
        """Check if a command is potentially destructive"""
        command_lower = command.lower()
        return any(cmd in command_lower for cmd in self.destructive_commands)
    
    def format_file_list(self, files: List[str], file_type: str = "files") -> str:
        """Format file list for voice-friendly output"""
        if not files:
            return f"No {file_type} found."
        
        count = len(files)
        if count == 1:
            return f"Found 1 {file_type[:-1]}: {files[0]}"
        elif count <= 5:
            return f"Found {count} {file_type}: {', '.join(files)}"
        else:
            first_five = ', '.join(files[:5])
            return f"Found {count} {file_type}. First 5: {first_five}, and {count-5} more."
    
    async def process(self, prompt: str, speech_module) -> Tuple[str, str]:
        """Process file operations with safety confirmations"""
        try:
            # Resolve natural language paths
            resolved_prompt = self.resolve_directory_path(prompt)
            
            # Check if this is a confirmation response
            if self.pending_operation and prompt.lower() in ['yes', 'no', 'confirm', 'cancel']:
                return await self.handle_confirmation(prompt.lower(), speech_module)
            
            # Analyze the request
            operation_type = self.analyze_operation(resolved_prompt)
            
            # Handle different operation types
            if operation_type == "search":
                return await self.handle_search(resolved_prompt)
            elif operation_type == "list":
                return await self.handle_list(resolved_prompt)
            elif operation_type == "info":
                return await self.handle_info(resolved_prompt)
            else:
                # For potentially destructive operations
                return await self.handle_with_confirmation(resolved_prompt, speech_module)
        
        except Exception as e:
            self.logger.error(f"Error in file operation: {e}")
            return f"I encountered an error with that file operation: {str(e)}", ""
    
    def analyze_operation(self, prompt: str) -> str:
        """Analyze what type of file operation is being requested"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['find', 'search', 'look for', 'locate']):
            return "search"
        elif any(word in prompt_lower for word in ['list', 'show', 'display', 'what']):
            return "list"
        elif any(word in prompt_lower for word in ['info', 'details', 'properties', 'size']):
            return "info"
        else:
            return "modify"
    
    async def handle_search(self, prompt: str) -> Tuple[str, str]:
        """Handle file search operations"""
        # Extract search parameters
        search_prompt = f"""Analyze this request and extract:
1. File type/extension (e.g., pdf, txt, all files)
2. Directory to search in
3. Any name patterns

Request: {prompt}

Respond in format:
Type: [file type]
Directory: [path]
Pattern: [optional pattern]"""
        
        self.memory.clear()
        self.memory.push('user', search_prompt)
        params, _ = await self.llm_request()
        
        # Execute search
        try:
            # Parse parameters and perform search
            # This is simplified - you'd parse the LLM response properly
            if "pdf" in prompt.lower():
                ext = ".pdf"
            elif "txt" in prompt.lower() or "text" in prompt.lower():
                ext = ".txt"
            else:
                ext = "*"
            
            # Determine directory
            directory = None
            for alias, path in self.directory_aliases.items():
                if alias in prompt.lower():
                    directory = path
                    break
            
            if not directory:
                directory = self.work_dir
            
            # Find files
            files = []
            if os.path.exists(directory):
                for root, dirs, filenames in os.walk(directory):
                    for filename in filenames:
                        if ext == "*" or filename.endswith(ext):
                            files.append(os.path.join(root, filename))
                    # Don't go too deep
                    if len(files) > 100:
                        break
            
            # Format response
            if files:
                response = self.format_file_list([os.path.basename(f) for f in files], 
                                               f"{ext} files" if ext != "*" else "files")
                # Store full paths for potential further operations
                self.last_search_results = files
            else:
                response = f"No files found in {os.path.basename(directory)}."
            
            return response, "Search completed"
            
        except Exception as e:
            return f"Error searching files: {str(e)}", "Search failed"
    
    async def handle_list(self, prompt: str) -> Tuple[str, str]:
        """Handle directory listing operations"""
        # Similar to search but just lists directory contents
        directory = self.work_dir
        
        for alias, path in self.directory_aliases.items():
            if alias in prompt.lower():
                directory = path
                break
        
        try:
            if os.path.exists(directory):
                items = os.listdir(directory)
                dirs = [d for d in items if os.path.isdir(os.path.join(directory, d))]
                files = [f for f in items if os.path.isfile(os.path.join(directory, f))]
                
                response = f"In {os.path.basename(directory)}: "
                if dirs:
                    response += f"{len(dirs)} folders"
                if files:
                    if dirs:
                        response += f" and "
                    response += f"{len(files)} files"
                
                if not dirs and not files:
                    response = f"{os.path.basename(directory)} is empty."
                
                return response, "List completed"
            else:
                return f"Directory {directory} not found.", "List failed"
                
        except Exception as e:
            return f"Error listing directory: {str(e)}", "List failed"
    
    async def handle_info(self, prompt: str) -> Tuple[str, str]:
        """Handle file information requests"""
        # Get file size, modified date, etc.
        return "File info feature coming soon.", "Info request"
    
    async def handle_with_confirmation(self, prompt: str, speech_module) -> Tuple[str, str]:
        """Handle potentially destructive operations with confirmation"""
        # Check if operation is destructive
        if self.is_destructive_operation(prompt):
            # Store pending operation
            self.pending_operation = prompt
            
            # Create confirmation message
            operation_desc = self.describe_operation(prompt)
            confirm_msg = f"You want me to {operation_desc}. This action cannot be undone. Say 'yes' to confirm or 'no' to cancel."
            
            return confirm_msg, "Confirmation required"
        else:
            # Non-destructive operation, execute directly
            return await self.execute_file_operation(prompt, speech_module)
    
    def describe_operation(self, command: str) -> str:
        """Create a human-readable description of the operation"""
        command_lower = command.lower()
        
        if 'delete' in command_lower or 'rm' in command_lower:
            return "delete files"
        elif 'move' in command_lower or 'mv' in command_lower:
            return "move files"
        elif 'copy' in command_lower or 'cp' in command_lower:
            return "copy files"
        elif 'rename' in command_lower:
            return "rename files"
        elif 'mkdir' in command_lower:
            return "create a new directory"
        else:
            return "modify files"
    
    async def handle_confirmation(self, response: str, speech_module) -> Tuple[str, str]:
        """Handle user's confirmation response"""
        if response in ['yes', 'confirm']:
            # Execute the pending operation
            operation = self.pending_operation
            self.pending_operation = None
            return await self.execute_file_operation(operation, speech_module)
        else:
            # Cancel the operation
            self.pending_operation = None
            return "Operation cancelled.", "Cancelled"
    
    async def execute_file_operation(self, prompt: str, speech_module) -> Tuple[str, str]:
        """Execute the actual file operation"""
        # Add safety wrapper
        safe_prompt = f"""Execute this file operation safely: {prompt}
Work directory: {self.work_dir}

Important: 
- Only work within allowed directories
- Provide clear success/failure messages
- Be voice-friendly in responses"""
        
        self.memory.push('user', safe_prompt)
        
        exec_success = False
        while exec_success is False and not self.stop:
            answer, reasoning = await self.llm_request()
            self.last_reasoning = reasoning
            
            # Execute with tools
            exec_success, result = self.execute_modules(answer)
            
            # Clean up response for voice
            answer = self.remove_blocks(answer)
            if len(answer) > 150:
                answer = answer[:150] + "..."
            
            self.last_answer = answer
        
        return answer, reasoning
    
    def remove_blocks(self, text: str) -> str:
        """Remove code blocks and technical markup for voice output"""
        # Remove ``` blocks
        import re
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]+`', '', text)
        # Clean up extra whitespace
        text = ' '.join(text.split())
        return text.strip()