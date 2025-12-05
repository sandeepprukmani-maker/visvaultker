"""
Browser Automation Agent using smolagents.
Control your browser with natural language commands.
"""

from src.browser_agent import BrowserAgent, create_agent
from src.browser_tools import get_all_browser_tools

__all__ = ["BrowserAgent", "create_agent", "get_all_browser_tools"]
