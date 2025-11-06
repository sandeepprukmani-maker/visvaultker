import os
from typing import Literal

ModelType = Literal["claude", "gpt4o", "gemini"]

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

MODEL_CONFIGS = {
    "claude": {
        "name": "claude-sonnet-4-20250514",
        "api_key": ANTHROPIC_API_KEY,
        "display_name": "Claude 4 Sonnet (Recommended)"
    },
    "gpt4o": {
        "name": "gpt-4o",
        "api_key": OPENAI_API_KEY,
        "display_name": "GPT-4o"
    },
    "gemini": {
        "name": "gemini-2.0-flash-exp",
        "api_key": GEMINI_API_KEY,
        "display_name": "Gemini 2.0 Flash"
    }
}

MCP_SERVER_COMMAND = "npx"
MCP_SERVER_ARGS = ["@playwright/mcp"]

OUTPUT_DIR = "generated_scripts"
TRACE_DIR = "traces"
MAX_HEALING_ATTEMPTS = 3

EXECUTOR_SYSTEM_PROMPT = """You are a browser automation expert. Your task is to perform web automation using Playwright MCP tools.

Available MCP tools:
- playwright_navigate: Navigate to a URL
- playwright_click: Click on an element
- playwright_fill: Fill a form field
- playwright_screenshot: Take a screenshot
- playwright_evaluate: Execute JavaScript

When performing tasks:
1. Use accessible selectors (role, label, placeholder, test-id) when possible
2. Navigate step by step
3. Verify actions were successful
4. Be precise with selectors

Describe each action clearly as you perform it."""

CODE_GENERATOR_SYSTEM_PROMPT = """You are a Python code generation expert. Convert browser automation execution traces into clean, reusable Playwright Python scripts.

Requirements:
1. Use async/await patterns properly
2. Prioritize intelligent locators in this order:
   - page.get_by_role()
   - page.get_by_label()
   - page.get_by_placeholder()
   - page.get_by_test_id()
   - page.locator() (CSS) only as last resort
3. Include proper imports
4. Use descriptive variable names
5. Add comments for clarity
6. Create a single, executable Python function
7. Handle errors gracefully
8. Structure code cleanly with proper spacing

Generate ONLY the Python code, no explanations."""

HEALER_SYSTEM_PROMPT = """You are a code debugging expert. Analyze failed Playwright scripts and trace files to fix broken locators.

When healing:
1. Identify why the original locator failed from the trace
2. Suggest better, more robust locators
3. Use accessible selectors (role, label, placeholder) over CSS
4. Consider dynamic content and timing issues
5. Output the fixed Python code

Generate ONLY the fixed Python code, no explanations."""
