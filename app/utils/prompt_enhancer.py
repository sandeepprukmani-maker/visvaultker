"""
Prompt Enhancer
Intelligently enhances prompts with learned website knowledge and sequential reasoning
"""
import re
import logging
from typing import Optional
from app.utils.website_learning import format_knowledge_for_prompt, extract_domain

logger = logging.getLogger(__name__)


def extract_url_from_instruction(instruction: str) -> Optional[str]:
    """
    Extract URL from instruction text
    
    Args:
        instruction: Natural language instruction
        
    Returns:
        Extracted URL or None
    """
    # Common URL patterns
    patterns = [
        r'(?:go to|navigate to|visit|open)\s+([a-zA-Z0-9.-]+\.com[^\s]*)',
        r'(?:go to|navigate to|visit|open)\s+(https?://[^\s]+)',
        r'(https?://[^\s]+)',
        r'(?:login|log in|sign in)\s+(?:to\s+)?([a-zA-Z0-9.-]+\.com)',
        r'(?:on|at)\s+([a-zA-Z0-9.-]+\.com)',
    ]
    
    instruction_lower = instruction.lower()
    
    for pattern in patterns:
        match = re.search(pattern, instruction_lower)
        if match:
            url = match.group(1)
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return url
    
    return None


def enhance_instruction_with_knowledge(instruction: str) -> tuple[str, Optional[str]]:
    """
    Enhance instruction with learned website knowledge
    
    Args:
        instruction: Original instruction
        
    Returns:
        Tuple of (enhanced_instruction, target_url)
    """
    url = extract_url_from_instruction(instruction)
    
    if not url:
        return instruction, None
    
    # Get learned knowledge
    knowledge_context = format_knowledge_for_prompt(url)
    
    if knowledge_context:
        enhanced = f"{knowledge_context}\n\nYOUR TASK: {instruction}"
        logger.info(f"📚 Enhanced instruction with knowledge for {extract_domain(url)}")
        return enhanced, url
    
    return instruction, url


def create_sequential_reasoning_prompt() -> str:
    """
    Create enhanced prompt section for better sequential reasoning
    
    Returns:
        Prompt text for sequential instruction handling
    """
    return """
🧠 SEQUENTIAL & COMPLEX TASK INTELLIGENCE 🧠

When given multi-step or complex instructions:

1. **DECOMPOSE TASKS**: Break complex instructions into logical sequential steps
   - Example: "Log in to Gmail and download the PDF attachment from the latest email"
     → Step 1: Navigate to Gmail
     → Step 2: Log in with credentials
     → Step 3: Find latest email
     → Step 4: Locate PDF attachment
     → Step 5: Download the PDF

2. **MAINTAIN CONTEXT**: Remember information from previous steps
   - Element locations, page states, extracted data
   - Use this context for subsequent steps

3. **HANDLE DEPENDENCIES**: Recognize when one step depends on another
   - Don't try to click a button before the page loads
   - Don't fill a form before navigating to it
   - Wait for authentication before accessing protected pages

4. **ADAPTIVE EXECUTION**: Adjust strategy based on what you observe
   - If expected element isn't found, try alternative selectors
   - If page structure differs from expectations, adapt approach
   - Use learned knowledge about the website when available

5. **ERROR RECOVERY**: If a step fails, try alternatives
   - Different selectors for the same element
   - Alternative navigation paths
   - Retry with slightly different timing

6. **VERIFICATION**: Confirm each critical step succeeded before proceeding
   - Check page URL changed after navigation
   - Verify form was submitted (look for success message/redirect)
   - Confirm elements appeared/disappeared as expected

WEBSITE-SPECIFIC LEARNING:
- I learn from every successful automation
- I remember common patterns (login flows, search methods, form structures)
- I use this knowledge to be faster and more accurate on repeat visits
- If you see "LEARNED KNOWLEDGE" above, use those patterns to guide your actions

COMPLEX WEBSITE HANDLING:
- Single Page Applications (SPAs): Wait for dynamic content to load
- Multi-step Forms: Complete all required fields before submitting
- Nested Menus: Navigate through menu hierarchy systematically
- Dynamic Dropdowns: Wait for options to load after opening
- CAPTCHAs/2FA: Report when manual intervention is needed
"""


def inject_enhanced_reasoning(base_prompt: str) -> str:
    """
    Inject sequential reasoning into existing prompt
    
    Args:
        base_prompt: Original system prompt
        
    Returns:
        Enhanced prompt with sequential reasoning
    """
    sequential_prompt = create_sequential_reasoning_prompt()
    
    # Insert after the ULTIMATE TASK line but before other instructions
    lines = base_prompt.split('\n')
    
    # Find a good insertion point (after CRITICAL section)
    insertion_index = -1
    for i, line in enumerate(lines):
        if 'AUXILIARY DECISIONS' in line or 'PAGE LOADING' in line:
            insertion_index = i
            break
    
    if insertion_index > 0:
        lines.insert(insertion_index, sequential_prompt)
        return '\n'.join(lines)
    
    # Fallback: append at the end
    return base_prompt + "\n" + sequential_prompt
