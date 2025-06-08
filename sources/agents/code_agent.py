import platform, os
import asyncio
import subprocess
import tempfile
from pathlib import Path

from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent, executorResult
from sources.tools.C_Interpreter import CInterpreter
from sources.tools.GoInterpreter import GoInterpreter
from sources.tools.PyInterpreter import PyInterpreter
from sources.tools.BashInterpreter import BashInterpreter
from sources.tools.JavaInterpreter import JavaInterpreter
from sources.tools.fileFinder import FileFinder
from sources.logger import Logger
from sources.memory import Memory

class CoderAgent(Agent):
    """
    The code agent is an agent that can write and execute code.
    Enhanced to support opening external editors.
    """
    def __init__(self, name, prompt_path, provider, verbose=False):
        super().__init__(name, prompt_path, provider, verbose, None)
        self.tools = {
            "bash": BashInterpreter(),
            "python": PyInterpreter(),
            "c": CInterpreter(),
            "go": GoInterpreter(),
            "java": JavaInterpreter(),
            "file_finder": FileFinder()
        }
        self.work_dir = self.tools["file_finder"].get_work_dir()
        self.role = "code"
        self.type = "code_agent"
        self.logger = Logger("code_agent.log")
        self.memory = Memory(self.load_prompt(prompt_path),
                        recover_last_session=False,
                        memory_compression=False,
                        model_provider=provider.get_model_name())
        
        # Editor preferences
        self.editors = {
            "vscode": ["code", "-n", "-w"],  # -n: new window, -w: wait
            "notepad++": ["notepad++"],
            "notepad": ["notepad.exe"]
        }
        self.preferred_editor = self.detect_available_editor()
    
    def detect_available_editor(self):
        """Detect which editor is available on the system."""
        if platform.system() == "Windows":
            # Try VS Code first
            try:
                subprocess.run(["code", "--version"], capture_output=True, check=True)
                return "vscode"
            except:
                pass
            
            # Try Notepad++
            try:
                subprocess.run(["notepad++", "--help"], capture_output=True, check=True)
                return "notepad++"
            except:
                pass
            
            # Fallback to notepad
            return "notepad"
        else:
            # For Linux/Mac, try VS Code
            try:
                subprocess.run(["code", "--version"], capture_output=True, check=True)
                return "vscode"
            except:
                return None
    
    def open_in_editor(self, code_content, file_extension=".py", filename=None):
        """Open code in external editor."""
        # Save directly to workspace folder
        work_path = Path(self.work_dir)
        
        if filename:
            # Use provided filename
            temp_file = work_path / filename
        else:
            # Generate a meaningful filename based on content
            if "calculator" in code_content.lower():
                base_name = "calculator"
            elif "def " in code_content:
                # Try to extract function name
                import re
                match = re.search(r'def\s+(\w+)', code_content)
                base_name = match.group(1) if match else "script"
            else:
                base_name = "script"
            
            # Add timestamp to avoid overwriting
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = work_path / f"{base_name}_{timestamp}{file_extension}"
        
        # Write code to file
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        pretty_print(f"Opening code in {self.preferred_editor}...", color="info")
        
        # Open in editor
        if self.preferred_editor and self.preferred_editor in self.editors:
            cmd = self.editors[self.preferred_editor] + [str(temp_file)]
            try:
                if self.preferred_editor == "vscode":
                    # For VS Code, open in new window
                    subprocess.Popen(["code", "-n", str(temp_file)])
                    pretty_print(f"Code opened in VS Code at: {temp_file}", color="success")
                else:
                    subprocess.Popen(cmd)
                    pretty_print(f"Code opened in {self.preferred_editor} at: {temp_file}", color="success")
                return True, str(temp_file)
            except Exception as e:
                pretty_print(f"Failed to open editor: {e}", color="failure")
                return False, None
        
        return False, None
    
    def open_terminal_for_execution(self, filepath, language="python"):
        """Open a new terminal window for code execution."""
        if platform.system() == "Windows":
            if language == "python":
                # Windows Terminal or CMD
                cmd = f'start cmd /k "cd /d {self.work_dir} && python {filepath} && pause"'
            else:
                cmd = f'start cmd /k "cd /d {self.work_dir} && {filepath} && pause"'
            subprocess.Popen(cmd, shell=True)
        elif platform.system() == "Darwin":  # macOS
            # Open Terminal app
            script = f'tell app "Terminal" to do script "cd {self.work_dir} && python {filepath}"'
            subprocess.Popen(["osascript", "-e", script])
        else:  # Linux
            # Try common terminal emulators
            terminals = ["gnome-terminal", "konsole", "xterm"]
            for term in terminals:
                try:
                    if term == "gnome-terminal":
                        subprocess.Popen([term, "--", "bash", "-c", f"cd {self.work_dir} && python {filepath}; read -p 'Press enter to close'"])
                    else:
                        subprocess.Popen([term, "-e", f"bash -c 'cd {self.work_dir} && python {filepath}; read -p \"Press enter to close\"'"])
                    break
                except:
                    continue
    
    def extract_code_blocks(self, text):
        """Extract code blocks from the response."""
        import re
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        code_blocks = []
        for match in matches:
            language = match[0] if match[0] else 'python'
            code = match[1].strip()
            code_blocks.append((language, code))
        
        return code_blocks
    
    def add_sys_info_prompt(self, prompt):
        """Add system information to the prompt."""
        info = f"System Info:\n" \
               f"OS: {platform.system()} {platform.release()}\n" \
               f"Python Version: {platform.python_version()}\n" \
               f"Available Editor: {self.preferred_editor}\n" \
               f"\nYou must save file at root directory: {self.work_dir}"
        return f"{prompt}\n\n{info}"

    async def process(self, prompt, speech_module) -> str:
        """Process user request with option to open in editor."""
        answer = ""
        attempt = 0
        max_attempts = 5
        prompt = self.add_sys_info_prompt(prompt)
        
        # Check if user wants to open in editor
        open_editor = any(keyword in prompt.lower() for keyword in 
                         ["open in", "use editor", "notepad", "vs code", "vscode", "open editor"])
        
        self.memory.push('user', prompt)
        clarify_trigger = "REQUEST_CLARIFICATION"

        while attempt < max_attempts and not self.stop:
            animate_thinking("Thinking...", color="status")
            await self.wait_message(speech_module)
            answer, reasoning = await self.llm_request()
            self.last_reasoning = reasoning
            
            if clarify_trigger in answer:
                self.last_answer = answer
                await asyncio.sleep(0)
                return answer, reasoning
            
            # Extract code blocks
            code_blocks = self.extract_code_blocks(answer)
            
            if code_blocks and (open_editor or len(code_blocks[0][1]) > 50):
                # Open in editor for longer code or if requested
                for language, code in code_blocks:
                    file_ext = {
                        'python': '.py',
                        'javascript': '.js',
                        'java': '.java',
                        'c': '.c',
                        'cpp': '.cpp',
                        'go': '.go',
                        'bash': '.sh'
                    }.get(language.lower(), '.txt')
                    
                    success, filepath = self.open_in_editor(code, file_ext)
                    if success:
                        answer += f"\n\nCode has been opened in {self.preferred_editor}."
                        answer += f"\nFile location: {filepath}"
                        answer += "\n\nYou can edit and save the file. Would you like me to execute it?"
                        
                        # Ask if user wants to open terminal too
                        if "terminal" in prompt.lower() or "run" in prompt.lower():
                            self.open_terminal_for_execution(filepath, language)
                            answer += "\n\nAlso opened a new terminal window for execution."
            
            if not "```" in answer or open_editor:
                self.last_answer = answer
                await asyncio.sleep(0)
                break
            
            # Original execution logic for shorter code
            self.show_answer()
            animate_thinking("Executing code...", color="status")
            self.status_message = "Executing code..."
            self.logger.info(f"Attempt {attempt + 1}:\n{answer}")
            exec_success, feedback = self.execute_modules(answer)
            self.logger.info(f"Execution result: {exec_success}")
            answer = self.remove_blocks(answer)
            self.last_answer = answer
            await asyncio.sleep(0)
            
            if exec_success and self.get_last_tool_type() != "bash":
                break
            
            pretty_print(f"Execution failure:\n{feedback}", color="failure")
            pretty_print("Correcting code...", color="status")
            self.status_message = "Correcting code..."
            attempt += 1
        
        self.status_message = "Ready"
        if attempt == max_attempts:
            return "I'm sorry, I couldn't find a solution to your problem. How would you like me to proceed?", reasoning
        
        self.last_answer = answer
        return answer, reasoning

if __name__ == "__main__":
    pass