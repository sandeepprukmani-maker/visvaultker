"""
Vision-Enhanced Element Finder
Uses browser-use for vision-based element detection as a fallback
when DOM-based semantic search has low confidence.
"""

from typing import Dict, Optional, List
from playwright.async_api import Page
import asyncio
import json
import os

class VisionFinder:
    """
    Hybrid element finder that combines DOM-based search with vision-based fallback.
    
    Strategy:
    1. Try DOM + embeddings first (fast, ~50-200ms)
    2. If confidence < threshold, use browser-use vision (slower, ~2-5s)
    """
    
    def __init__(self, vision_threshold: float = 0.75):
        """
        Args:
            vision_threshold: Confidence threshold below which to use vision fallback
        """
        self.vision_threshold = vision_threshold
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
    async def find_element_with_vision(
        self, 
        page: Page,
        description: str,
        context: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Use browser-use vision to find an element on the page.
        
        Args:
            page: Playwright page object
            description: Natural language description of element to find
            context: Optional context about what we're trying to do
            
        Returns:
            Dict with selector and metadata, or None if not found
        """
        if not self.openai_api_key:
            return None
            
        try:
            # Build the vision task prompt
            task = f"Find the element that matches: {description}"
            if context:
                task = f"{task}. Context: {context}"
            task += ". Return the CSS selector or XPath for this element."
            
            # Use browser-use's vision capabilities
            # Note: We'll create a lightweight wrapper around the current page
            # instead of spawning a new browser
            
            # Extract page info for vision analysis
            page_info = await self._extract_page_info(page)
            
            # Take screenshot for vision analysis
            screenshot_bytes = await page.screenshot(full_page=False)
            
            # Use OpenAI vision to analyze (lightweight approach)
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            # Encode screenshot as base64
            import base64
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            # Ask GPT-4 Vision to identify the element
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""Analyze this webpage screenshot and find the element matching: "{description}"

Available elements on the page:
{json.dumps(page_info['elements'][:20], indent=2)}

Task: {task}

Return a JSON response with:
{{
  "found": true/false,
  "selector": "CSS selector or XPath",
  "confidence": 0.0-1.0,
  "reasoning": "Why this element matches",
  "element_info": {{"tag": "...", "text": "...", "attributes": {{}}}}
}}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', result_text or '', re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                if result.get('found') and result.get('confidence', 0) > 0.6:
                    return {
                        "selector": result['selector'],
                        "confidence": result['confidence'],
                        "method": "vision",
                        "reasoning": result.get('reasoning', ''),
                        "element": result.get('element_info', {}),
                        "healing_applied": True,
                        "vision_enhanced": True
                    }
            
            return None
            
        except Exception as e:
            print(f"Vision finder error: {e}")
            return None
    
    async def _extract_page_info(self, page: Page) -> Dict:
        """Extract current page DOM info for vision analysis context."""
        try:
            elements = await page.evaluate('''() => {
                function extractElements() {
                    const elements = [];
                    const allElements = document.querySelectorAll('*');
                    
                    for (let el of allElements) {
                        // Only include visible, interactive elements
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;
                        
                        const isInteractive = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName) ||
                                            el.hasAttribute('onclick') ||
                                            el.hasAttribute('role');
                        
                        if (!isInteractive && el.children.length > 0) continue;
                        
                        const computedStyle = window.getComputedStyle(el);
                        if (computedStyle.display === 'none' || computedStyle.visibility === 'hidden') continue;
                        
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            text: el.textContent?.trim().substring(0, 50) || '',
                            id: el.id || '',
                            classes: Array.from(el.classList).join(' '),
                            role: el.getAttribute('role') || '',
                            ariaLabel: el.getAttribute('aria-label') || '',
                            placeholder: el.getAttribute('placeholder') || '',
                            type: el.getAttribute('type') || '',
                            href: el.getAttribute('href') || '',
                            position: {
                                x: Math.round(rect.left),
                                y: Math.round(rect.top),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            }
                        });
                        
                        if (elements.length >= 50) break;
                    }
                    
                    return elements;
                }
                return extractElements();
            }''')
            
            return {
                "elements": elements,
                "url": page.url,
                "title": await page.title()
            }
        except Exception as e:
            print(f"Error extracting page info: {e}")
            return {"elements": [], "url": "", "title": ""}
    
    def should_use_vision(self, confidence: float) -> bool:
        """Determine if vision fallback should be used based on confidence."""
        return confidence < self.vision_threshold
