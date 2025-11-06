#!/usr/bin/env python3
"""
Example usage of the Playwright MCP Automation Script Generator

This script demonstrates how to use the CLI tool to generate automation scripts.
"""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

EXAMPLES = """
# Playwright MCP Automation Script Generator

## Quick Start Examples

### Basic Usage
```bash
python main.py "Navigate to example.com and click the login button"
```

### Choose a different AI model
```bash
python main.py "Fill out the contact form" --model gpt4o
python main.py "Search for Python tutorials" --model gemini
```

### Custom output file
```bash
python main.py "Click the submit button" --output my_script.py
```

### Disable auto-healing
```bash
python main.py "Navigate to site" --no-heal
```

## Sample Tasks

### E-commerce
```bash
python main.py "Go to amazon.com, search for laptop, and add first result to cart"
```

### Form Filling
```bash
python main.py "Navigate to example.com/contact and fill out the contact form"
```

### Web Scraping
```bash
python main.py "Go to news.ycombinator.com and get the top 5 story titles"
```

### Testing
```bash
python main.py "Login to the app with test credentials and verify dashboard loads"
```

## Available Models

- **claude** (default) - Claude 4 Sonnet - Recommended for best results
- **gpt4o** - GPT-4o - Fast and capable
- **gemini** - Gemini 2.0 Flash - Google's latest

## Before You Start

Make sure you have set up your API keys:
- ANTHROPIC_API_KEY (for Claude)
- OPENAI_API_KEY (for GPT-4o)
- GEMINI_API_KEY (for Gemini)

## How It Works

1. 🤖 **Executor Agent** performs your task live in a browser using MCP
2. 📝 **Code Generator** creates a clean Python script from the execution
3. 🔧 **Auto-Healer** fixes any issues if the script fails (optional)

Your generated scripts will be saved in the `generated_scripts/` directory.
"""

console.print(Panel.fit(
    "[bold cyan]Playwright MCP Automation Script Generator[/bold cyan]",
    border_style="cyan"
))

md = Markdown(EXAMPLES)
console.print(md)

console.print("\n[bold yellow]Ready to generate automation scripts![/bold yellow]")
console.print("[dim]Run this tool with: python main.py \"your task description\"[/dim]\n")
