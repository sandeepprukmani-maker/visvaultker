"""
Intelligent Website Exploration Service
Deep DOM exploration, element discovery, and interaction learning
"""

from typing import Dict, List, Any, Optional
from backend.browser_engine import BrowserEngine
from backend.llm_manager import llm_manager, TaskType
import json
import asyncio
from datetime import datetime

class WebsiteExplorer:
    def __init__(self, browser_engine: BrowserEngine):
        self.browser = browser_engine
        self.max_depth = 5
        self.interaction_timeout = 5000
    
    async def explore_website(self, url: str, profile_id: str) -> Dict[str, Any]:
        """
        Explore a website and build comprehensive profile
        Returns: DOM map, interaction graph, element categories, selectors
        """
        context_id = f"explore_{profile_id}"
        page_id = f"page_{profile_id}"
        
        try:
            # Create browser context and page
            await self.browser.create_context(context_id)
            await self.browser.create_page(context_id, page_id)
            
            # Navigate to website
            await self.browser.navigate(page_id, url)
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Take initial screenshot
            screenshot_path = await self.browser.take_screenshot(
                page_id, 
                f"initial_{profile_id}"
            )
            
            # Extract DOM structure
            dom_map = await self._extract_dom_structure(page_id)
            
            # Discover interactive elements
            interactive_elements = await self._discover_interactive_elements(page_id)
            
            # Build interaction graph
            interaction_graph = await self._build_interaction_graph(
                page_id, 
                interactive_elements
            )
            
            # Categorize elements using AI
            element_categories = await self._categorize_elements(
                dom_map, 
                interactive_elements
            )
            
            # Generate robust selectors
            selectors = await self._generate_selectors(interactive_elements)
            
            result = {
                'dom_map': dom_map,
                'interaction_graph': interaction_graph,
                'element_categories': element_categories,
                'selectors': selectors,
                'screenshot': screenshot_path,
                'element_count': len(interactive_elements),
                'explored_at': datetime.utcnow().isoformat()
            }
            
            return result
            
        finally:
            # Cleanup
            await self.browser.cleanup(page_id=page_id, context_id=context_id)
    
    async def _extract_dom_structure(self, page_id: str) -> Dict[str, Any]:
        """Extract complete DOM structure"""
        script = """
        function extractDOM(element, depth = 0, maxDepth = 5) {
            if (depth > maxDepth) return null;
            
            const node = {
                tag: element.tagName?.toLowerCase() || 'text',
                id: element.id || null,
                classes: element.className ? element.className.split(' ').filter(Boolean) : [],
                attributes: {},
                text: element.textContent?.trim().substring(0, 100) || '',
                visible: element.offsetParent !== null,
                children: []
            };
            
            // Extract key attributes
            if (element.attributes) {
                for (let attr of element.attributes) {
                    if (['href', 'src', 'type', 'name', 'placeholder', 'value'].includes(attr.name)) {
                        node.attributes[attr.name] = attr.value;
                    }
                }
            }
            
            // Process children
            if (element.children && depth < maxDepth) {
                for (let child of element.children) {
                    const childNode = extractDOM(child, depth + 1, maxDepth);
                    if (childNode) {
                        node.children.push(childNode);
                    }
                }
            }
            
            return node;
        }
        
        return extractDOM(document.body);
        """
        
        return await self.browser.execute_script(page_id, script)
    
    async def _discover_interactive_elements(self, page_id: str) -> List[Dict[str, Any]]:
        """Discover all interactive elements on the page"""
        script = """
        function discoverInteractiveElements() {
            const elements = [];
            const interactiveSelectors = [
                'a[href]', 'button', 'input', 'textarea', 'select',
                '[onclick]', '[role="button"]', '[role="link"]',
                '[tabindex]', 'form', '[contenteditable]'
            ];
            
            document.querySelectorAll(interactiveSelectors.join(', ')).forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                const isVisible = rect.width > 0 && rect.height > 0 && 
                                 el.offsetParent !== null &&
                                 window.getComputedStyle(el).visibility !== 'hidden';
                
                if (isVisible) {
                    elements.push({
                        index: index,
                        tag: el.tagName.toLowerCase(),
                        id: el.id || null,
                        classes: el.className ? el.className.split(' ').filter(Boolean) : [],
                        text: el.textContent?.trim().substring(0, 100) || '',
                        type: el.type || null,
                        name: el.name || null,
                        placeholder: el.placeholder || null,
                        href: el.href || null,
                        role: el.getAttribute('role') || null,
                        ariaLabel: el.getAttribute('aria-label') || null,
                        position: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        }
                    });
                }
            });
            
            return elements;
        }
        
        return discoverInteractiveElements();
        """
        
        return await self.browser.execute_script(page_id, script)
    
    async def _build_interaction_graph(
        self, 
        page_id: str, 
        elements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build graph of element relationships and interactions"""
        
        # Group elements by type
        graph = {
            'forms': [],
            'navigation': [],
            'inputs': [],
            'actions': [],
            'relationships': []
        }
        
        for element in elements:
            if element['tag'] == 'form':
                graph['forms'].append(element)
            elif element['tag'] in ['a', 'nav'] or element.get('role') == 'navigation':
                graph['navigation'].append(element)
            elif element['tag'] in ['input', 'textarea', 'select']:
                graph['inputs'].append(element)
            elif element['tag'] == 'button' or element.get('role') == 'button':
                graph['actions'].append(element)
        
        return graph
    
    async def _categorize_elements(
        self, 
        dom_map: Dict[str, Any],
        interactive_elements: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Use AI to categorize elements by semantic function"""
        
        # Prepare element summary for AI
        element_summary = []
        for el in interactive_elements[:50]:  # Limit to first 50
            element_summary.append({
                'tag': el['tag'],
                'text': el['text'][:50],
                'type': el.get('type'),
                'role': el.get('role'),
                'aria_label': el.get('ariaLabel')
            })
        
        prompt = f"""Analyze these webpage elements and categorize them by function.
Elements: {json.dumps(element_summary, indent=2)}

Categorize into: login_elements, search_elements, navigation_elements, 
form_elements, action_buttons, content_elements, social_elements.

Return JSON with categories as keys and arrays of element indices as values."""
        
        try:
            response = await asyncio.to_thread(
                llm_manager.complete,
                prompt,
                task_type=TaskType.FAST
            )
            
            # Parse AI response
            categories = json.loads(response)
            return categories
            
        except Exception as e:
            # Fallback to basic categorization
            return {
                'login_elements': [],
                'search_elements': [],
                'navigation_elements': [],
                'form_elements': [],
                'action_buttons': [],
                'content_elements': [],
                'social_elements': []
            }
    
    async def _generate_selectors(
        self, 
        elements: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, str]]:
        """Generate robust CSS and XPath selectors for elements"""
        
        selectors = {}
        
        for idx, el in enumerate(elements):
            element_selectors = []
            
            # ID selector (most robust)
            if el.get('id'):
                element_selectors.append(f"#{el['id']}")
            
            # Name attribute
            if el.get('name'):
                element_selectors.append(f"{el['tag']}[name='{el['name']}']")
            
            # Placeholder
            if el.get('placeholder'):
                element_selectors.append(f"{el['tag']}[placeholder='{el['placeholder']}']")
            
            # Aria label
            if el.get('ariaLabel'):
                element_selectors.append(f"{el['tag']}[aria-label='{el['ariaLabel']}']")
            
            # Class-based (if not too generic)
            if el.get('classes') and len(el['classes']) > 0:
                class_selector = f"{el['tag']}.{'.'.join(el['classes'][:3])}"
                element_selectors.append(class_selector)
            
            # Text-based
            if el.get('text') and len(el['text']) > 3:
                text_clean = el['text'][:30].replace("'", "\\'")
                element_selectors.append(f"{el['tag']}:has-text('{text_clean}')")
            
            selectors[f"element_{idx}"] = {
                'css': element_selectors,
                'element_info': {
                    'tag': el['tag'],
                    'text': el.get('text', '')[:50]
                }
            }
        
        return selectors

# Global instance
async def get_explorer(browser_engine: BrowserEngine) -> WebsiteExplorer:
    return WebsiteExplorer(browser_engine)
