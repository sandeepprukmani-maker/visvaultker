"""
Browser Automation Agent - Main Entry Point

Control your browser with natural language commands using AI.

Usage:
    python main.py                    # Interactive mode
    python main.py "Search for cats"  # Execute single task
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()


def print_banner():
    """Print welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════╗
║         Browser Automation Agent (smolagents)            ║
║                                                          ║
║  Control your browser with natural language commands!    ║
║                                                          ║
║  Commands:                                               ║
║    - Type any task to execute it                         ║
║    - Type 'quit' or 'exit' to stop                       ║
║    - Type 'help' for example commands                    ║
╚══════════════════════════════════════════════════════════╝
""")


def print_help():
    """Print help with example commands."""
    print("""
Example tasks you can give:
  - "Go to google.com and search for Python tutorials"
  - "Navigate to github.com and find the trending repositories"
  - "Go to news.ycombinator.com and get the top 5 headlines"
  - "Visit wikipedia.org and search for artificial intelligence"
  - "Go to amazon.com and search for wireless headphones"

Tips:
  - Be specific about what you want to accomplish
  - The agent will show its thinking and actions as it works
  - Screenshots are saved to screenshot.png
""")


def check_api_key():
    """Check if OpenAI API key is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[ERROR] OPENAI_API_KEY environment variable is not set!")
        print("Please set your OpenAI API key to use this agent.")
        print("\nYou can set it by:")
        print("  1. Adding it to a .env file: OPENAI_API_KEY=your-key-here")
        print("  2. Or setting it in your environment")
        return False
    return True


def run_interactive():
    """Run the agent in interactive mode."""
    from src.browser_agent import create_agent
    
    print_banner()
    
    if not check_api_key():
        return
    
    print("Starting browser agent (this may take a moment)...")
    
    agent = None
    try:
        agent = create_agent(headless=True)
        
        print("\nAgent ready! Enter your tasks below.\n")
        
        while True:
            try:
                task = input("\n🌐 Enter task: ").strip()
                
                if not task:
                    continue
                
                if task.lower() in ["quit", "exit", "q"]:
                    break
                
                if task.lower() == "help":
                    print_help()
                    continue
                
                result = agent.run(task)
                print(f"\n✅ Result: {result}")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user.")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
    
    finally:
        if agent is not None:
            agent.stop()


def run_single_task(task: str):
    """Run a single task and exit."""
    from src.browser_agent import create_agent
    
    if not check_api_key():
        return
    
    print(f"Executing task: {task}\n")
    
    agent = None
    try:
        agent = create_agent(headless=True)
        result = agent.run(task)
        print(f"\n✅ Result: {result}")
    finally:
        if agent is not None:
            agent.stop()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        run_single_task(task)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
