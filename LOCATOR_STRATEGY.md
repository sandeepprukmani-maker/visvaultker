# Semantic Locator Strategy

## Overview

This tool uses a **3-stage pipeline** where semantic locators are used **from the very beginning**:

```
ExecutorAgent → CodeGeneratorAgent → HealerAgent
   (uses)          (preserves)         (improves)
  semantic         semantic            semantic
  locators         locators            locators
```

## Stage 1: ExecutorAgent (Browser Execution)

The ExecutorAgent **actually runs the browser** and uses semantic locators during execution:

### Locator Priority (Enforced During Execution):
1. **`get_by_role("button", name="Submit")`** - For buttons, links, headings, inputs
2. **`get_by_label("Email")`** - For form inputs with labels
3. **`get_by_placeholder("Enter email")`** - For inputs with placeholders
4. **`get_by_text("Sign In")`** - For unique visible text
5. **`get_by_test_id("login-btn")`** - For elements with test IDs
6. **CSS selectors** - ONLY as last resort

### What It Does:
- Opens real Chromium browser
- Uses Playwright MCP tools to interact with pages
- Records **execution trace** with semantic locators
- Example trace entry:
  ```json
  {
    "type": "tool_call",
    "tool": "playwright_click",
    "arguments": {
      "selector": "get_by_role(\"button\", name=\"Submit\")"
    }
  }
  ```

## Stage 2: CodeGeneratorAgent (Trace → Python Code)

The CodeGeneratorAgent converts the execution trace into clean Python:

### What It Does:
- **Preserves** the semantic locators from the trace
- Converts MCP tool calls to Playwright Python syntax:
  ```python
  # Trace: playwright_click with selector: 'get_by_role("button", name="Submit")'
  # Generated Code:
  await page.get_by_role("button", name="Submit").click()
  ```
- Adds proper async structure, imports, error handling
- Adds waits where needed

### Example Output:
```python
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to page
        await page.goto("https://example.com")
        await page.wait_for_load_state("networkidle")
        
        # Click submit button (semantic locator preserved from trace)
        await page.get_by_role("button", name="Submit").click()
        
        await browser.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Stage 3: HealerAgent (Auto-Fix If Needed)

If the generated script fails, the HealerAgent:
- Analyzes the error
- Improves locators (making them more robust)
- Adds proper waits
- Fixes timing issues

## Why This Approach?

### ✅ Advantages:
1. **Locators are discovered, not guessed** - Real browser execution finds working selectors
2. **Best practices from start** - Semantic locators used during execution
3. **Accurate traces** - Code generator gets high-quality input
4. **Reliable scripts** - Generated code uses proven locators
5. **Self-healing** - Auto-fixes if environment differs

### ❌ What We DON'T Do:
- ❌ Guess selectors based on AI knowledge
- ❌ Use fragile CSS selectors by default
- ❌ Generate code without testing it first
- ❌ Leave broken scripts for the user to fix

## Usage Example

```bash
# The tool will:
# 1. Run browser with semantic locators
# 2. Record trace with those locators
# 3. Generate Python code preserving them
python main.py "Go to example.com and click the More information link"
```

## Result Quality

**Input (Your Request):**
> "Fill out the contact form and submit"

**ExecutorAgent Trace:**
```json
[
  {"tool": "playwright_fill", "arguments": {"selector": "get_by_label(\"Name\")", "value": "John"}},
  {"tool": "playwright_fill", "arguments": {"selector": "get_by_label(\"Email\")", "value": "john@example.com"}},
  {"tool": "playwright_click", "arguments": {"selector": "get_by_role(\"button\", name=\"Submit\")"}}
]
```

**Generated Code:**
```python
await page.get_by_label("Name").fill("John")
await page.get_by_label("Email").fill("john@example.com")
await page.get_by_role("button", name="Submit").click()
```

**Notice:** The semantic locators flow from execution → trace → generated code, maintaining high quality throughout!
