import os
import sys
import torch
import random
from typing import List, Tuple, Type, Dict

from transformers import pipeline

# The correct imports based on your project structure:
from sources.agents import Agent, CoderAgent, CasualAgent, FileAgent, PlannerAgent, BrowserAgent
from sources.language import LanguageUtility
from sources.utility import pretty_print, animate_thinking
from sources.logger import Logger

class AgentRouter:
    """
    AgentRouter is a class that selects the appropriate agent based on the user query.
    """
    def __init__(self, agents: list, supported_language: List[str] = ["en"]):
        self.agents = agents
        self.logger = Logger("router.log")
        self.lang_analysis = LanguageUtility(supported_language=supported_language)
        self.pipelines = self.load_pipelines()
        self.talk_classifier = self.load_llm_router()
        self.complexity_classifier = self.load_llm_router()
        
        # Map classification labels to agent types
        self.classifier_map = {
            "web": BrowserAgent,
            "browser": BrowserAgent,
            "casual": CasualAgent,
            "talk": CasualAgent,
            "files": FileAgent,
            "code": CoderAgent,
            "planner": PlannerAgent
        }
        
        # Learn from examples
        if hasattr(self.talk_classifier, "add_examples"):
            self.learn_few_shots_tasks()
        if hasattr(self.complexity_classifier, "add_examples"):
            self.learn_few_shots_complexity()
        self.asked_clarify = False
    
    def load_pipelines(self) -> Dict[str, Type[pipeline]]:
        """
        Load the pipelines for the text classification used for routing.
        returns:
            Dict[str, Type[pipeline]]: The loaded pipelines
        """
        animate_thinking("Loading zero-shot pipeline...", color="status")
        return {
            "bart": pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        }

    def load_llm_router(self):
        """
        Use local llm_router.py backed by Ollama for routing.
        """
        try:
            from pathlib import Path
            import importlib.util

            router_path = Path(__file__).parent.parent.parent / "llm_router.py"
            spec = importlib.util.spec_from_file_location("llm_router", str(router_path))
            llm_router = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(llm_router)

            class LLMRouterWrapper:
                def classify(self, text):
                    # Enhanced prompt for better classification
                    prompt = f"""You are a query classifier. Classify the following text into EXACTLY ONE category.

Categories:
- "web": For weather, news, online searches, current events, temperature, forecasts, web browsing, internet queries
- "code": For programming, debugging, scripts, coding tasks, software development
- "files": For finding files, folders, organizing directories on local system
- "talk": For casual chat, jokes, stories, greetings, general conversation
- "planner": For complex multi-step tasks that need planning

Important rules:
- Weather queries (temperature, forecast, rain, snow, climate) ALWAYS classify as "web"
- Current information queries ALWAYS classify as "web"
- Internet/online searches ALWAYS classify as "web"

Text to classify: "{text}"

Respond with ONLY the category name. Nothing else. Just one word: web, code, files, talk, or planner."""

                    result = llm_router.query_llama3(prompt)
                    # Clean and process the result
                    result = result.strip().lower()
                    
                    # Direct matches
                    if "web" in result or "browse" in result or "search" in result:
                        return "web"
                    elif "code" in result or "program" in result:
                        return "code"
                    elif "file" in result or "folder" in result:
                        return "files"
                    elif "planner" in result or "plan" in result:
                        return "planner"
                    elif "talk" in result or "chat" in result:
                        return "talk"
                    
                    # Fallback keyword matching
                    text_lower = text.lower()
                    if any(word in text_lower for word in ['weather', 'temperature', 'forecast', 'rain', 'snow', 
                                                           'humid', 'climate', 'sunny', 'cloudy', 'news', 'current',
                                                           'search', 'browse', 'find online', 'look up', 'website']):
                        return "web"
                    elif any(word in text_lower for word in ['code', 'script', 'program', 'debug', 'function']):
                        return "code"
                    elif any(word in text_lower for word in ['file', 'folder', 'directory', 'path']):
                        return "files"
                    
                    return "talk"  # Default fallback
                
                def predict(self, text):
                    # Predict method for compatibility
                    category = self.classify(text)
                    
                    # Return predictions in expected format
                    if category == "web":
                        return [("web", 0.9), ("talk", 0.05), ("files", 0.05)]
                    elif category == "code":
                        return [("code", 0.9), ("files", 0.05), ("talk", 0.05)]
                    elif category == "files":
                        return [("files", 0.9), ("code", 0.05), ("talk", 0.05)]
                    elif category == "planner":
                        return [("planner", 0.9), ("web", 0.05), ("talk", 0.05)]
                    else:
                        return [("talk", 0.9), ("web", 0.05), ("files", 0.05)]
                
                def add_examples(self, texts, labels):
                    # Dummy method for compatibility
                    pass

            return LLMRouterWrapper()
        except Exception as e:
            raise Exception(f"❌ Failed to load local LLM router: {e}")

    def get_device(self) -> str:
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda:0"
        else:
            return "cpu"
    
    def learn_few_shots_complexity(self) -> None:
        """
        Few shot learning for complexity estimation.
        """
        few_shots = [
            ("hi", "LOW"),
            ("What's the weather like today?", "LOW"),
            ("Write a Python script to check if a number is prime", "LOW"),
            ("Find a file named notes.txt", "LOW"),
            ("Search for the latest news", "LOW"),
            ("Create a web app with user authentication and database", "HIGH"),
            ("Plan a trip to Japan including flights, hotels, and activities", "HIGH"),
            ("Build a machine learning model and deploy it", "HIGH"),
        ]
        texts = [text for text, _ in few_shots]
        labels = [label for _, label in few_shots]
        self.complexity_classifier.add_examples(texts, labels)

    def learn_few_shots_tasks(self) -> None:
        """
        Few shot learning for tasks classification.
        """
        few_shots = [
            # Web/Browser tasks
            ("What's the weather like today?", "web"),
            ("Search for the latest news", "web"),
            ("Find restaurants near me", "web"),
            ("What's the temperature in New York?", "web"),
            ("Check the stock market", "web"),
            ("Look up information about Paris", "web"),
            
            # Code tasks
            ("Write a Python script", "code"),
            ("Debug this JavaScript error", "code"),
            ("Create a function to sort a list", "code"),
            ("Fix this bug in my code", "code"),
            
            # File tasks - EXPANDED
            ("Find all PDF files", "files"),
            ("List files in my documents", "files"),
            ("Open my downloads folder", "files"),
            ("Search for a file named report.docx", "files"),
            ("Open explorer", "files"),
            ("Open file explorer", "files"),
            ("Show me what's in my desktop", "files"),
            ("List all PDF files in my documents folder", "files"),
            ("What files are in downloads", "files"),
            ("Delete old files", "files"),
            ("Move files to another folder", "files"),
            ("Copy this file", "files"),
            ("Rename document.txt", "files"),
            ("Create a new folder", "files"),
            ("Show me my recent files", "files"),
            ("Find large files on my computer", "files"),
            ("Open Windows Explorer", "files"),
            ("Navigate to my documents", "files"),
            
            # Talk/Casual tasks
            ("Hello", "talk"),
            ("How are you?", "talk"),
            ("Tell me a joke", "talk"),
            ("What do you think about AI?", "talk"),
            
            # Complex/Planner tasks
            ("Plan a trip to Japan", "planner"),
            ("Create a full web application", "planner"),
            ("Organize a conference", "planner"),
        ]
        texts = [text for text, _ in few_shots]
        labels = [label for _, label in few_shots]
        self.talk_classifier.add_examples(texts, labels)

    def llm_router(self, text: str) -> tuple:
        """
        Inference of the LLM router model.
        """
        predictions = self.talk_classifier.predict(text)
        predictions = [pred for pred in predictions if pred[0] not in ["HIGH", "LOW"]]
        predictions = sorted(predictions, key=lambda x: x[1], reverse=True)
        return predictions[0] if predictions else ("talk", 0.5)
    
    def router_vote(self, text: str, labels: list, log_confidence: bool = False) -> str:
        """
        Vote between the LLM router and BART model.
        """
        if len(text) <= 8:
            return "talk"
        
        result_bart = self.pipelines['bart'](text, labels)
        result_llm_router = self.llm_router(text)
        
        bart, confidence_bart = result_bart['labels'][0], result_bart['scores'][0]
        llm_router, confidence_llm_router = result_llm_router[0], result_llm_router[1]
        
        final_score_bart = confidence_bart / (confidence_bart + confidence_llm_router)
        final_score_llm = confidence_llm_router / (confidence_bart + confidence_llm_router)
        
        self.logger.info(f"Routing Vote: BART: {bart} ({final_score_bart}) LLM: {llm_router} ({final_score_llm})")
        
        if log_confidence:
            pretty_print(f"Agent choice -> BART: {bart} ({final_score_bart}) LLM: {llm_router} ({final_score_llm})")
        
        return bart if final_score_bart > final_score_llm else llm_router
    
    def find_first_sentence(self, text: str) -> str:
        first_sentence = None
        for line in text.split("\n"):
            first_sentence = line.strip()
            if first_sentence:
                break
        return first_sentence if first_sentence else text
    
    def estimate_complexity(self, text: str) -> str:
        """
        Estimate the complexity of the text.
        """
        try:
            predictions = self.complexity_classifier.predict(text)
            predictions = sorted(predictions, key=lambda x: x[1], reverse=True)
            
            if not predictions:
                return "LOW"
            
            complexity, confidence = predictions[0][0], predictions[0][1]
            
            if confidence < 0.5:
                self.logger.info(f"Low confidence in complexity: {confidence}")
                return "HIGH"
            
            return complexity if complexity in ["HIGH", "LOW"] else "LOW"
        except Exception as e:
            pretty_print(f"Error in estimate_complexity: {str(e)}", color="failure")
            return "LOW"
    
    def find_planner_agent(self) -> Agent:
        """
        Find the planner agent.
        """
        for agent in self.agents:
            if agent.type == "planner_agent":
                return agent
        pretty_print(f"Error: Planner agent not found.", color="failure")
        self.logger.error("Planner agent not found.")
        return None
    
    def select_agent(self, text: str) -> Agent:
        """
        Select the appropriate agent based on the text.
        This is the main method called by interaction.py
        """
        assert len(self.agents) > 0, "No agents available."
        
        if len(self.agents) == 1:
            return self.agents[0]
        
        # Detect language and translate if needed
        lang = self.lang_analysis.detect_language(text)
        text = self.find_first_sentence(text)
        text = self.lang_analysis.translate(text, lang)
        
        # Estimate complexity
        complexity = self.estimate_complexity(text)
        if complexity == "HIGH":
            pretty_print(f"Complex task detected, routing to planner agent.", color="info")
            planner = self.find_planner_agent()
            if planner:
                return planner
        
        # Get agent roles for voting
        labels = [agent.role for agent in self.agents]
        
        try:
            # Use voting mechanism to select best agent
            best_agent_role = self.router_vote(text, labels, log_confidence=False)
        except Exception as e:
            self.logger.error(f"Error in router_vote: {e}")
            # Fallback to LLM router only
            best_agent_role = self.llm_router(text)[0]
        
        # Find agent by role
        for agent in self.agents:
            if hasattr(agent, 'role') and best_agent_role == agent.role:
                pretty_print(f"Selected agent: {agent.agent_name} (role: {best_agent_role})", color="warning")
                return agent
        
        # If no match by role, try by type
        agent_class = self.classifier_map.get(best_agent_role)
        if agent_class:
            for agent in self.agents:
                if isinstance(agent, agent_class):
                    pretty_print(f"Selected agent: {agent.agent_name} (type: {type(agent).__name__})", color="warning")
                    return agent
        
        # Default fallback
        pretty_print(f"No specific agent found, using default.", color="failure")
        return self.agents[0]


if __name__ == "__main__":
    # Test code
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Mock agents for testing
    agents = [
        type('MockAgent', (), {'agent_name': 'TestCasual', 'role': 'talk', 'type': 'casual_agent'})(),
        type('MockAgent', (), {'agent_name': 'TestBrowser', 'role': 'web', 'type': 'browser_agent'})(),
        type('MockAgent', (), {'agent_name': 'TestCoder', 'role': 'code', 'type': 'coder_agent'})(),
    ]
    
    router = AgentRouter(agents)
    
    # Test queries
    test_queries = [
        "What's the weather like today?",
        "Write a Python script",
        "Hello, how are you?",
        "Search for news about AI",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        agent = router.select_agent(query)
        print(f"Selected: {agent.agent_name}")