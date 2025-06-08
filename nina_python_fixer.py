"""
Nina Python Code Fixer
Automatically fixes Python code formatting, indentation, and common errors
"""

import ast
import autopep8
import black
import isort
import re
from pathlib import Path
import subprocess
import tempfile
import difflib
from typing import List, Tuple, Dict
import tokenize
import io
import astunparse
import pyflakes.api
import pylint.lint
from pylint.reporters.text import TextReporter


class PythonCodeFixer:
    """Fix Python code formatting, indentation, and common errors"""
    
    def __init__(self, nina):
        self.nina = nina
        self.style_guide = {
            'line_length': 88,  # Black default
            'indent_size': 4,
            'use_tabs': False,
            'sort_imports': True,
            'remove_unused': True,
            'fix_line_endings': True
        }
        
    def fix_code_from_file(self, file_path):
        """Fix Python code from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            fixed_code, issues = self.fix_code(original_code)
            
            if fixed_code != original_code:
                # Show diff
                self.show_diff(original_code, fixed_code, file_path)
                
                # Ask before saving
                self.nina.speak(f"I found and fixed {len(issues)} issues in your code. The main problems were: {', '.join(issues[:3])}")
                
                # Save fixed code
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                    
                self.nina.speak("I've fixed and saved your code!")
            else:
                self.nina.speak("Your code looks good! No formatting issues found.")
                
        except Exception as e:
            self.nina.speak(f"I encountered an error while fixing the code: {str(e)}")
    
    def fix_code(self, code: str) -> Tuple[str, List[str]]:
        """Fix Python code and return fixed version with list of issues"""
        issues = []
        
        # Step 1: Fix basic indentation errors
        code, indent_issues = self.fix_indentation(code)
        issues.extend(indent_issues)
        
        # Step 2: Fix syntax errors if possible
        code, syntax_issues = self.fix_syntax_errors(code)
        issues.extend(syntax_issues)
        
        # Step 3: Apply autopep8 for PEP8 compliance
        try:
            code = autopep8.fix_code(code, options={
                'aggressive': 2,
                'max_line_length': self.style_guide['line_length']
            })
            if code != code:
                issues.append("PEP8 style violations")
        except:
            pass
        
        # Step 4: Apply Black formatter
        try:
            code = black.format_str(code, mode=black.Mode(
                line_length=self.style_guide['line_length']
            ))
        except:
            issues.append("Could not apply Black formatting")
        
        # Step 5: Sort imports with isort
        if self.style_guide['sort_imports']:
            try:
                code = isort.code(code)
                issues.append("Import sorting")
            except:
                pass
        
        # Step 6: Remove unused imports
        if self.style_guide['remove_unused']:
            code, unused = self.remove_unused_imports(code)
            if unused:
                issues.append(f"Removed unused imports: {', '.join(unused)}")
        
        # Step 7: Fix common patterns
        code, pattern_issues = self.fix_common_patterns(code)
        issues.extend(pattern_issues)
        
        return code, issues
    
    def fix_indentation(self, code: str) -> Tuple[str, List[str]]:
        """Fix indentation errors in Python code"""
        issues = []
        lines = code.split('\n')
        fixed_lines = []
        indent_stack = [0]
        
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue
            
            # Calculate expected indentation
            current_indent = len(line) - len(stripped)
            
            # Check for block starters
            if stripped.endswith(':'):
                fixed_lines.append(' ' * indent_stack[-1] + stripped)
                indent_stack.append(indent_stack[-1] + 4)
                issues.append(f"Fixed indentation at line {i+1}")
            
            # Check for block enders
            elif stripped.startswith(('return', 'break', 'continue', 'pass')):
                if len(indent_stack) > 1:
                    fixed_lines.append(' ' * indent_stack[-1] + stripped)
                    indent_stack.pop()
                else:
                    fixed_lines.append(stripped)
            
            # Check for dedent keywords
            elif stripped.startswith(('else:', 'elif ', 'except:', 'finally:', 'except ')):
                if len(indent_stack) > 1:
                    indent_stack.pop()
                fixed_lines.append(' ' * indent_stack[-1] + stripped)
                indent_stack.append(indent_stack[-1] + 4)
                issues.append(f"Fixed indentation for {stripped.split()[0]} at line {i+1}")
            
            # Regular line
            else:
                # Fix mixed tabs and spaces
                if '\t' in line:
                    line = line.replace('\t', '    ')
                    issues.append(f"Replaced tabs with spaces at line {i+1}")
                
                # Use current indentation level
                fixed_lines.append(' ' * indent_stack[-1] + stripped)
        
        return '\n'.join(fixed_lines), issues
    
    def fix_syntax_errors(self, code: str) -> Tuple[str, List[str]]:
        """Attempt to fix common syntax errors"""
        issues = []
        
        # Fix missing colons
        lines = code.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            fixed_line = line
            
            # Add missing colons
            if re.match(r'^\s*(if|elif|else|for|while|def|class|try|except|finally|with)\s+.*[^:]$', line):
                fixed_line = line + ':'
                issues.append(f"Added missing colon at line {i+1}")
            
            # Fix common typos
            replacements = {
                'prnit': 'print',
                'pritn': 'print',
                'improt': 'import',
                'form': 'from',
                'retrun': 'return',
                'ture': 'True',
                'flase': 'False',
                'none': 'None',
                'slef': 'self',
                'sefl': 'self',
            }
            
            for typo, correct in replacements.items():
                if typo in fixed_line:
                    fixed_line = fixed_line.replace(typo, correct)
                    issues.append(f"Fixed typo '{typo}' -> '{correct}' at line {i+1}")
            
            # Fix missing quotes
            if 'print(' in fixed_line:
                # Simple regex to fix unquoted strings in print
                match = re.search(r'print\(([^"\'\)]+)\)', fixed_line)
                if match and not match.group(1).strip().isdigit():
                    content = match.group(1).strip()
                    if not any(char in content for char in ['(', ')', '+', '-', '*', '/', '=']):
                        fixed_line = fixed_line.replace(f'print({content})', f'print("{content}")')
                        issues.append(f"Added quotes to print statement at line {i+1}")
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines), issues
    
    def remove_unused_imports(self, code: str) -> Tuple[str, List[str]]:
        """Remove unused imports from code"""
        try:
            tree = ast.parse(code)
            
            # Find all imports
            imports = []
            used_names = set()
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)
                elif isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name):
                        used_names.add(node.value.id)
            
            # Check which imports are unused
            unused = []
            lines_to_remove = []
            
            for imp in imports:
                if isinstance(imp, ast.Import):
                    for alias in imp.names:
                        name = alias.asname if alias.asname else alias.name
                        if name not in used_names:
                            unused.append(name)
                            lines_to_remove.append(imp.lineno - 1)
                elif isinstance(imp, ast.ImportFrom):
                    module_used = False
                    for alias in imp.names:
                        name = alias.asname if alias.asname else alias.name
                        if name in used_names:
                            module_used = True
                            break
                    if not module_used:
                        unused.append(imp.module)
                        lines_to_remove.append(imp.lineno - 1)
            
            # Remove unused import lines
            if lines_to_remove:
                lines = code.split('\n')
                for line_no in sorted(lines_to_remove, reverse=True):
                    if line_no < len(lines):
                        del lines[line_no]
                code = '\n'.join(lines)
            
            return code, unused
            
        except:
            return code, []
    
    def fix_common_patterns(self, code: str) -> Tuple[str, List[str]]:
        """Fix common Python anti-patterns"""
        issues = []
        
        # Fix == None to is None
        if '== None' in code:
            code = code.replace('== None', 'is None')
            issues.append("Changed '== None' to 'is None'")
        
        if '!= None' in code:
            code = code.replace('!= None', 'is not None')
            issues.append("Changed '!= None' to 'is not None'")
        
        # Fix == True/False
        if '== True' in code:
            code = re.sub(r'(\w+)\s*==\s*True', r'\1', code)
            issues.append("Simplified '== True' comparisons")
        
        if '== False' in code:
            code = re.sub(r'(\w+)\s*==\s*False', r'not \1', code)
            issues.append("Simplified '== False' comparisons")
        
        # Fix string concatenation with +
        if re.search(r'"\s*\+\s*"', code):
            issues.append("Consider using f-strings instead of string concatenation")
        
        # Fix mutable default arguments
        if re.search(r'def\s+\w+\([^)]*=\s*\[\]', code):
            issues.append("Warning: Mutable default argument detected")
        
        return code, issues
    
    def show_diff(self, original: str, fixed: str, filename: str):
        """Show differences between original and fixed code"""
        print(f"\n🔧 Changes to {filename}:")
        print("=" * 60)
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f'{filename} (original)',
            tofile=f'{filename} (fixed)',
            n=3
        )
        
        for line in diff:
            if line.startswith('+'):
                print(f"\033[32m{line}\033[0m", end='')  # Green
            elif line.startswith('-'):
                print(f"\033[31m{line}\033[0m", end='')  # Red
            else:
                print(line, end='')
    
    def analyze_code_quality(self, code: str) -> Dict:
        """Analyze code quality and provide suggestions"""
        analysis = {
            'complexity': 0,
            'issues': [],
            'suggestions': [],
            'score': 100
        }
        
        try:
            tree = ast.parse(code)
            
            # Check for code complexity
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While)):
                    analysis['complexity'] += 1
            
            # Check for long functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno
                    if func_lines > 50:
                        analysis['suggestions'].append(
                            f"Function '{node.name}' is {func_lines} lines long. Consider breaking it up."
                        )
                        analysis['score'] -= 10
            
            # Check for missing docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        analysis['issues'].append(f"Missing docstring for {node.name}")
                        analysis['score'] -= 5
            
            # Check variable naming
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if len(node.id) == 1 and node.id not in ('i', 'j', 'k', 'x', 'y', 'z'):
                        analysis['suggestions'].append(
                            f"Single-letter variable '{node.id}' - consider more descriptive name"
                        )
            
        except SyntaxError as e:
            analysis['issues'].append(f"Syntax error: {e}")
            analysis['score'] = 0
        
        return analysis
    
    def fix_from_clipboard(self):
        """Fix code from clipboard"""
        try:
            import pyperclip
            code = pyperclip.paste()
            
            if not code.strip():
                self.nina.speak("No code found in clipboard")
                return
            
            fixed_code, issues = self.fix_code(code)
            
            if issues:
                self.nina.speak(f"I fixed {len(issues)} issues in your code")
                pyperclip.copy(fixed_code)
                self.nina.speak("The fixed code is now in your clipboard")
            else:
                self.nina.speak("The code looks good, no issues found")
                
        except ImportError:
            self.nina.speak("Please install pyperclip to use clipboard features")
    
    def fix_current_file(self):
        """Fix the currently open Python file"""
        if hasattr(self.nina, 'vision'):
            content = self.nina.vision.read_document_content()
            
            if content and content['text']:
                # Check if it's Python code
                if 'def ' in content['text'] or 'import ' in content['text']:
                    fixed_code, issues = self.fix_code(content['text'])
                    
                    if issues:
                        self.nina.speak(f"I can see Python code with {len(issues)} issues. "
                                      f"The main problems are: {', '.join(issues[:3])}")
                        
                        # Save to temporary file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                            f.write(fixed_code)
                            temp_path = f.name
                        
                        self.nina.speak(f"I've saved the fixed code. You can copy it from {temp_path}")
                    else:
                        self.nina.speak("Your code looks well-formatted!")
                else:
                    self.nina.speak("I don't see Python code on the screen")
            else:
                self.nina.speak("I can't see any code on the screen")
        else:
            self.nina.speak("Screen vision is not enabled")


class PythonCodeHelper:
    """Additional Python coding assistance"""
    
    def __init__(self, nina, fixer):
        self.nina = nina
        self.fixer = fixer
        
    def explain_error(self, error_message: str):
        """Explain Python errors in simple terms"""
        explanations = {
            "IndentationError": "Your code isn't lined up correctly. Python uses spacing to understand code blocks.",
            "SyntaxError": "There's a typo or missing character in your code, like a colon or parenthesis.",
            "NameError": "You're using a variable or function that hasn't been defined yet.",
            "TypeError": "You're trying to use a value in a way that doesn't make sense for its type.",
            "ValueError": "The value you're using is the right type but not acceptable for the operation.",
            "AttributeError": "You're trying to use a method or property that doesn't exist for this object.",
            "IndexError": "You're trying to access a list position that doesn't exist.",
            "KeyError": "You're trying to access a dictionary key that doesn't exist.",
            "ImportError": "Python can't find the module you're trying to import.",
            "ZeroDivisionError": "You're trying to divide by zero, which isn't allowed."
        }
        
        for error_type, explanation in explanations.items():
            if error_type in error_message:
                return f"{explanation} The full error is: {error_message}"
        
        return f"You have an error: {error_message}"
    
    def suggest_fix_for_error(self, code: str, error_message: str):
        """Suggest fixes for common Python errors"""
        suggestions = []
        
        if "IndentationError" in error_message:
            suggestions.append("Let me fix the indentation for you")
            fixed_code, _ = self.fixer.fix_indentation(code)
            return fixed_code, suggestions
            
        elif "SyntaxError: invalid syntax" in error_message:
            line_match = re.search(r'line (\d+)', error_message)
            if line_match:
                line_no = int(line_match.group(1))
                suggestions.append(f"Check line {line_no} for missing colons, parentheses, or quotes")
                
        elif "NameError" in error_message:
            name_match = re.search(r"name '(\w+)' is not defined", error_message)
            if name_match:
                undefined_name = name_match.group(1)
                
                if undefined_name == "true" or undefined_name == "false":
                    code = code.replace("true", "True").replace("false", "False")
                    suggestions.append("Fixed: Python uses 'True' and 'False' with capital letters")
                elif undefined_name == "null":
                    code = code.replace("null", "None")
                    suggestions.append("Fixed: Python uses 'None' instead of 'null'")
                else:
                    suggestions.append(f"Make sure you've defined '{undefined_name}' before using it")
        
        return code, suggestions
    
    def generate_boilerplate(self, template_type: str) -> str:
        """Generate Python boilerplate code"""
        templates = {
            "script": '''#!/usr/bin/env python3
"""
Script description here
"""

import sys
import argparse


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Script description')
    parser.add_argument('input', help='Input file')
    parser.add_argument('-o', '--output', help='Output file', default='output.txt')
    
    args = parser.parse_args()
    
    # Your code here
    print(f"Processing {args.input}")


if __name__ == "__main__":
    main()
''',
            
            "class": '''class MyClass:
    """Class description"""
    
    def __init__(self, name):
        """Initialize the class"""
        self.name = name
        self._private_var = None
    
    def public_method(self):
        """Public method description"""
        return f"Hello from {self.name}"
    
    def _private_method(self):
        """Private method description"""
        pass
    
    @property
    def private_var(self):
        """Getter for private variable"""
        return self._private_var
    
    @private_var.setter
    def private_var(self, value):
        """Setter for private variable"""
        self._private_var = value
''',
            
            "test": '''import unittest


class TestMyModule(unittest.TestCase):
    """Test cases for my_module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = []
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_example(self):
        """Test example functionality"""
        result = 2 + 2
        self.assertEqual(result, 4)
    
    def test_with_assertion(self):
        """Test with various assertions"""
        self.assertTrue(True)
        self.assertFalse(False)
        self.assertIsNone(None)
        self.assertIn(1, [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
''',
            
            "async": '''import asyncio


async def fetch_data(url):
    """Async function to fetch data"""
    # Simulate async operation
    await asyncio.sleep(1)
    return f"Data from {url}"


async def main():
    """Main async function"""
    urls = ["url1", "url2", "url3"]
    
    # Run tasks concurrently
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
'''
        }
        
        return templates.get(template_type, "# Template not found")


# Integration function
def add_python_fixer_to_nina(handlers):
    """Add Python fixing capabilities to Nina"""
    
    # Initialize the fixer
    fixer = PythonCodeFixer(handlers.nina)
    helper = PythonCodeHelper(handlers.nina, fixer)
    
    # Store in handlers
    handlers.python_fixer = fixer
    handlers.python_helper = helper
    
    def handle_fix_python(command):
        """Handle Python fixing commands"""
        cmd_lower = command.lower()
        
        if "fix" in cmd_lower and ("python" in cmd_lower or "code" in cmd_lower or "file" in cmd_lower):
            # Check if specific file mentioned
            if ".py" in command:
                # Extract filename
                filename = None
                for word in command.split():
                    if ".py" in word:
                        filename = word
                        break
                
                if filename and os.path.exists(filename):
                    fixer.fix_code_from_file(filename)
                else:
                    handlers.nina.speak("I couldn't find that Python file")
            
            elif "clipboard" in cmd_lower:
                fixer.fix_from_clipboard()
            
            elif "this" in cmd_lower or "current" in cmd_lower:
                fixer.fix_current_file()
            
            else:
                # Look for Python files in current directory
                py_files = list(Path.cwd().glob("*.py"))
                if py_files:
                    handlers.nina.speak(f"I found {len(py_files)} Python files. Which one should I fix?")
                else:
                    handlers.nina.speak("I don't see any Python files in the current directory")
        
        elif "explain" in cmd_lower and "error" in cmd_lower:
            # Extract error message
            error_part = command.split("error")[-1].strip()
            explanation = helper.explain_error(error_part)
            handlers.nina.speak(explanation)
        
        elif "template" in cmd_lower or "boilerplate" in cmd_lower:
            template_type = "script"  # default
            
            if "class" in cmd_lower:
                template_type = "class"
            elif "test" in cmd_lower:
                template_type = "test"
            elif "async" in cmd_lower:
                template_type = "async"
            
            code = helper.generate_boilerplate(template_type)
            
            # Save to file
            filename = f"{template_type}_template.py"
            with open(filename, 'w') as f:
                f.write(code)
            
            handlers.nina.speak(f"I've created a {template_type} template for you in {filename}")
    
    # Add handler
    handlers.handle_fix_python = handle_fix_python
    
    return handlers