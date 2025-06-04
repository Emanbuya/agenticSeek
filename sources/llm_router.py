# Update your llm_router.py file to use deepseek-v2:16b

import requests
import json
import sys
import os

OLLAMA_URL = "http://localhost:11434/api/generate"

# Read model from environment or config
def get_model_name():
    # Try environment variable first
    model = os.getenv("OLLAMA_MODEL")
    if model:
        return model
    
    # Try reading from config.ini
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config.get('MAIN', 'provider_model', fallback='deepseek-v2:16b')
    except:
        return 'deepseek-v2:16b'

OLLAMA_MODEL = get_model_name()

def query_llama3(prompt):
    """Send a prompt to the local Ollama model and return the response."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "temperature": 0.1,  # Lower temperature for more consistent routing
        "top_p": 0.9
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(OLLAMA_URL, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        return result if result else "No response generated."
    except requests.exceptions.ConnectionError:
        return f"❌ Error: Could not connect to Ollama. Make sure `ollama serve` is running and {OLLAMA_MODEL} is pulled."
    except requests.exceptions.Timeout:
        return "⏱️ Error: Ollama request timed out."
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"

# Optional CLI usage
if __name__ == "__main__":
    print(f"Using model: {OLLAMA_MODEL}")
    if len(sys.argv) < 2:
        print(f"Usage: python llm_router.py \"Your question here\"")
    else:
        prompt = " ".join(sys.argv[1:])
        print(f"\n🧠 {OLLAMA_MODEL} Response:\n{query_llama3(prompt)}")