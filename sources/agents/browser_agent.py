import re
import time
import asyncio
from datetime import date
from typing import List, Tuple, Type, Dict
from enum import Enum

from sources.utility import pretty_print, animate_thinking
from sources.agents.agent import Agent
from sources.tools.searxSearch import searxSearch
from sources.browser import Browser
from sources.logger import Logger
from sources.memory import Memory


class BrowserAgent(Agent):
    """
    Nina's Web Intelligence Module - Fixed Version
    Fast, reliable web search with timeout protection
    """
    
    def __init__(self, name, prompt_path, provider, verbose=False, browser=None):
        """Initialize Nina's web browsing capabilities"""
        super().__init__(name, prompt_path, provider, verbose, browser)
        self.tools = {
            "web_search": searxSearch(base_url="http://localhost:8080"),
        }
        self.role = "web"
        self.type = "browser_agent"
        self.browser = browser
        self.logger = Logger("nina_browser.log")
        self.memory = Memory(
            self.load_prompt(prompt_path),
            recover_last_session=False,
            memory_compression=False,
            model_provider=provider.get_model_name()
        )
        self.date = self.get_today_date()
        
        # Timeout settings
        self.search_timeout = 10  # seconds
        self.browse_timeout = 15  # seconds
        self.total_timeout = 30   # seconds total
        
        # Disable visual elements
        if browser and hasattr(browser, 'screenshot'):
            browser.screenshot = lambda: None
    
    def get_today_date(self) -> str:
        """Get today's date in natural format"""
        date_time = date.today()
        return date_time.strftime("%B %d, %Y")
    
    def extract_snippets(self, search_text: str) -> List[Dict]:
        """Extract search results from text format"""
        results = []
        blocks = search_text.split("\n\n")
        
        for block in blocks[:5]:  # Limit to first 5 results
            if "Title:" in block and "Snippet:" in block:
                title_match = re.search(r'Title:\s*(.+)', block)
                snippet_match = re.search(r'Snippet:\s*(.+)', block)
                link_match = re.search(r'Link:\s*(.+)', block)
                
                if title_match and snippet_match:
                    results.append({
                        'title': title_match.group(1).strip(),
                        'snippet': snippet_match.group(1).strip(),
                        'link': link_match.group(1).strip() if link_match else ""
                    })
        
        return results
    
    async def process(self, user_prompt: str, speech_module: type) -> Tuple[str, str]:
        """
        Main processing - simplified and fast
        """
        try:
            # Set a total timeout for the entire process
            start_time = time.time()
            
            # Step 1: Create search query (quick)
            search_query = await self._create_search_query(user_prompt)
            
            # Step 2: Perform web search
            search_results = await self._perform_search(search_query)
            
            if time.time() - start_time > self.total_timeout:
                return self._timeout_response(user_prompt)
            
            # Step 3: Extract answer from search results
            answer = await self._extract_answer(search_results, user_prompt)
            
            # Make sure we have a valid answer
            if not answer or len(answer) < 20:
                answer = self._fallback_response(user_prompt)
            
            self.last_answer = answer
            return answer, "Search completed"
            
        except asyncio.TimeoutError:
            self.logger.error("Process timeout")
            return self._timeout_response(user_prompt), "Timeout"
        except Exception as e:
            self.logger.error(f"Process error: {e}")
            return self._error_response(user_prompt), str(e)
    
    async def _create_search_query(self, user_prompt: str) -> str:
        """Create optimized search query"""
        try:
            # Simple approach - just clean up the query
            query = user_prompt.lower()
            
            # Add context for common queries
            if "weather" in query and "in" not in query:
                query += " in San Marcos TX"
            elif "who is" in query:
                query = query.replace("who is", "").strip() + " biography"
            
            return query
            
        except Exception as e:
            self.logger.error(f"Error creating search query: {e}")
            return user_prompt
    
    async def _perform_search(self, query: str) -> str:
        """Perform web search with timeout"""
        try:
            # Use asyncio timeout
            search_task = asyncio.create_task(
                asyncio.to_thread(self.tools["web_search"].execute, [query], False)
            )
            
            results = await asyncio.wait_for(search_task, timeout=self.search_timeout)
            return results
            
        except asyncio.TimeoutError:
            self.logger.error("Search timeout")
            return ""
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return ""
    
    async def _extract_answer(self, search_results: str, user_prompt: str) -> str:
        """Extract concise answer from search results"""
        try:
            if not search_results:
                return self._fallback_response(user_prompt)
            
            # Parse search results
            snippets = self.extract_snippets(search_results)
            
            if not snippets:
                return self._fallback_response(user_prompt)
            
            # Combine top snippets
            combined_info = "\n".join([
                f"{s['title']}: {s['snippet']}" 
                for s in snippets[:3]
            ])
            
            # Use LLM to create natural response
            prompt = f"""Based on this information, give a brief natural answer to: {user_prompt}

Information:
{combined_info}

Give a 1-2 sentence conversational response. Just the facts, no preamble."""
            
            self.memory.clear()
            self.memory.push('user', prompt)
            
            # Set timeout for LLM response
            llm_task = asyncio.create_task(self.llm_request())
            answer, _ = await asyncio.wait_for(llm_task, timeout=10)
            
            return answer.strip()
            
        except asyncio.TimeoutError:
            return self._timeout_response(user_prompt)
        except Exception as e:
            self.logger.error(f"Extract answer error: {e}")
            return self._error_response(user_prompt)
    
    def _fallback_response(self, query: str) -> str:
        """Provide fallback response based on query type"""
        query_lower = query.lower()
        
        if "weather" in query_lower:
            return "I'm having trouble getting current weather data. Please try again in a moment."
        elif "who is" in query_lower:
            person = query_lower.replace("who is", "").strip()
            return f"I couldn't find information about {person} right now."
        elif "news" in query_lower:
            return "I'm unable to fetch the latest news at the moment."
        else:
            return "I couldn't find that information right now. Please try again."
    
    def _timeout_response(self, query: str) -> str:
        """Response when search times out"""
        return "The search is taking too long. Please try again with a simpler query."
    
    def _error_response(self, query: str) -> str:
        """Response when an error occurs"""
        return "I encountered an error while searching. Please try again."
    
    # Quick responses for common queries
    def get_quick_response(self, query: str) -> str:
        """Check if we can provide a quick response without searching"""
        query_lower = query.lower()
        
        quick_responses = {
            "hello": "Hello! How can I help you today?",
            "how are you": "I'm functioning well, thank you! What can I do for you?",
            "what time is it": f"I don't have real-time access, but you can check your device for the current time.",
            "thank you": "You're welcome! Is there anything else you need?",
        }
        
        for key, response in quick_responses.items():
            if key in query_lower:
                return response
        
        return None