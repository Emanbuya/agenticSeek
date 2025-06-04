# llm_router.py
import requests
import json
import sys

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:mini"

def query_llama3(prompt):
    """Send a prompt to the local Ollama LLaMA3 model and return the response."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(OLLAMA_URL, headers=headers, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        return result if result else "No response generated."
    except requests.exceptions.ConnectionError:
        return "❌ Error: Could not connect to Ollama. Make sure `ollama serve` is running."
    except requests.exceptions.Timeout:
        return "⏱️ Error: Ollama request timed out."
    except Exception as e:
        return f"⚠️ Unexpected error: {e}"

# Optional CLI usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python llm_router.py \"Your question here\"")
    else:
        prompt = " ".join(sys.argv[1:])
        print(f"\n🧠 LLaMA3 Response:\n{query_llama3(prompt)}")
