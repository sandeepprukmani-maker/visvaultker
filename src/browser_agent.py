"""
Browser automation agent using smolagents framework.
This agent can control a local browser using natural language commands.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from smolagents import CodeAgent, LiteLLMModel
from src.browser_tools import get_all_browser_tools, set_browser_state

load_dotenv()


class BrowserAgent:
    """An AI agent that can control a browser using natural language."""
    
    def __init__(self, model_id: str = "gpt-4o", headless: bool = False):
        """
        Initialize the browser agent.
        
        Args:
            model_id: The LLM model to use (default: gpt-4o)
            headless: Whether to run browser in headless mode (default: False for visibility)
        """
        self.model_id = model_id
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.agent: Optional[CodeAgent] = None
        
    def start(self):
        """Start the browser and initialize the agent."""
        print("Starting browser...")
        self.playwright = sync_playwright().start()
        
        import subprocess
        chromium_path = subprocess.run(
            ["which", "chromium"], 
            capture_output=True, 
            text=True
        ).stdout.strip()
        
        self.browser = self.playwright.chromium.launch(
            executable_path=chromium_path if chromium_path else None,
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        
        self.context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        self.page = self.context.new_page()
        
        set_browser_state(self.playwright, self.browser, self.context, self.page)
        
        print("Initializing AI agent...")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        model = LiteLLMModel(
            model_id=self.model_id,
            api_key=api_key,
        )
        
        self.agent = CodeAgent(
            tools=get_all_browser_tools(),
            model=model,
            max_steps=20,
            verbosity_level=2,
        )
        
        print("Browser agent ready!")
        
    def run(self, task: str):
        """
        Execute a natural language task in the browser.
        
        Args:
            task: Natural language description of what to do (e.g., "Search for Python tutorials on Google")
            
        Returns:
            The result of the task execution
        """
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call start() first.")
        
        print(f"\nExecuting task: {task}")
        print("-" * 50)
        
        enhanced_prompt = f"""You are controlling a web browser. Complete the following task:

Task: {task}

Instructions:
1. First use get_page_content() or get_page_elements() to understand what's on the current page
2. Use navigate_to_url() to go to websites
3. Use click_text() to click on visible text, or click_element() with CSS selectors
4. Use type_text() to fill in forms
5. Use press_key('Enter') to submit forms
6. Use take_screenshot() if you need to see the current state
7. Always verify your actions worked by checking the page content

Be methodical and verify each step before proceeding to the next."""

        try:
            result = self.agent.run(enhanced_prompt)
            return result
        except Exception as e:
            return f"Error executing task: {str(e)}"
    
    def stop(self):
        """Stop the browser and clean up resources."""
        print("\nClosing browser...")
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("Browser closed.")


def create_agent(model_id: str = "gpt-4o", headless: bool = False) -> BrowserAgent:
    """
    Create and start a browser agent.
    
    Args:
        model_id: The LLM model to use
        headless: Whether to run in headless mode
        
    Returns:
        An initialized BrowserAgent
    """
    agent = BrowserAgent(model_id=model_id, headless=headless)
    agent.start()
    return agent
