import sys
print("Python path:", sys.executable)
print("Current directory:", os.getcwd())

try:
    from sources.llm_provider import Provider
    print("✓ Provider imported")
except Exception as e:
    print("✗ Provider import failed:", e)

try:
    from sources.interaction import Interaction
    print("✓ Interaction imported")
except Exception as e:
    print("✗ Interaction import failed:", e)

try:
    from sources.agents import CasualAgent, CoderAgent, FileAgent, PlannerAgent, BrowserAgent
    print("✓ Agents imported")
except Exception as e:
    print("✗ Agents import failed:", e)

print("\nTrying to start API...")