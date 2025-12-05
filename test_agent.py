"""
Simple test script to verify the browser agent works.
Run with: python test_agent.py "your task here"
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

def test_browser_agent(task: str):
    """Run a simple browser task to test the agent."""
    from src.browser_agent import create_agent
    
    print(f"Testing browser agent with task: {task}")
    print("=" * 60)
    
    agent = None
    try:
        agent = create_agent(headless=True)
        result = agent.run(task)
        print(f"\nResult:\n{result}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if agent:
            agent.stop()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        task = "Go to google.com and tell me what you see on the page"
    else:
        task = " ".join(sys.argv[1:])
    
    test_browser_agent(task)
