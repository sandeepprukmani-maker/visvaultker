import os
import sys
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

MCP_SERVER_COMMAND = "npx.cmd" if sys.platform == "win32" else "npx"
MCP_SERVER_ARGS = ["@playwright/mcp", "--headed"]

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

CRITICAL LOCATOR REQUIREMENTS:
1. ALWAYS use semantic locators in this EXACT priority order:
   a) page.get_by_role("button", name="Click Me") - for buttons, links, headings, textboxes
   b) page.get_by_label("Email") - for form inputs with labels
   c) page.get_by_placeholder("Enter email") - for inputs with placeholders
   d) page.get_by_text("Exact Text") - for unique text content
   e) page.get_by_test_id("submit-btn") - if test IDs are present
   f) page.locator("css") - ONLY as absolute last resort

2. NEVER use generic CSS selectors like ".class" or "#id" without trying semantic locators first

3. Add explicit waits for elements:
   - await page.wait_for_selector() when needed
   - Use expect(locator).to_be_visible() for verification

4. Structure:
   - Proper async/await patterns
   - All necessary imports
   - Error handling with try/except
   - Descriptive variable names
   - Comments explaining each step

Generate ONLY the Python code, no explanations."""

HEALER_SYSTEM_PROMPT = """You are a code debugging expert. Analyze failed Playwright scripts and fix broken locators.

CRITICAL HEALING RULES:
1. Identify the EXACT error cause from the error message
2. Replace fragile locators with robust semantic locators:
   - Use get_by_role() for buttons, links, headings
   - Use get_by_label() for form inputs
   - Use get_by_text() for unique text
   - AVOID CSS selectors unless absolutely necessary

3. Add proper waits:
   - await page.wait_for_load_state("networkidle")
   - await expect(locator).to_be_visible()
   - await page.wait_for_selector() for dynamic content

4. Add error handling with try/except blocks

5. Common fixes:
   - Timeout errors → Add waits
   - Element not found → Use semantic locators
   - Click intercepted → Wait for element to be visible and enabled

Generate ONLY the fixed Python code with ALL improvements applied, no explanations."""
