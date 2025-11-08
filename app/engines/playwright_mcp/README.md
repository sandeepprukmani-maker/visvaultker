# Playwright MCP Engine - Enhanced with Multi-Locator Strategies & Intelligence

This enhanced Playwright MCP engine includes robust locator strategies, execution tracing, automatic code healing, **persistent MCP connections for blazing-fast performance**, and **highly intelligent AI agents** with diagnostic capabilities.

## Key Features

### 0. ⚡ Persistent MCP Client (Performance Enhancement)
The engine now maintains a **persistent, pre-warmed MCP client** that eliminates the 5-second cold start on every task:

- **First task**: ~5 seconds to start MCP server + execute task
- **Subsequent tasks**: ~0.1 seconds (reuses existing connection)
- **Health checks**: Automatic connection validation and reconnection
- **Thread-safe**: Async locks prevent race conditions
- **Lazy initialization**: Lock created only when needed (no import-time errors)

This results in **50x faster** automation for repeat tasks!

### 1. Rich Reusable Locators
The engine now uses multiple locator strategies with automatic fallbacks:

- `page.get_by_role()` - Most robust, uses ARIA roles
- `page.get_by_label()` - For form fields with labels
- `page.get_by_placeholder()` - For inputs with placeholders
- `page.get_by_text()` - For elements with specific text
- `page.get_by_test_id()` - For elements with test IDs
- `page.locator()` - CSS/XPath selectors (last resort)

### 2. Enhanced Execution Traces
Execution traces now include detailed locator information:

```python
{
  "type": "tool_call",
  "tool": "playwright_click",
  "arguments": {"selector": "button.submit"},
  "locator_info": {
    "action": "playwright_click",
    "selectors": [
      {"type": "role", "value": "button", "name": "Submit"},
      {"type": "text", "value": "Submit"},
      {"type": "css", "value": "button.submit"}
    ]
  }
}
```

This allows the code generator to reuse the same robust locators from the execution.

### 3. HealerAgent - Automatic Code Fixing
The HealerAgent can automatically fix failed scripts by:

- Analyzing error messages
- Using execution traces to understand what worked
- Implementing multi-locator fallback strategies
- Adding proper waits and error handling

### 4. 🧠 Highly Intelligent AI Agents
All three AI agents (Executor, Generator, Healer) have been enhanced with **diagnostic intelligence** and **contextual awareness**:

#### MCPExecutorAgent Intelligence
- **Context Awareness**: Analyzes page state before taking actions (modals, popups, dynamic content)
- **Adaptive Strategy**: Chooses optimal locators based on element type and context
- **Predictive Thinking**: Anticipates timing issues, overlays, and dynamic content
- **Smart Waiting**: Uses networkidle, domcontentloaded, and element readiness waits
- **Comprehensive Identification**: Records primary + backup identifiers for every element
- **Error Prevention**: Proactively validates page state and handles edge cases

#### CodeGeneratorAgent Intelligence
- **Production-Grade Code**: Generates defensive, maintainable code with proper error handling
- **Multi-Level Fallbacks**: Implements trace-based → accessible → contextual → CSS locators
- **Context-Aware Waits**: Analyzes execution traces to add appropriate waits
- **Structural Patterns**: Recognizes common workflows (login, forms, search) and applies best practices
- **Performance Optimization**: Batches operations, minimizes unnecessary waits
- **Meta-Intelligence**: Studies trace timing, identifies error-prone steps, considers edge cases

#### HealerAgent Intelligence
- **Root Cause Analysis**: Diagnoses WHY automation failed, not just WHAT failed
- **Progressive Healing**: Multi-level strategy with retry logic and exponential backoff
- **Intelligent Rewriting**: Transforms brittle code → robust code (surgical fixes, not rewrites)
- **Diagnostic Framework**: Maps error symptoms to root causes (timeouts, detached frames, selectors)
- **Context-Aware Fixes**: Analyzes error messages for clues and uses trace data intelligently
- **Preventive Measures**: Adds safeguards to prevent similar failures (not just bandaids)

These enhancements make the agents **think like experienced QA engineers** - they don't just execute actions, they understand context, anticipate problems, and implement robust solutions.

## Usage Examples

### Basic Automation Task

```python
from app.engines.playwright_mcp import PlaywrightMCPEngine

engine = PlaywrightMCPEngine()

result = await engine.run_task(
    task_description="Go to example.com and click the login button",
    headless=True,
    model_name="gpt-4o"
)

print(result["generated_code"])
```

### Using Individual Agents

```python
from app.engines.playwright_mcp import MCPExecutorAgent, CodeGeneratorAgent, HealerAgent
from app.engines.playwright_mcp.mcp_client import PlaywrightMCPClient

# 1. Execute task with MCP client
async with PlaywrightMCPClient("npx", ["@playwright/mcp"]) as mcp_client:
    # Execute automation
    executor = MCPExecutorAgent(
        model_name="gpt-4o",
        api_key=api_key,
        mcp_client=mcp_client
    )
    
    result = await executor.execute_task("Navigate to example.com and search for 'playwright'")
    execution_trace = result["trace"]
    
    # Generate code from trace
    generator = CodeGeneratorAgent(
        model_name="gpt-4o",
        api_key=api_key
    )
    
    code = await generator.generate_code(
        execution_trace=execution_trace,
        task_description="Search example.com for 'playwright'"
    )
    
    print(code)
```

### Using HealerAgent to Fix Failed Code

```python
from app.engines.playwright_mcp import HealerAgent

healer = HealerAgent(
    model_name="gpt-4o",
    api_key=api_key
)

# Original code that failed
failed_code = '''
async def automate():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        await page.click("button.submit")  # This selector is fragile
        await browser.close()
'''

error_message = "TimeoutError: locator.click: Timeout 30000ms exceeded"

# Heal the code with multi-locator strategies
fixed_code = await healer.heal_code(
    original_code=failed_code,
    error_message=error_message,
    execution_trace=execution_trace  # Optional, helps with context
)

print(fixed_code)
```

### Expected Output - Code with Multi-Locator Fallbacks

The healer will generate code with robust locator strategies:

```python
async def automate():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        
        # Try multiple locator strategies with fallbacks
        submit_button = None
        strategies = [
            ("role", lambda: page.get_by_role("button", name="Submit")),
            ("text", lambda: page.get_by_text("Submit")),
            ("label", lambda: page.get_by_label("Submit")),
            ("css", lambda: page.locator("button.submit")),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                submit_button = strategy_func()
                await submit_button.wait_for(state="visible", timeout=5000)
                print(f"Located button using {strategy_name} strategy")
                break
            except Exception as e:
                print(f"{strategy_name} strategy failed: {e}")
                continue
        
        if submit_button:
            await submit_button.click()
        else:
            raise Exception("Could not locate submit button with any strategy")
        
        await browser.close()
```

## Benefits

### 1. More Reliable Automation
- Multiple fallback locators ensure scripts work even if page structure changes
- Accessible selectors (role, label) are more stable than CSS selectors

### 2. Better Generated Code
- Code generator uses exact locator information from execution trace
- Implements best practices automatically

### 3. Self-Healing Scripts
- HealerAgent can fix broken scripts automatically
- Adds robust error handling and retry logic

### 4. Reduced Maintenance
- Multi-locator strategies reduce script breakage
- Less manual intervention needed when pages change

## Configuration

The engine uses the following system prompts for enhanced locator strategies:

- `EXECUTOR_SYSTEM_PROMPT` - Guides executor to identify multiple locator options
- `CODE_GENERATOR_SYSTEM_PROMPT` - Instructs generator to use multi-locator fallbacks
- `HEALER_SYSTEM_PROMPT` - Teaches healer to fix scripts with robust patterns

These prompts emphasize:
- Trying multiple locator strategies
- Recording all locator options in traces
- Implementing fallback mechanisms
- Adding proper waits and error handling

## Architecture

```
PlaywrightMCPEngine
├── MCPExecutorAgent
│   ├── Executes tasks via MCP protocol
│   ├── Records enhanced traces with locator info
│   └── Uses multiple locator strategies
├── CodeGeneratorAgent
│   ├── Generates code from execution traces
│   └── Implements multi-locator fallbacks
└── HealerAgent
    ├── Analyzes failed scripts
    └── Fixes with robust locator patterns
```

## Advanced Features

### Execution Trace with Locator Information

The executor now captures detailed locator information for each action:

```python
trace_entry = {
    "type": "tool_call",
    "tool": "playwright_fill",
    "arguments": {
        "selector": "#email",
        "value": "user@example.com"
    },
    "locator_info": {
        "action": "playwright_fill",
        "selectors": [
            {"type": "label", "value": "Email"},
            {"type": "placeholder", "value": "Enter your email"},
            {"type": "css", "value": "#email"}
        ]
    }
}
```

This rich information allows the code generator to create more robust scripts.

## Best Practices

1. **Always use execution traces**: Pass the trace to HealerAgent for better context
2. **Start with accessible locators**: Role, label, and text are most stable
3. **Implement fallbacks**: Multiple strategies prevent single points of failure
4. **Add proper waits**: Use `wait_for()` to ensure elements are ready
5. **Log strategy usage**: Help debug which locators work best

## Migration Guide

If you're using the old engine, the new version is backward compatible. Enhanced features are automatic:

```python
# Old way - still works
result = await engine.run_task("Click the submit button")

# New way - same interface, better results
result = await engine.run_task("Click the submit button")
# Now includes multi-locator strategies automatically!
```

## Troubleshooting

### Script still fails after healing?
- Check if the element actually exists on the page
- Try running in headful mode to debug visually
- Review the execution trace for clues

### Generated code is too complex?
- The multi-locator pattern ensures reliability
- You can simplify if you know the page structure is stable

### Need custom locator strategies?
- Modify `_extract_locator_info()` in `MCPExecutorAgent`
- Update system prompts to emphasize your preferred strategies
