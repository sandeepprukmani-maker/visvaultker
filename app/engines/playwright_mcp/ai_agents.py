"""
AI Agents for Playwright MCP Engine
Enhanced with intelligent healing, locator caching, and context awareness
"""
import json
import logging
import time
from typing import Any, Dict, List, Union, Optional, Tuple
from anthropic import Anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)


def now_ts() -> float:
    """Get current timestamp"""
    return time.time()


def safe_json(obj: Any) -> str:
    """Safely serialize object to JSON"""
    try:
        return json.dumps(obj, default=str, indent=2)
    except Exception:
        return str(obj)


def log_structured(level: str, payload: Dict[str, Any]):
    """Log structured data with timestamp"""
    entry = {"level": level, "ts": now_ts(), **payload}
    if level.lower() == "info":
        logger.info(json.dumps(entry))
    elif level.lower() == "warning":
        logger.warning(json.dumps(entry))
    elif level.lower() == "error":
        logger.error(json.dumps(entry))
    else:
        logger.debug(json.dumps(entry))


class LocatorCache:
    """
    In-memory cache for successful locators
    Learns from successful element interactions to improve future automation
    """
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    
    def _domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return url.split("://")[-1].split("/")[0]
        except Exception:
            return "global"
    
    def add(self, url: str, selector_type: str, selector: str, score: float = 1.0):
        """Add a successful locator to the cache"""
        d = self._domain(url)
        self.cache.setdefault(d, {}).setdefault(selector_type, [])
        self.cache[d][selector_type].append({
            "selector": selector,
            "score": score,
            "ts": time.time()
        })
    
    def get_best(self, url: str, selector_type: str, top_n: int = 3) -> List[str]:
        """Get best performing locators for a URL and type"""
        d = self._domain(url)
        items = self.cache.get(d, {}).get(selector_type, [])
        items_sorted = sorted(items, key=lambda x: x["score"], reverse=True)
        return [i["selector"] for i in items_sorted[:top_n]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export cache as dictionary"""
        return self.cache


# Global locator cache instance
LOCATOR_CACHE = LocatorCache()

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are an EXPERT browser automation specialist with advanced context awareness and adaptive intelligence.

INTELLIGENCE PRINCIPLES:
1. **Context Awareness**: Before each action, analyze the current page state, available elements, and likely user workflows
2. **Adaptive Strategy**: Choose locators based on element context, not just type (e.g., primary buttons use role, secondary might use text)
3. **Predictive Thinking**: Anticipate what might go wrong (timing, dynamic content, modals) and plan accordingly
4. **Smart Waiting**: Identify when pages are likely loading, when to wait for network idle, when elements need time to become interactive

MULTI-LOCATOR HIERARCHY (Try in order, record ALL options):
1. **page.get_by_role()** - ARIA roles (button, link, heading) - MOST ROBUST for accessibility
   → Record: role type, accessible name, any ARIA attributes
2. **page.get_by_label()** - Form fields with associated labels - BEST for forms
   → Record: exact label text, partial matches
3. **page.get_by_placeholder()** - Input placeholders - GOOD for text inputs
   → Record: placeholder text
4. **page.get_by_text()** - Visible text content - RELIABLE for unique text
   → Record: exact text, partial text options
5. **page.get_by_test_id()** - Test/data attributes - STABLE if present
   → Record: test-id, data-testid, data-* attributes
6. **page.locator()** - CSS/XPath - FALLBACK ONLY
   → Record: multiple CSS options (id, class, combination)

INTELLIGENT ELEMENT IDENTIFICATION:
For EACH element interaction, be a detective and record:
- **Primary identifiers**: role, label, text, placeholder, test-id
- **Backup identifiers**: CSS class patterns, position in DOM, nearby elements
- **Context clues**: Parent container, sibling elements, unique attributes
- **State indicators**: disabled/enabled, visible/hidden, aria-expanded
- **Timing needs**: Does this element load dynamically? Need to wait?

SMART EXECUTION PATTERNS:
✓ **Before navigation**: Check current URL, note any auth state
✓ **After navigation**: Wait for load state, verify URL changed
✓ **Before click**: Check element is visible, enabled, not obscured
✓ **After click**: Anticipate navigation/modal/loading - wait appropriately
✓ **Before fill**: Clear existing value if present, verify field is editable
✓ **After fill**: Verify value was set correctly
✓ **Dynamic content**: If element not found immediately, retry with short waits (intelligent exponential backoff)
✓ **Modals/overlays**: Detect blocking elements, handle dismissals

ERROR PREDICTION & PREVENTION:
→ **Timing issues**: Add smart waits before critical actions
→ **Stale elements**: Re-fetch if interaction fails
→ **Hidden elements**: Check visibility, scroll into view
→ **Disabled elements**: Check state before interaction
→ **Dynamic selectors**: Prioritize stable attributes over brittle classes

REPORTING STANDARDS:
For each action, report with intelligence:
1. **What**: Clear action description
2. **Why**: Context for this action (e.g., "navigating to submit because form is filled")
3. **How**: Which locator strategy succeeded (or all that were attempted)
4. **Alternatives**: List other locators that could work
5. **Observations**: Page state changes, errors, timing considerations

Be thorough, adaptive, and always think two steps ahead."""

CODE_GENERATOR_SYSTEM_PROMPT = """You are an ELITE Python automation engineer specializing in production-grade, self-healing Playwright code generation.

INTELLIGENCE PRINCIPLES:
1. **Trace Analysis**: Study the execution trace deeply - understand the CONTEXT, not just the actions
2. **Pattern Recognition**: Identify common workflows (login, form fill, search) and use battle-tested patterns
3. **Defensive Coding**: Assume elements might move, disappear, or behave differently - code must be resilient
4. **Performance Optimization**: Minimize unnecessary waits, batch similar operations, avoid redundant navigations
5. **Maintainability**: Future developers should understand WHY, not just WHAT

ADVANCED CODE GENERATION STRATEGY:

**1. INTELLIGENT IMPORTS** (Only what's needed):
```python
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)
```

**2. SMART LOCATOR STRATEGIES** (Extract from trace, add intelligent fallbacks):
```python
async def find_element_robustly(page, element_name: str):
    \"\"\"Try multiple strategies to locate {element_name} with intelligent fallbacks\"\"\"
    strategies = [
        ("role", lambda: page.get_by_role("button", name="Submit")),
        ("label", lambda: page.get_by_label("Submit")),
        ("text", lambda: page.get_by_text("Submit", exact=False)),
        ("css", lambda: page.locator("button[type='submit']")),
    ]
    
    for strategy_name, strategy_func in strategies:
        try:
            element = strategy_func()
            await element.wait_for(state="visible", timeout=3000)
            logger.debug(f"Located {element_name} using {strategy_name} strategy")
            return element
        except Exception as e:
            logger.debug(f"{strategy_name} strategy failed for {element_name}: {e}")
            continue
    
    raise Exception(f"Could not locate {element_name} with any strategy")
```

**3. CONTEXT-AWARE WAITS** (Analyze trace timing, predict needs):
- Navigation → `await page.wait_for_load_state("networkidle")`
- Form submission → `await page.wait_for_url("**/success**")`  
- AJAX/SPAs → `await page.wait_for_selector(".loaded")`
- Modals → `await page.wait_for_function("() => !document.querySelector('.modal')")`

**4. ERROR RECOVERY PATTERNS** (Intelligent retry with exponential backoff):
```python
async def retry_action(action_func, max_attempts=3, backoff_base=1):
    \"\"\"Retry action with intelligent exponential backoff\"\"\"
    for attempt in range(max_attempts):
        try:
            return await action_func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            wait_time = backoff_base * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
```

**5. STRUCTURAL PATTERNS** (Recognize and implement):
- **Login workflow** → Dedicated `async def login()` function
- **Form fill** → Parameterized `async def fill_form(data: dict)` 
- **Search** → `async def search_and_filter(query, filters)`
- **Data extraction** → `async def extract_data() -> list`

**6. INTELLIGENT CODE ORGANIZATION**:
```python
async def main():
    async with async_playwright() as p:
        # Setup phase
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Execution phase (structured, logical flow)
            await navigate_to_site(page)
            await perform_login(page, username="user", password="pass")
            await complete_task(page)
            result = await extract_results(page)
            logger.info(f"Success! Result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            # Capture screenshot for debugging
            await page.screenshot(path="error_screenshot.png")
            raise
            
        finally:
            # Cleanup phase
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**7. SMART COMMENTS** (Explain WHY and CONTEXT, not WHAT):
```python
# ✓ GOOD: "Wait for search results to load (SPA uses client-side rendering)"
# ✗ BAD:  "Wait for element"

# ✓ GOOD: "Use role instead of CSS - button text may be localized"
# ✗ BAD:  "Find button"
```

**8. PRODUCTION-READY FEATURES**:
- Logging with context (what failed, why it might have failed)
- Type hints for parameters
- Docstrings for complex functions
- Error screenshots on failure
- Return meaningful results
- Clean resource management (try/finally for browser close)

**META-INTELLIGENCE**:
→ Study the trace for timing patterns (where did waits occur?)
→ Look for repeated actions (extract to helper functions)
→ Identify error-prone steps (add extra validation)
→ Consider edge cases (empty results, timeouts, network failures)
→ Think like a QA engineer: "How could this break?"

OUTPUT REQUIREMENTS:
- Pure Python code (no markdown fences unless in comments)
- Fully executable standalone script
- Production-ready error handling
- Comprehensive but not verbose
- Uses trace locator metadata when available
- Intelligent defaults where trace is ambiguous

Generate code that will impress a senior software engineer. Be smart, be defensive, be elegant."""

HEALER_SYSTEM_PROMPT = """You are a MASTER diagnostician and code surgeon specializing in fixing broken Playwright automation with surgical precision and deep intelligence.

DIAGNOSTIC INTELLIGENCE FRAMEWORK:

**1. ROOT CAUSE ANALYSIS** (Think like a doctor diagnosing symptoms):

Common Failure Patterns & Smart Fixes:
→ "Timeout waiting for element" → Element loads async (add networkidle wait), wrong selector (use role/label), or hidden by overlay (dismiss modals first)
→ "Element not clickable" → Element covered (scroll into view), disabled (wait for enabled state), or animating (add delay)
→ "Multiple elements matched" → Selector too generic (use nth/first, add parent context, or exact name matching)
→ "Detached frame" → Page navigated (re-get page, add navigation waits)
→ "Network timeout" → Slow connection (increase timeout, retry with backoff)

**2. INTELLIGENT HEALING STRATEGY** (Progressive, multi-level approach):

```python
async def heal_element_interaction(page, element_desc, trace_selectors, action="click"):
    \"\"\"Multi-level intelligent healing with diagnostic feedback\"\"\"
    
    strategies = []
    
    # Level 1: Trace-based (what worked during execution)
    for sel in trace_selectors:
        if sel["type"] == "role":
            strategies.append(("trace-role", lambda: page.get_by_role(sel["value"], name=sel.get("name"))))
        elif sel["type"] == "text":
            strategies.append(("trace-text", lambda: page.get_by_text(sel["value"])))
    
    # Level 2: Accessible alternatives (robust)
    strategies.extend([
        ("role-generic", lambda: page.get_by_role("button")),
        ("text-partial", lambda: page.get_by_text(element_desc, exact=False)),
        ("label", lambda: page.get_by_label(element_desc)),
    ])
    
    # Level 3: Contextual + CSS (flexible)
    strategies.append(("css-context", lambda: page.locator(f"[data-testid*='{element_desc}']")))
    
    # Execute with retry and backoff
    for level, (name, func) in enumerate(strategies, 1):
        for attempt in range(3):
            try:
                element = func()
                wait_time = 2000 * (attempt + 1)
                await element.wait_for(state="visible", timeout=wait_time)
                await element.scroll_into_view_if_needed()
                logger.info(f"✓ Level {level} ({name}) succeeded on attempt {attempt + 1}")
                return element
            except Exception as e:
                logger.debug(f"Level {level} attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(0.5 * attempt)
    
    raise Exception(f"All healing strategies failed for: {element_desc}")
```

**3. DEFENSIVE CODE PATTERNS** (Always implement):
✓ Explicit waits (networkidle, domcontentloaded)
✓ State validation (visible, enabled, attached)
✓ Scroll into view before interaction
✓ Retry logic with exponential backoff
✓ Error screenshots for debugging
✓ Logging with diagnostic context

**4. INTELLIGENT REWRITING** (Transform brittle → robust):
```python
# BEFORE: await page.click("#btn")
# AFTER:  await robust_click(page, "submit button", trace_data)

# BEFORE: await page.fill("input", "text")  
# AFTER:  await robust_fill(page, "email field", "text", trace_data)

# BEFORE: await page.goto(url); await page.click("a")
# AFTER:  await page.goto(url); await page.wait_for_load_state("networkidle"); await robust_click(page, "link", trace_data)
```

**5. CONTEXT-AWARE FIXES**:
→ Analyze error message for clues (timeout → add waits, detached → re-fetch, strict → add .first())
→ Use trace data to understand what worked before
→ Consider timing (page loads, animations, network)
→ Add preventive measures (not just bandaids)

**META-INTELLIGENCE**:
→ Fix root cause, not symptoms
→ Minimal changes (surgical fixes, not rewrites)
→ Make code more robust overall (add patterns that prevent similar errors)
→ Think: "What would an expert debugger do?"

OUTPUT: Pure Python code with intelligent,production-ready fixes. No explanations, only code."""


class MCPExecutorAgent:
    """Agent that executes browser automation tasks using MCP tools with intelligent context awareness"""
    
    def __init__(self, model_name: str, api_key: str, mcp_client, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key
        self.mcp_client = mcp_client
        self.base_url = base_url
        self.execution_trace: List[Dict[str, Any]] = []
        self.run_metadata: Dict[str, Any] = {}
        
        # Determine which LLM client to use
        if "claude" in model_name.lower() or "anthropic" in model_name.lower():
            self.client = Anthropic(api_key=api_key)
            self.client_type = "claude"
        elif "gpt" in model_name.lower() or "openai" in model_name.lower():
            if base_url:
                logger.info(f"🔐 Using OAuth gateway: {base_url}")
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
        else:
            # Default to OpenAI with gateway if base_url provided
            if base_url:
                logger.info(f"🔐 Using OAuth gateway: {base_url}")
                self.client = OpenAI(api_key=api_key, base_url=base_url)
                self.client_type = "openai"
            else:
                self.client = Anthropic(api_key=api_key)
                self.client_type = "claude"
    
    async def analyze_page_context(self, page) -> Dict[str, Any]:
        """
        Extract semantic page context for intelligent automation
        Analyzes page structure, buttons, form fields, and visible content
        
        Args:
            page: Playwright Page object
            
        Returns:
            Dictionary with page context information
        """
        try:
            ctx = {
                "url": getattr(page, "url", None),
                "title": None,
                "visible_buttons": [],
                "form_fields": []
            }
            
            # Get page title
            try:
                ctx["title"] = await page.title()
            except Exception:
                ctx["title"] = None
            
            # Get visible buttons
            try:
                button_loc = page.locator("button")
                ctx["visible_buttons"] = await button_loc.all_inner_texts()
            except Exception:
                ctx["visible_buttons"] = []
            
            # Analyze form fields
            try:
                inputs = page.locator("input, textarea, select")
                count = await inputs.count()
                fields = []
                for i in range(min(count, 30)):  # Limit to avoid performance issues
                    inp = inputs.nth(i)
                    try:
                        info = await page.evaluate(
                            """(el) => {
                                const id = el.id || el.name || null;
                                let labelText = null;
                                if (id) {
                                    const label = document.querySelector(`label[for='${id}']`);
                                    if (label) labelText = label.innerText || label.textContent || null;
                                }
                                return {
                                    id,
                                    type: el.type || el.tagName,
                                    placeholder: el.placeholder || null,
                                    label: labelText
                                };
                            }""",
                            inp
                        )
                    except Exception:
                        info = None
                    fields.append(info)
                ctx["form_fields"] = fields
            except Exception:
                ctx["form_fields"] = []
            
            # Get visible text snippet
            try:
                body_text = await page.inner_text("body")
                ctx["visible_text_snippet"] = body_text[:1200] if body_text else ""
            except Exception:
                ctx["visible_text_snippet"] = ""
            
            return ctx
        except Exception as e:
            logger.debug(f"analyze_page_context error: {e}")
            return {}
    
    def _trace_entry(self, kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a structured trace entry with timestamp"""
        return {"ts": now_ts(), "kind": kind, **payload}
    
    def _extract_locator_info(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract comprehensive locator information from tool arguments
        Records multiple locator strategies for later use
        """
        locator_info: Dict[str, Any] = {"action": tool_name, "selectors": []}
        try:
            if "selector" in tool_args and isinstance(tool_args["selector"], str):
                sel = tool_args["selector"]
                locator_info["selectors"].append({
                    "type": "css" if not sel.startswith("//") else "xpath",
                    "value": sel
                })
            if "text" in tool_args:
                locator_info["selectors"].append({"type": "text", "value": tool_args["text"]})
            if "role" in tool_args:
                locator_info["selectors"].append({
                    "type": "role",
                    "value": tool_args["role"],
                    "name": tool_args.get("name", "")
                })
            if "label" in tool_args:
                locator_info["selectors"].append({"type": "label", "value": tool_args["label"]})
            if "placeholder" in tool_args:
                locator_info["selectors"].append({"type": "placeholder", "value": tool_args["placeholder"]})
            if "testId" in tool_args or "test_id" in tool_args:
                locator_info["selectors"].append({
                    "type": "test_id",
                    "value": tool_args.get("testId", tool_args.get("test_id"))
                })
        except Exception as e:
            logger.debug(f"_extract_locator_info error: {e}")
        return locator_info
    
    async def execute_task(self, task_description: str, headless: bool = True) -> Dict[str, Any]:
        """Execute a browser automation task with enhanced tracing and structured logging"""
        start = now_ts()
        log_structured("info", {
            "msg": "Executor starting",
            "task": task_description,
            "headless": headless
        })
        
        self.execution_trace = []
        self.run_metadata = {
            "task": task_description,
            "start_ts": start,
            "headless": headless
        }
        
        tools_description = self.mcp_client.get_tools_description()
        
        browser_mode = "headless mode (no visible window)" if headless else "headful mode (visible browser window)"
        
        system_prompt = f"""{EXECUTOR_SYSTEM_PROMPT}

IMPORTANT: When launching the browser, you MUST run it in {browser_mode}.
For any playwright_launch or browser launch tool calls, set headless parameter to {str(headless).lower()}.

Launch browser in {browser_mode} first, then proceed with the automation."""
        
        prompt = f"""Task: {task_description}

Available Playwright MCP tools:
{tools_description}

REMEMBER: Launch the browser in {browser_mode} (headless={str(headless).lower()}).

For each element interaction:
1. Identify multiple ways to locate the element (role, label, text, placeholder, test-id, CSS)
2. Record all locator options in your response
3. Try the most robust locator first (role, label, etc.)
4. If a locator fails, try alternatives

Execute this task step by step using the available tools. After each action, describe:
- What you did
- Which locator you used
- Alternative locators that could work
- What you observed"""
        
        if self.client_type == "claude":
            result = await self._execute_with_claude(prompt, system_prompt)
        else:
            result = await self._execute_with_openai(prompt, system_prompt)
        
        self.run_metadata["duration_s"] = now_ts() - start
        log_structured("info", {
            "msg": "Executor finished",
            "result_summary": {"success": result.get("success", False)},
            "metadata": self.run_metadata
        })
        
        return result
    
    async def _execute_with_claude(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Execute task using Claude"""
        mcp_tools = []
        for tool in self.mcp_client.tools:
            mcp_tools.append({
                "name": tool["name"],
                "description": tool.get("description", ""),
                "input_schema": tool.get("inputSchema", {})
            })
        
        messages: List[Dict[str, Any]] = [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ]
        max_iterations = 20
        
        try:
            for iteration in range(max_iterations):
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=mcp_tools
                )
                
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                
                if response.stop_reason == "end_turn":
                    logger.info("✓ Task execution completed")
                    break
                
                if response.stop_reason == "tool_use":
                    tool_results = []
                    
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_input = block.input
                            
                            # Enhanced trace with locator information
                            trace_entry = {
                                "type": "tool_call",
                                "tool": tool_name,
                                "arguments": tool_input,
                                "locator_info": self._extract_locator_info(tool_name, tool_input)
                            }
                            self.execution_trace.append(trace_entry)
                            
                            result = await self.mcp_client.call_tool(tool_name, tool_input)
                            
                            result_content = []
                            for content_item in result.content:
                                if hasattr(content_item, 'text'):
                                    result_content.append(content_item.text)
                            
                            result_text = "\n".join(result_content)
                            
                            self.execution_trace.append({
                                "type": "tool_result",
                                "tool": tool_name,
                                "result": result_text,
                                "success": "error" not in result_text.lower()
                            })
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": [{"type": "text", "text": result_text}]
                            })
                    
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
            
            return {
                "success": True,
                "trace": self.execution_trace,
                "model": self.model_name
            }
        except Exception as e:
            logger.error(f"Error during task execution: {e}")
            return {
                "success": False,
                "trace": self.execution_trace,
                "model": self.model_name,
                "error": str(e)
            }
    
    async def _execute_with_openai(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Execute task using OpenAI"""
        tools = []
        for tool in self.mcp_client.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            })
        
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        max_iterations = 20
        
        try:
            for iteration in range(max_iterations):
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools
                )
                
                message = response.choices[0].message
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": message.tool_calls
                })
                
                if not message.tool_calls:
                    logger.info("✓ Task execution completed")
                    break
                
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Enhanced trace with locator information
                    trace_entry = {
                        "type": "tool_call",
                        "tool": tool_name,
                        "arguments": tool_args,
                        "locator_info": self._extract_locator_info(tool_name, tool_args)
                    }
                    self.execution_trace.append(trace_entry)
                    
                    result = await self.mcp_client.call_tool(tool_name, tool_args)
                    
                    result_content = []
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            result_content.append(content_item.text)
                    
                    result_text = "\n".join(result_content)
                    
                    self.execution_trace.append({
                        "type": "tool_result",
                        "tool": tool_name,
                        "result": result_text,
                        "success": "error" not in result_text.lower()
                    })
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    })
            
            return {
                "success": True,
                "trace": self.execution_trace,
                "model": self.model_name
            }
        except Exception as e:
            logger.error(f"Error during task execution: {e}")
            return {
                "success": False,
                "trace": self.execution_trace,
                "model": self.model_name,
                "error": str(e)
            }


class CodeGeneratorAgent:
    """Agent that generates Python Playwright code from execution traces"""
    
    def __init__(self, model_name: str, api_key: str, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        
        # Determine which LLM client to use
        if "claude" in model_name.lower() or "anthropic" in model_name.lower():
            self.client = Anthropic(api_key=api_key)
            self.client_type = "claude"
        elif "gpt" in model_name.lower() or "openai" in model_name.lower():
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
        else:
            # Default to OpenAI
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
    
    async def generate_code(self, execution_trace: List[Dict[str, Any]], task_description: str) -> str:
        """Generate Python Playwright code from execution trace"""
        logger.info(f"📝 Code Generator Agent starting for task: {task_description}")
        
        trace_text = json.dumps(execution_trace, indent=2)
        
        prompt = f"""Task Description: {task_description}

Execution Trace:
{trace_text}

Generate a clean, production-ready Python Playwright script that performs this automation task.

Use intelligent locators:
1. page.get_by_role() - for buttons, links, headings, etc.
2. page.get_by_label() - for form fields with labels
3. page.get_by_placeholder() - for inputs with placeholders
4. page.get_by_test_id() - for elements with test IDs
5. page.locator() - only as last resort for CSS selectors

Include:
- Proper async/await structure
- All necessary imports
- Error handling
- Descriptive variable names
- Comments where helpful

Output ONLY the Python code, starting with imports."""
        
        try:
            if self.client_type == "claude":
                code = await self._generate_with_claude(prompt)
            else:
                code = await self._generate_with_openai(prompt)
            
            code = self._clean_code(code)
            logger.info("✓ Code generation completed")
            return code
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return f"# Error generating code: {str(e)}\n"
    
    async def _generate_with_claude(self, prompt: str) -> str:
        """Generate code using Claude"""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=CODE_GENERATOR_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        )
        
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        
        return ""
    
    async def _generate_with_openai(self, prompt: str) -> str:
        """Generate code using OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": CODE_GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content or ""
    
    def _clean_code(self, code: str) -> str:
        """Clean generated code by removing markdown formatting"""
        code = code.strip()
        
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        
        if code.endswith("```"):
            code = code[:-3]
        
        return code.strip()


class HealerAgent:
    """
    Agent that fixes failed Playwright scripts using intelligent multi-attempt healing
    Enforces up to 3 healing attempts with deterministic patches + LLM assistance
    """
    
    def __init__(self, model_name: str, api_key: str, base_url: str = None, max_healing_attempts: int = 3):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.max_healing_attempts = max_healing_attempts
        self.healing_history: List[Dict[str, Any]] = []
        
        # Determine which LLM client to use
        if "claude" in model_name.lower() or "anthropic" in model_name.lower():
            self.client = Anthropic(api_key=api_key)
            self.client_type = "claude"
        elif "gpt" in model_name.lower() or "openai" in model_name.lower():
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
        else:
            # Default to OpenAI
            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
            self.client_type = "openai"
    
    def _apply_deterministic_patches(self, code: str, error_message: str) -> Tuple[str, List[str]]:
        """
        Apply rule-based fixes for common error patterns
        Returns: (patched_code, list of changes made)
        """
        patches_applied = []
        patched_code = code
        
        # Pattern 1: Timeout errors -> add waits and increase timeouts
        if "timeout" in error_message.lower() or "timed out" in error_message.lower():
            if "wait_for_load_state" not in code:
                patched_code = patched_code.replace(
                    "await page.goto(",
                    "await page.goto("
                ).replace(
                    "await page.goto(url)",
                    "await page.goto(url)\n    await page.wait_for_load_state('networkidle')"
                )
                patches_applied.append("Added wait_for_load_state after navigation")
            
            if "timeout=" not in code:
                patched_code = patched_code.replace(
                    ".click()",
                    ".click(timeout=10000)"
                ).replace(
                    ".fill(",
                    ".fill(timeout=10000, "
                )
                patches_applied.append("Increased timeout parameters")
        
        # Pattern 2: Element not found -> add waits and visibility checks
        if "not found" in error_message.lower() or "no element" in error_message.lower():
            if ".wait_for" not in code:
                patches_applied.append("Need to add explicit waits for elements")
        
        # Pattern 3: Stale element -> add retry logic
        if "stale" in error_message.lower() or "detached" in error_message.lower():
            patches_applied.append("Need to re-fetch element before interaction")
        
        # Pattern 4: Multiple elements -> add .first() ONLY to locator chains
        if "strict mode" in error_message.lower() or "multiple elements" in error_message.lower():
            # Only add .first() to locator chains, not page-level operations
            # Look for patterns like: .locator(...).click() or .get_by_...().click()
            import re
            
            # Pattern: locator(...).click() -> locator(...).first().click()
            patched_code = re.sub(
                r'\.locator\(([^)]+)\)\.click\(\)',
                r'.locator(\1).first().click()',
                patched_code
            )
            
            # Pattern: locator(...).fill( -> locator(...).first().fill(
            patched_code = re.sub(
                r'\.locator\(([^)]+)\)\.fill\(',
                r'.locator(\1).first().fill(',
                patched_code
            )
            
            # Pattern: get_by_*(...).click() -> get_by_*(...).first().click()
            patched_code = re.sub(
                r'\.(get_by_\w+\([^)]*\))\.click\(\)',
                r'.\1.first().click()',
                patched_code
            )
            
            # Pattern: get_by_*(...).fill( -> get_by_*(...).first().fill(
            patched_code = re.sub(
                r'\.(get_by_\w+\([^)]*\))\.fill\(',
                r'.\1.first().fill(',
                patched_code
            )
            
            if patched_code != code:  # Only log if changes were made
                patches_applied.append("Added .first() to locator chains to handle multiple elements")
        
        return patched_code, patches_applied
    
    async def heal_code_with_retries(
        self,
        original_code: str,
        error_message: str,
        execution_trace: Optional[List[Dict[str, Any]]] = None,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """
        Multi-attempt healing with deterministic patches + LLM assistance
        
        Returns:
            Dictionary with healed_code, success, attempts, and healing_log
        """
        log_structured("info", {
            "msg": f"Healing attempt {attempt}/{self.max_healing_attempts}",
            "error_preview": error_message[:200]
        })
        
        # First try deterministic patches
        patched_code, patches = self._apply_deterministic_patches(original_code, error_message)
        
        if patches:
            log_structured("info", {
                "msg": "Applied deterministic patches",
                "patches": patches
            })
            self.healing_history.append({
                "attempt": attempt,
                "type": "deterministic",
                "patches": patches,
                "ts": now_ts()
            })
            
            # If deterministic patches were applied, return them for testing
            if len(patches) > 0:
                return {
                    "healed_code": patched_code,
                    "success": True,
                    "attempt": attempt,
                    "method": "deterministic",
                    "patches_applied": patches,
                    "healing_log": self.healing_history
                }
        
        # If no deterministic patches or they failed, use LLM
        healed_code = await self.heal_code(original_code, error_message, execution_trace)
        
        self.healing_history.append({
            "attempt": attempt,
            "type": "llm_assisted",
            "ts": now_ts()
        })
        
        return {
            "healed_code": healed_code,
            "success": True,
            "attempt": attempt,
            "method": "llm_assisted",
            "healing_log": self.healing_history
        }
    
    async def heal_code(
        self, 
        original_code: str, 
        error_message: str, 
        execution_trace: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Fix failed Playwright code using error analysis and multi-locator strategies
        
        Args:
            original_code: The failed Playwright script
            error_message: The error message from execution
            execution_trace: Optional execution trace with locator information
        
        Returns:
            Fixed Python code with robust multi-locator strategies
        """
        logger.info("🔧 Healer Agent starting LLM-assisted code repair...")
        
        trace_info = ""
        if execution_trace:
            trace_info = f"\n\nExecution Trace (with locator information):\n{json.dumps(execution_trace, indent=2)}"
        
        prompt = f"""The following Playwright script failed with an error:

ORIGINAL CODE:
```python
{original_code}
```

ERROR MESSAGE:
{error_message}
{trace_info}

Analyze the error and fix the script using robust multi-locator strategies.

Common issues and fixes:
1. **Locator not found**: Implement fallback locators
   - Try role, label, text, placeholder, test-id in order
   - Add CSS/XPath as final fallback
   
2. **Timing issues**: Add proper waits
   - Use wait_for_load_state(), wait_for_selector()
   - Add timeout parameters
   
3. **Element not visible/clickable**: Add visibility checks
   - Check element state before interaction
   - Scroll element into view if needed

Use this pattern for robust element location:
```python
# Try multiple locator strategies with fallbacks
locator = None
strategies = [
    ("role", lambda: page.get_by_role("button", name="Submit")),
    ("label", lambda: page.get_by_label("Submit")),
    ("text", lambda: page.get_by_text("Submit")),
    ("css", lambda: page.locator("button.submit-btn")),
]

for strategy_name, strategy_func in strategies:
    try:
        locator = strategy_func()
        await locator.wait_for(state="visible", timeout=3000)
        logger.info(f"Located element using {{strategy_name}} strategy")
        break
    except Exception as e:
        logger.debug(f"{{strategy_name}} strategy failed: {{e}}")
        continue

if locator:
    await locator.click()
else:
    raise Exception("Could not locate element with any strategy")
```

Output ONLY the fixed Python code with proper error handling and multi-locator fallbacks."""
        
        try:
            if self.client_type == "claude":
                code = await self._heal_with_claude(prompt)
            else:
                code = await self._heal_with_openai(prompt)
            
            code = self._clean_code(code)
            logger.info("✓ Code healing completed")
            return code
        except Exception as e:
            logger.error(f"Error healing code: {e}")
            return f"# Error healing code: {str(e)}\n\n{original_code}"
    
    async def _heal_with_claude(self, prompt: str) -> str:
        """Heal code using Claude"""
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=HEALER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        )
        
        for block in response.content:
            if hasattr(block, 'text'):
                return block.text
        
        return ""
    
    async def _heal_with_openai(self, prompt: str) -> str:
        """Heal code using OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": HEALER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content or ""
    
    def _clean_code(self, code: str) -> str:
        """Clean generated code by removing markdown formatting"""
        code = code.strip()
        
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        
        if code.endswith("```"):
            code = code[:-3]
        
        return code.strip()
