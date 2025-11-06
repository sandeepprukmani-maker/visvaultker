# Intelligent, Goal-Driven Agent

## Overview

This tool features an **intelligent, goal-driven ExecutorAgent** that doesn't just follow rigid steps - it thinks, adapts, and makes autonomous decisions to achieve your goals.

## Key Intelligence Features

### 🎯 Goal-Driven Behavior
The agent focuses on **achieving the end goal**, not just executing steps:
- Understands the ultimate objective
- Plans multiple approaches before acting
- Adapts strategy based on observations
- Tries alternative paths if one fails

### 🧠 Autonomous Decision Making
The agent makes smart decisions without needing hand-holding:
- **Plans** before acting - thinks through needed steps
- **Observes** after each action - understands what happened
- **Adapts** when things don't go as expected
- **Retries** with different approaches if something fails
- **Explores** alternative paths when needed

### 💡 Intelligent Problem Solving

The agent is authorized to:
- Take screenshots to understand page state
- Execute JavaScript to inspect elements
- Navigate through multiple pages
- Fill forms with reasonable test data
- Handle popups, modals, cookie banners
- Scroll and expand dynamic content
- Use search functionality
- Try similar buttons/links if exact ones aren't found

### 🔄 Adaptive Strategies

**Example intelligent behaviors:**

1. **Button Not Found?**
   - Tries similar text variations
   - Looks for alternative buttons with similar purpose
   - Checks if it needs to scroll or expand sections

2. **Form Field Missing?**
   - Looks for alternative input methods
   - Checks for multi-step forms
   - Tries alternative field names

3. **Navigation Failed?**
   - Uses site search to find content
   - Explores menu structures
   - Tries alternative navigation paths

4. **Element Hidden?**
   - Scrolls to reveal it
   - Expands collapsed sections
   - Clicks through tabs or accordions

## Example Scenarios

### Scenario 1: E-commerce Shopping
**User Goal:** "Add a laptop to cart on Amazon"

**Rigid Bot Would:**
1. Go to amazon.com
2. Find search box with exact selector
3. Type "laptop"
4. Click exact "Search" button
5. Click exact first result
6. Find exact "Add to Cart" button

**Intelligent Agent Does:**
1. Plans: "I'll search for laptop, filter results, and add to cart"
2. Navigates to Amazon
3. If cookie banner appears → dismisses it autonomously
4. Finds search (tries multiple selectors: by_label, by_placeholder, by_role)
5. Types "laptop" and submits
6. If results are poor quality → refines search
7. Looks for "Add to Cart" button (tries multiple text variations)
8. If cart modal appears → handles it
9. Verifies success by checking cart

### Scenario 2: Form Submission
**User Goal:** "Fill out contact form on example.com"

**Rigid Bot Would:**
- Fail if exact field names don't match
- Get stuck on unexpected required fields
- Break if captcha appears

**Intelligent Agent Does:**
1. Plans: "Navigate to contact page, fill fields, submit"
2. Goes to example.com
3. Looks for "Contact" link (tries multiple variations: "Contact Us", "Get in Touch", etc.)
4. Identifies all form fields (name, email, message, etc.)
5. If unexpected field appears → makes reasonable choice
6. If captcha appears → notifies in trace (can't solve but handles gracefully)
7. Submits form with semantic locator
8. Verifies submission success

### Scenario 3: Research Task
**User Goal:** "Find top 5 articles on Hacker News"

**Intelligent Agent Does:**
1. Plans: "Navigate to HN, identify article structure, extract top 5"
2. Goes to news.ycombinator.com
3. Takes screenshot to understand page layout
4. Uses JavaScript to inspect article structure
5. Identifies article titles via semantic selectors
6. Adapts to actual HTML structure observed
7. Extracts top 5 articles
8. Formats output appropriately

## How It Works

### Planning Phase
```
User: "Book a flight from NYC to LA"

Agent thinks:
- Approach 1: Use airline website directly
- Approach 2: Use flight search aggregator
- Approach 3: Search for flights then navigate

Agent chooses: Approach 2 (most reliable)
```

### Execution Phase
```
Agent executes:
1. Navigate to flight search site
2. [OBSERVES: Cookie banner appeared]
   → Autonomously dismisses it
3. Fill origin field
   [OBSERVES: Autocomplete dropdown appeared]
   → Selects NYC from dropdown
4. Fill destination
   [OBSERVES: Different UI than expected]
   → Adapts approach, finds alternative selector
5. Click search
   [OBSERVES: Loading spinner]
   → Waits for results
6. Select flight
   [OBSERVES: Price changed]
   → Notes in trace, continues
```

### Adaptation Examples
```
IF button text is "Submit" but not found:
  TRY "Send", "Continue", "Next", "Proceed"
  
IF form field "Email" not found:
  TRY "Email Address", "Your Email", "E-mail"
  
IF navigation link not visible:
  TRY scrolling, expanding menu, using search
  
IF element not clickable:
  TRY waiting, scrolling into view, removing overlays
```

## Configuration

The agent is configured with:
- **Max iterations:** 30 (allows complex multi-step workflows)
- **Semantic locators:** Required for reliability
- **Adaptive retry:** Built into decision making
- **Screenshot capability:** For debugging
- **JavaScript execution:** For dynamic inspection

## Limitations & Safeguards

**What the agent CAN do:**
✅ Make autonomous navigation decisions
✅ Try alternative selectors and approaches
✅ Handle popups and cookie banners
✅ Fill forms with test data
✅ Navigate multi-page workflows
✅ Use search functionality
✅ Adapt to unexpected UI changes

**What the agent CANNOT/WILL NOT do:**
❌ Solve CAPTCHAs (notes in trace if encountered)
❌ Make financial transactions without clear instruction
❌ Access password-protected areas without credentials
❌ Perform actions that violate website terms
❌ Make destructive actions (delete, modify user data)

## Usage Examples

### Simple Goal
```bash
python main.py "Find the most popular GitHub repository for Python"
```

Agent will:
- Navigate to GitHub
- Use search intelligently
- Sort/filter results autonomously
- Identify and click top result

### Complex Goal
```bash
python main.py "Research latest AI news: go to HN, find top 3 AI-related stories, and screenshot them"
```

Agent will:
- Plan approach to HN
- Navigate and understand page structure
- Intelligently identify AI-related content
- Select top 3 based on ranking
- Take meaningful screenshots
- Handle any popups/cookies autonomously

### Adaptive Goal
```bash
python main.py "Sign up for newsletter on example.com"
```

Agent will:
- Find signup form (tries multiple locations: footer, modal, dedicated page)
- Fill required fields (adapts to whatever fields exist)
- Handle email verification if needed
- Confirm subscription
- Report success or failure

## Benefits

1. **Higher Success Rate** - Adapts when exact selectors don't match
2. **More Robust** - Handles unexpected UI elements
3. **Less Maintenance** - Generated scripts include adaptive logic
4. **Smarter Traces** - Execution traces show reasoning
5. **Better Code** - Generated Python includes intelligent error handling

## Result Quality

**Traditional approach:**
```python
# Brittle - breaks if text changes
await page.click("#submit-btn")
```

**Intelligent agent generates:**
```python
# Semantic, with fallbacks
try:
    await page.get_by_role("button", name="Submit").click()
except:
    # Agent tried alternatives during execution
    await page.get_by_text("Send").click()
```

The agent's intelligence and adaptability are captured in both the execution trace and the final generated code, making your automation more reliable and maintainable!
