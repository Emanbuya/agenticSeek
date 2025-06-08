"""
Nina LLM Switcher
Allows Nina to switch between different LLMs on command
"""

import subprocess
import json
from pathlib import Path


class LLMSwitcher:
    """Manage and switch between different LLMs"""
    
    def __init__(self, nina):
        self.nina = nina
        self.current_model = nina.config.get('MAIN', 'provider_model')
        self.default_model = self.current_model
        
        # Define available models and their purposes
        self.models = {
            'default': {
                'name': self.default_model,
                'description': 'General purpose model',
                'aliases': ['default', 'normal', 'regular', 'mistral']
            },
            'coder': {
                'name': 'deepseek-coder:6.7b',
                'description': 'Specialized for coding tasks',
                'aliases': ['coder', 'deepseek', 'code', 'programming', 'developer']
            },
            'codellama': {
                'name': 'codellama:7b-instruct',
                'description': 'Code generation and analysis',
                'aliases': ['codellama', 'llama', 'meta']
            },
            'fast': {
                'name': 'phi3:mini',
                'description': 'Fast responses for simple tasks',
                'aliases': ['fast', 'quick', 'phi', 'mini']
            },
            'creative': {
                'name': 'llama2:13b',
                'description': 'Creative writing and complex reasoning',
                'aliases': ['creative', 'large', 'big', 'llama2']
            }
        }
        
        # Check which models are actually installed
        self.installed_models = self.check_installed_models()
        
    def check_installed_models(self):
        """Check which models are installed in Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                installed = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        installed.append(model_name)
                return installed
            else:
                print("Could not check installed models")
                return []
                
        except Exception as e:
            print(f"Error checking models: {e}")
            return []
    
    def switch_model(self, model_key):
        """Switch to a different model"""
        model_info = None
        
        # Find the model by alias
        for key, info in self.models.items():
            if model_key.lower() in info['aliases']:
                model_info = info
                break
                
        if not model_info:
            return False, f"I don't recognize the model '{model_key}'. Available options are: {', '.join(self.models.keys())}"
            
        model_name = model_info['name']
        
        # Check if model is installed
        if model_name not in self.installed_models and not any(model_name in m for m in self.installed_models):
            return False, f"The {model_name} model is not installed. Would you like me to install it?"
            
        # Update the provider with new model
        try:
            self.nina.provider.model = model_name
            self.current_model = model_name
            
            # Update all agents to use new model
            for agent in self.nina.agents:
                if hasattr(agent, 'llm'):
                    agent.llm.model = model_name
                    
            return True, f"Switched to {model_name} - {model_info['description']}"
            
        except Exception as e:
            return False, f"Error switching models: {str(e)}"
    
    def install_model(self, model_name):
        """Install a new model using Ollama"""
        self.nina.speak(f"Installing {model_name}. This may take a few minutes...")
        
        try:
            # Run ollama pull command
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    
            if process.returncode == 0:
                self.installed_models = self.check_installed_models()
                return True, f"Successfully installed {model_name}"
            else:
                return False, f"Failed to install {model_name}"
                
        except Exception as e:
            return False, f"Error installing model: {str(e)}"
    
    def list_models(self):
        """List available models and their status"""
        response = "Available models:\n"
        
        for key, info in self.models.items():
            model_name = info['name']
            status = "✅ Installed" if model_name in self.installed_models or any(model_name in m for m in self.installed_models) else "❌ Not installed"
            current = " (current)" if model_name == self.current_model else ""
            
            response += f"- {key}: {model_name} - {info['description']} {status}{current}\n"
            
        return response
    
    def get_current_model(self):
        """Get the current model name"""
        return self.current_model


def add_llm_switching_to_nina(nina):
    """Add LLM switching capabilities to Nina"""
    
    # Create switcher instance
    switcher = LLMSwitcher(nina)
    nina.llm_switcher = switcher
    
    # Add to handlers
    if hasattr(nina, 'handlers'):
        
        def handle_llm_switch(command):
            """Handle LLM switching commands"""
            cmd_lower = command.lower()
            
            # List models
            if any(phrase in cmd_lower for phrase in ["list models", "what models", "available models"]):
                response = switcher.list_models()
                nina.speak(response)
                return True
                
            # Switch model
            elif any(phrase in cmd_lower for phrase in ["switch to", "use", "launch", "activate"]):
                # Extract model name
                model_name = None
                
                for key, info in switcher.models.items():
                    for alias in info['aliases']:
                        if alias in cmd_lower:
                            model_name = key
                            break
                    if model_name:
                        break
                        
                if model_name:
                    success, message = switcher.switch_model(model_name)
                    nina.speak(message)
                    
                    if not success and "not installed" in message:
                        nina.speak("Should I install it for you?")
                        # Would need to handle follow-up response
                else:
                    nina.speak("Which model would you like to use? I have coder, creative, fast, or default available.")
                    
                return True
                
            # Install model
            elif "install" in cmd_lower and "model" in cmd_lower:
                # Extract model name
                for key, info in switcher.models.items():
                    if key in cmd_lower or info['name'] in cmd_lower:
                        success, message = switcher.install_model(info['name'])
                        nina.speak(message)
                        return True
                        
                nina.speak("Which model would you like to install?")
                return True
                
            # Current model
            elif any(phrase in cmd_lower for phrase in ["current model", "which model", "what model"]):
                current = switcher.get_current_model()
                nina.speak(f"I'm currently using {current}")
                return True
                
            return False
        
        # Store the handler
        nina.handlers.handle_llm_switch = handle_llm_switch
        
    return nina