import os, sys
import stat
import mimetypes
import configparser
from pathlib import Path
from typing import List, Dict, Optional

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sources.tools.tools import Tools

class FileFinder(Tools):
    """
    Enhanced File Finder for Nina - understands natural language paths
    """
    def __init__(self):
        super().__init__()
        self.tag = "file_finder"
        self.name = "File Finder"
        self.description = "Finds files across common directories with natural language support"
        
        # Set up natural language directory mappings
        self.setup_directory_aliases()
    
    def setup_directory_aliases(self):
        """Set up common directory aliases for natural language understanding"""
        home = str(Path.home())
        
        self.directory_aliases = {
            "my documents": str(Path(home) / "Documents"),
            "documents": str(Path(home) / "Documents"),
            "downloads": str(Path(home) / "Downloads"),
            "desktop": str(Path(home) / "Desktop"),
            "pictures": str(Path(home) / "Pictures"),
            "videos": str(Path(home) / "Videos"),
            "music": str(Path(home) / "Music"),
            "home": home,
            "workspace": self.work_dir,
            "nina_workspace": self.work_dir,
            "current": os.getcwd(),
        }
        
        # Add Windows-specific paths
        if os.name == 'nt':
            self.directory_aliases.update({
                "program files": "C:\\Program Files",
                "program files x86": "C:\\Program Files (x86)",
                "appdata": str(Path(home) / "AppData"),
                "temp": str(Path(home) / "AppData" / "Local" / "Temp"),
                "c drive": "C:\\",
                "c:": "C:\\",
            })
    
    def resolve_directory(self, user_input: str) -> str:
        """Resolve natural language directory references to actual paths"""
        if not user_input:
            return self.work_dir
            
        input_lower = user_input.lower().strip()
        
        # Check for exact alias matches
        for alias, path in self.directory_aliases.items():
            if alias in input_lower:
                return path
        
        # Check if it's already a valid path
        if os.path.exists(user_input):
            return user_input
            
        # Default to workspace
        return self.work_dir
    
    def read_file(self, file_path: str) -> str:
        """Reads the content of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        except Exception as e:
            return f"Error reading file: {e}"
    
    def read_arbitrary_file(self, file_path: str, file_type: str) -> str:
        """Reads the content of a file with appropriate handling for different types."""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith(('image/', 'video/', 'audio/')):
                return "can't read file type: image, video, or audio files are not supported."
        
        if "text" in str(file_type):
            content = self.read_file(file_path)
        elif "pdf" in str(file_type).lower():
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                content = '\n'.join([page.extract_text() for page in reader.pages])
            except:
                content = "Error: Could not read PDF file"
        else:
            content = self.read_file(file_path)
        
        return content
    
    def get_file_info(self, file_path: str) -> Dict:
        """Gets detailed information about a file."""
        if os.path.exists(file_path):
            stats = os.stat(file_path)
            permissions = oct(stat.S_IMODE(stats.st_mode))
            file_type, _ = mimetypes.guess_type(file_path)
            file_type = file_type if file_type else "Unknown"
            
            # Get file size in human readable format
            size = stats.st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    size_str = f"{size:.1f} {unit}"
                    break
                size /= 1024.0
            else:
                size_str = f"{size:.1f} TB"
            
            result = {
                "filename": os.path.basename(file_path),
                "path": file_path,
                "type": file_type,
                "size": size_str,
                "permissions": permissions
            }
            return result
        else:
            return {"filename": file_path, "error": "File not found"}
    
    def search_files(self, directory: str, pattern: str = "*", file_type: str = None, 
                    max_results: int = 50) -> List[str]:
        """
        Search for files matching pattern in directory
        Args:
            directory: Directory to search in
            pattern: File pattern to match (e.g., "*.pdf", "report*")
            file_type: Optional file type filter
            max_results: Maximum number of results to return
        """
        results = []
        excluded = ['.git', '__pycache__', 'node_modules', '.vs', '.idea']
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip excluded directories
                dirs[:] = [d for d in dirs if d not in excluded]
                
                for file in files:
                    if len(results) >= max_results:
                        return results
                    
                    # Check pattern match
                    if pattern == "*" or pattern in file.lower():
                        if file_type:
                            if file.lower().endswith(f".{file_type.lower()}"):
                                results.append(os.path.join(root, file))
                        else:
                            results.append(os.path.join(root, file))
        except PermissionError:
            pass  # Skip directories we can't access
        
        return results
    
    def list_directory(self, directory: str) -> Dict[str, List[str]]:
        """List contents of a directory"""
        try:
            items = os.listdir(directory)
            dirs = [d for d in items if os.path.isdir(os.path.join(directory, d))]
            files = [f for f in items if os.path.isfile(os.path.join(directory, f))]
            
            return {
                "directories": sorted(dirs),
                "files": sorted(files),
                "total": len(items)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def execute(self, blocks: list, safety: bool = False) -> str:
        """
        Execute file operations based on natural language commands
        """
        if not blocks or not isinstance(blocks, list):
            return "Error: No valid commands provided"
        
        output = ""
        
        for block in blocks:
            # Extract parameters
            action = self.get_parameter_value(block, "action") or "search"
            name = self.get_parameter_value(block, "name") or "*"
            directory = self.get_parameter_value(block, "directory") or ""
            file_type = self.get_parameter_value(block, "type")
            
            # Resolve natural language directory
            search_dir = self.resolve_directory(directory)
            
            if action == "list":
                # List directory contents
                result = self.list_directory(search_dir)
                if "error" in result:
                    output += f"Error listing {search_dir}: {result['error']}\n"
                else:
                    output += f"Contents of {os.path.basename(search_dir)}:\n"
                    output += f"  Folders: {len(result['directories'])}\n"
                    output += f"  Files: {len(result['files'])}\n"
                    if result['files']:
                        output += f"  First 10 files: {', '.join(result['files'][:10])}\n"
            
            elif action == "search" or action == "find":
                # Search for files
                if file_type:
                    name = f"*.{file_type}"
                
                files = self.search_files(search_dir, name, file_type)
                
                if files:
                    output += f"Found {len(files)} matching files:\n"
                    for file in files[:10]:  # Show first 10
                        output += f"  - {os.path.basename(file)} ({os.path.dirname(file)})\n"
                    if len(files) > 10:
                        output += f"  ... and {len(files) - 10} more\n"
                else:
                    output += f"No files found matching '{name}' in {os.path.basename(search_dir)}\n"
            
            elif action == "info":
                # Get file info
                file_path = self.search_files(search_dir, name, file_type, max_results=1)
                if file_path:
                    info = self.get_file_info(file_path[0])
                    output += f"File: {info['filename']}\n"
                    output += f"  Path: {info['path']}\n"
                    output += f"  Type: {info['type']}\n"
                    output += f"  Size: {info['size']}\n"
                else:
                    output += f"File '{name}' not found\n"
            
            elif action == "read":
                # Read file content
                file_path = self.search_files(search_dir, name, file_type, max_results=1)
                if file_path:
                    content = self.read_arbitrary_file(file_path[0], file_type or "text")
                    output += f"Content of {os.path.basename(file_path[0])}:\n{content[:500]}...\n"
                else:
                    output += f"File '{name}' not found\n"
        
        return output.strip()
    
    def execution_failure_check(self, output: str) -> bool:
        """Check if the operation failed"""
        if not output:
            return True
        failure_indicators = ["Error", "not found", "Failed"]
        return any(indicator in output for indicator in failure_indicators)
    
    def interpreter_feedback(self, output: str) -> str:
        """Provide feedback about the operation"""
        if not output:
            return "No output generated"
        
        if self.execution_failure_check(output):
            return f"Operation encountered issues: {output}"
        else:
            return f"Operation successful: {output}"


# Quick utility functions for common operations
def find_pdfs_in_documents():
    """Quick function to find PDFs in Documents folder"""
    finder = FileFinder()
    docs_path = finder.directory_aliases.get("documents", "")
    return finder.search_files(docs_path, "*", "pdf")

def open_explorer(path=None):
    """Open Windows Explorer at specified path"""
    import subprocess
    if path:
        subprocess.Popen(f'explorer "{path}"')
    else:
        subprocess.Popen('explorer')


if __name__ == "__main__":
    # Test the enhanced file finder
    tool = FileFinder()
    
    # Test natural language directory resolution
    print("Testing directory aliases:")
    print(f"'my documents' resolves to: {tool.resolve_directory('my documents')}")
    print(f"'downloads' resolves to: {tool.resolve_directory('downloads')}")
    
    # Test file search
    result = tool.execute(["""
action=search
directory=my documents
type=pdf
"""], False)
    print("\nSearch result:")
    print(result)