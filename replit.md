# Browser Automation Agent (smolagents)

## Overview
An AI-powered browser automation tool using the smolagents framework. Control your browser with natural language commands - the AI agent will navigate, click, type, and interact with web pages on your behalf.

## Features
- Natural language task input for browser automation
- AI-powered action planning using OpenAI GPT-4
- Browser control capabilities (navigate, click, type, scroll)
- Real-time action logging showing what the agent is doing
- Web-based UI for easy command input
- CLI interface for scripting

## Project Structure
```
├── app.py                  # Flask web interface (main entry)
├── main.py                 # CLI interface for command-line usage
├── test_agent.py           # Test script
├── src/
│   ├── __init__.py         # Package exports
│   ├── browser_agent.py    # Main BrowserAgent class using smolagents
│   └── browser_tools.py    # Browser automation tools (Playwright-based)
└── .gitignore
```

## Dependencies
- **smolagents**: Hugging Face's AI agent framework
- **litellm**: LLM API abstraction layer
- **playwright**: Browser automation library
- **flask**: Web framework for the UI
- **pillow**: Image processing for screenshots
- **python-dotenv**: Environment variable management

## Usage

### Web Interface (Default)
Run the workflow and use the web UI to enter commands like:
- "Go to google.com and search for Python tutorials"
- "Navigate to github.com and find trending repositories"
- "Go to news.ycombinator.com and get the top headlines"

### CLI Mode
```bash
python main.py                                    # Interactive mode
python main.py "Go to google.com and search for Python"  # Single task
```

### Test Script
```bash
python test_agent.py "your task here"
```

## Configuration
Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key for AI-powered task planning
- `SESSION_SECRET`: Session secret for Flask (optional, auto-generated)

## Browser Tools Available
- `navigate_to_url`: Go to a specific URL
- `click_element`: Click using CSS selector
- `click_text`: Click on visible text
- `type_text`: Type into input fields
- `press_key`: Press keyboard keys (Enter, Tab, etc.)
- `scroll_page`: Scroll up or down
- `get_page_content`: Get text content of the page
- `get_page_elements`: List interactive elements
- `take_screenshot`: Capture current state
- `wait_for_element`: Wait for element to appear
- `go_back`: Navigate back in history
- `refresh_page`: Refresh current page

## Recent Changes
- Dec 2024: Initial project setup
- Created browser automation tools using Playwright
- Integrated smolagents CodeAgent for LLM-powered browser control
- Added Flask web UI for easy command input
- Added CLI interface for scripting
- Configured system Chromium for NixOS compatibility

## User Preferences
- Headless browser mode for server environment
- Web-based interface for easy interaction
