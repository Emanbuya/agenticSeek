"""
Nina Intern Mode
Train Nina to do your work by watching and learning
"""

import json
import os
from datetime import datetime
import threading
import queue
from pathlib import Path
import pickle
import time

class InternTraining:
    """Train Nina to be an AI intern by observing your work"""
    
    def __init__(self, nina, vision):
        self.nina = nina
        self.vision = vision
        self.training_data = []
        self.current_session = None
        self.recording = False
        self.training_dir = Path("nina_training")
        self.training_dir.mkdir(exist_ok=True)
        
    def start_training_session(self, task_name):
        """Start recording a training session"""
        self.current_session = {
            'task': task_name,
            'started': datetime.now().isoformat(),
            'actions': [],
            'screenshots': [],
            'narration': []
        }
        self.recording = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_screen)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.nina.speak(f"Starting training session for: {task_name}. I'll watch and learn what you do.")
        
    def stop_training_session(self):
        """Stop recording and save session"""
        self.recording = False
        if self.current_session:
            self.current_session['ended'] = datetime.now().isoformat()
            
            # Save session
            session_file = self.training_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(session_file, 'w') as f:
                json.dump(self.current_session, f, indent=2)
            
            self.nina.speak(f"Training session saved. I recorded {len(self.current_session['actions'])} actions.")
            self.current_session = None
    
    def _monitor_screen(self):
        """Monitor screen during training"""
        import pyautogui
        import mouse
        import keyboard
        
        last_mouse_pos = None
        
        while self.recording:
            try:
                # Capture mouse position
                current_mouse = pyautogui.position()
                
                # Record mouse clicks
                if mouse.is_pressed():
                    action = {
                        'type': 'click',
                        'position': (current_mouse.x, current_mouse.y),
                        'timestamp': datetime.now().isoformat(),
                        'window': self.vision.capture_active_window()[1]
                    }
                    self.current_session['actions'].append(action)
                
                # Capture periodic screenshots
                if len(self.current_session['screenshots']) == 0 or \
                   (datetime.now() - datetime.fromisoformat(self.current_session['screenshots'][-1]['timestamp'])).seconds > 5:
                    
                    screenshot = self.vision.capture_screen()
                    screenshot_data = {
                        'timestamp': datetime.now().isoformat(),
                        'text_content': self.vision.get_text_from_screen(screenshot),
                        'window': self.vision.capture_active_window()[1]
                    }
                    self.current_session['screenshots'].append(screenshot_data)
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
    
    def add_narration(self, narration):
        """Add voice narration to explain what you're doing"""
        if self.recording and self.current_session:
            self.current_session['narration'].append({
                'text': narration,
                'timestamp': datetime.now().isoformat()
            })
            print(f"📝 Narration added: {narration}")
    
    def learn_task_pattern(self, task_name):
        """Analyze training sessions to learn task patterns"""
        sessions = []
        
        # Load all sessions for this task
        for session_file in self.training_dir.glob("session_*.json"):
            with open(session_file, 'r') as f:
                session = json.load(f)
                if session['task'] == task_name:
                    sessions.append(session)
        
        if not sessions:
            return None
        
        # Extract patterns
        pattern = {
            'task': task_name,
            'common_actions': self._extract_common_actions(sessions),
            'typical_windows': self._extract_typical_windows(sessions),
            'key_phrases': self._extract_key_phrases(sessions),
            'workflow': self._build_workflow(sessions)
        }
        
        return pattern
    
    def _extract_common_actions(self, sessions):
        """Find common action patterns across sessions"""
        all_actions = []
        for session in sessions:
            all_actions.extend(session['actions'])
        
        # Group similar actions
        action_patterns = {}
        for action in all_actions:
            key = f"{action['type']}_{action.get('window', 'unknown')}"
            if key not in action_patterns:
                action_patterns[key] = 0
            action_patterns[key] += 1
        
        return action_patterns
    
    def _extract_typical_windows(self, sessions):
        """Find which applications are typically used"""
        windows = set()
        for session in sessions:
            for screenshot in session['screenshots']:
                if screenshot['window']:
                    windows.add(screenshot['window'])
        return list(windows)
    
    def _extract_key_phrases(self, sessions):
        """Extract key phrases from narrations"""
        phrases = []
        for session in sessions:
            for narration in session['narration']:
                phrases.append(narration['text'])
        return phrases
    
    def _build_workflow(self, sessions):
        """Build a workflow from training sessions"""
        # This is simplified - you'd want more sophisticated pattern matching
        workflow_steps = []
        
        for session in sessions:
            steps = []
            current_window = None
            
            for i, action in enumerate(session['actions']):
                window = action.get('window', 'unknown')
                
                # Detect window changes as workflow steps
                if window != current_window:
                    current_window = window
                    
                    # Find narration near this timestamp
                    narration = self._find_nearest_narration(
                        action['timestamp'], 
                        session['narration']
                    )
                    
                    steps.append({
                        'window': window,
                        'narration': narration,
                        'action_type': action['type']
                    })
            
            workflow_steps.append(steps)
        
        return workflow_steps
    
    def _find_nearest_narration(self, timestamp, narrations):
        """Find narration closest to given timestamp"""
        if not narrations:
            return None
            
        action_time = datetime.fromisoformat(timestamp)
        closest = None
        min_diff = float('inf')
        
        for narration in narrations:
            narr_time = datetime.fromisoformat(narration['timestamp'])
            diff = abs((action_time - narr_time).total_seconds())
            
            if diff < min_diff and diff < 30:  # Within 30 seconds
                min_diff = diff
                closest = narration['text']
        
        return closest
    
    def execute_learned_task(self, task_name):
        """Execute a task that Nina has learned"""
        pattern = self.learn_task_pattern(task_name)
        
        if not pattern:
            self.nina.speak(f"I haven't learned how to do '{task_name}' yet. Please train me first.")
            return
        
        self.nina.speak(f"I'll help you with '{task_name}'. I've learned this from {len(pattern['workflow'])} training sessions.")
        
        # Execute the workflow
        # This is where you'd implement the actual automation
        # For now, we'll just describe what Nina would do
        
        steps_description = []
        for workflow in pattern['workflow']:
            for step in workflow:
                if step['narration']:
                    steps_description.append(step['narration'])
                else:
                    steps_description.append(f"Open {step['window']}")
        
        self.nina.speak("Here's what I would do: " + "; ".join(steps_description[:3]))


class CustomerTaskAutomation:
    """Automate tasks for customers based on training"""
    
    def __init__(self, nina, vision, training):
        self.nina = nina
        self.vision = vision
        self.training = training
        self.task_library = self.load_task_library()
        
    def load_task_library(self):
        """Load library of trained tasks"""
        library_path = Path("nina_training") / "task_library.json"
        
        if library_path.exists():
            with open(library_path, 'r') as f:
                return json.load(f)
        else:
            # Default task templates
            return {
                "fill_form": {
                    "description": "Fill out web forms automatically",
                    "steps": ["Locate form fields", "Enter data", "Submit"]
                },
                "process_documents": {
                    "description": "Process Word documents",
                    "steps": ["Open document", "Apply formatting", "Save"]
                },
                "data_entry": {
                    "description": "Enter data into spreadsheets",
                    "steps": ["Open Excel", "Navigate to cells", "Enter data"]
                },
                "email_response": {
                    "description": "Draft email responses",
                    "steps": ["Read email", "Draft response", "Review"]
                }
            }
    
    def list_available_tasks(self):
        """List tasks Nina can do"""
        tasks = []
        for task_name, task_info in self.task_library.items():
            tasks.append(f"{task_name}: {task_info['description']}")
        
        # Add learned tasks
        for session_file in Path("nina_training").glob("session_*.json"):
            with open(session_file, 'r') as f:
                session = json.load(f)
                task = session['task']
                if task not in [t.split(':')[0] for t in tasks]:
                    tasks.append(f"{task}: Learned from your training")
        
        return tasks
    
    def demonstrate_capability(self, task_type):
        """Demonstrate what Nina can do for a specific task"""
        if task_type == "form_filling":
            return self.demo_form_filling()
        elif task_type == "document_processing":
            return self.demo_document_processing()
        elif task_type == "data_entry":
            return self.demo_data_entry()
        else:
            return f"I can help with {task_type}. Train me by showing me how you do it!"
    
    def demo_form_filling(self):
        """Demonstrate form filling capabilities"""
        # Check what's on screen
        content = self.vision.read_document_content()
        
        if content and 'form' in content['text'].lower():
            # Analyze form fields
            self.nina.speak("I can see a form on your screen. I can help fill it out based on the data you provide.")
            
            # In real implementation, would:
            # 1. Identify form fields using OCR
            # 2. Match fields to data
            # 3. Fill fields programmatically
            
            return "Ready to fill the form. Please provide the data."
        else:
            return "Please open a form and I'll show you how I can help fill it automatically."
    
    def demo_document_processing(self):
        """Demonstrate document processing"""
        content = self.vision.read_document_content()
        
        if content and content['type'] == 'document':
            word_count = content['word_count']
            
            capabilities = [
                f"I can see you have a document with {word_count} words open.",
                "I can help with:",
                "- Formatting (headings, fonts, spacing)",
                "- Proofreading and grammar checking",
                "- Creating table of contents",
                "- Mail merge operations",
                "- Converting to different formats"
            ]
            
            return " ".join(capabilities)
        else:
            return "Please open a Word document and I'll show you how I can help process it."
    
    def demo_data_entry(self):
        """Demonstrate data entry capabilities"""
        content = self.vision.read_document_content()
        
        if content and content['type'] == 'spreadsheet':
            return "I can see your spreadsheet. I can help enter data, create formulas, and generate reports."
        else:
            return "Please open a spreadsheet and I'll show you how I can help with data entry."