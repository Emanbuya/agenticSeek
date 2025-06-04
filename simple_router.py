#!/usr/bin/env python3
"""
Simple router for Agentic Seek - bypasses complex routing
"""

import random
from sources.agents.agent import Agent

class SimpleRouter:
    def __init__(self, agents):
        self.agents = agents
        self.casual_agent = None
        
        # Find casual agent
        for agent in agents:
            if agent.type == "casual_agent":
                self.casual_agent = agent
                break
                
    def select_agent(self, text):
        """Simple selection - just use casual agent for most things"""
        text_lower = text.lower()
        
        # Simple keyword matching
        if any(word in text_lower for word in ['browse', 'search', 'google', 'web', 'find online']):
            for agent in self.agents:
                if agent.type == "browser_agent":
                    return agent
                    
        if any(word in text_lower for word in ['code', 'script', 'program', 'function', 'debug']):
            for agent in self.agents:
                if agent.type == "code_agent":
                    return agent
                    
        if any(word in text_lower for word in ['file', 'folder', 'directory', 'find', 'locate']):
            for agent in self.agents:
                if agent.type == "file_agent":
                    return agent
        
        # Default to casual agent
        return self.casual_agent

# Monkey patch the import
import sys
sys.modules['sources.router'] = sys.modules[__name__]
AgentRouter = SimpleRouter
