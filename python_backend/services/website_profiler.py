import asyncio
import yaml
from typing import Dict, List, Optional, Any
from .browser_automation import BrowserAutomation
from .llm_manager import LLMManager
import json

class WebsiteProfiler:
    def __init__(self, config_path: str = "config.yaml"):
        import os
        if not os.path.exists(config_path):
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.exploration_settings = self.config["exploration_settings"]
        self.browser = BrowserAutomation(config_path)
        self.llm = LLMManager(config_path)
        self.visited_states = set()
        self.interaction_graph = {
            "nodes": [],
            "edges": []
        }
    
    async def profile_website(self, url: str) -> Dict[str, Any]:
        await self.browser.initialize()
        
        try:
            nav_result = await self.browser.navigate(url)
            if not nav_result["success"]:
                return {"error": nav_result["error"]}
            
            dom_structure = await self.browser.extract_dom_structure()
            
            screenshots = []
            initial_screenshot = await self.browser.take_screenshot(full_page=True)
            screenshots.append(initial_screenshot)
            
            interactive_elements = await self.browser.find_interactive_elements()
            
            element_map = await self._analyze_elements_with_ai(interactive_elements, initial_screenshot)
            
            exploration_results = await self._intelligent_exploration(url, interactive_elements)
            
            profile = {
                "url": url,
                "name": nav_result.get("title", "Unknown"),
                "domStructure": dom_structure,
                "interactionGraph": self.interaction_graph,
                "elementMap": element_map,
                "screenshots": screenshots + exploration_results["screenshots"],
                "explorationLog": exploration_results["log"]
            }
            
            return profile
            
        finally:
            await self.browser.close()
    
    async def _analyze_elements_with_ai(self, elements: List[Dict], screenshot: str) -> Dict[str, Any]:
        element_descriptions = "\n".join([
            f"{i}: {el['tag']} - {el.get('text', '')[:50]} (id: {el.get('id', 'none')}, classes: {', '.join(el.get('classes', [])[:3])})"
            for i, el in enumerate(elements[:50])
        ])
        
        prompt = f"""Analyze these interactive elements from a webpage and categorize them by function:

{element_descriptions}

Categorize each element into:
- navigation: links/buttons for page navigation
- form_input: input fields, textareas, selects
- action: buttons that trigger actions (submit, save, etc.)
- media: image links, video players
- social: social media links/buttons
- utility: settings, preferences, filters

Return a JSON object with element indices as keys and categories as values.
Example: {{"0": "navigation", "1": "form_input", "2": "action"}}
"""
        
        try:
            response = await self.llm.complete(
                prompt=prompt,
                task_type="reasoning",
                with_vision=False,
                temperature=0.3
            )
            
            categorization = json.loads(response["content"])
            
            return {
                "elements": elements,
                "categorization": categorization,
                "analysis": response
            }
        except Exception as e:
            return {
                "elements": elements,
                "categorization": {},
                "error": str(e)
            }
    
    async def _intelligent_exploration(self, base_url: str, interactive_elements: List[Dict]) -> Dict[str, Any]:
        exploration_log = []
        screenshots = []
        interactions_count = 0
        max_interactions = self.exploration_settings["max_interactions"]
        safe_actions = set(self.exploration_settings["safe_actions"])
        avoid_patterns = self.exploration_settings["avoid_patterns"]
        
        for element in interactive_elements[:max_interactions]:
            if interactions_count >= max_interactions:
                break
            
            text = element.get("text", "").lower()
            if any(pattern in text for pattern in avoid_patterns):
                exploration_log.append({
                    "action": "skipped",
                    "element": element,
                    "reason": "matches avoid pattern"
                })
                continue
            
            selector = element.get("selector", "")
            if not selector:
                continue
            
            if "hover" in safe_actions:
                hover_result = await self.browser.hover_element(selector)
                if hover_result["success"]:
                    await asyncio.sleep(0.5)
                    
                    new_state = await self.browser.get_page_content()
                    state_hash = hash(new_state)
                    
                    if state_hash not in self.visited_states:
                        self.visited_states.add(state_hash)
                        screenshot = await self.browser.take_screenshot()
                        screenshots.append(screenshot)
                        
                        self.interaction_graph["edges"].append({
                            "from": base_url,
                            "to": f"hover_{element.get('index')}",
                            "action": "hover",
                            "element": element
                        })
                    
                    exploration_log.append({
                        "action": "hover",
                        "element": element,
                        "result": hover_result
                    })
            
            if "click_safe" in safe_actions and element.get("tag") in ["a"] and element.get("href"):
                href = element.get("href", "")
                if href.startswith("http") and not href.startswith(base_url):
                    exploration_log.append({
                        "action": "skipped_external_link",
                        "element": element
                    })
                    continue
            
            interactions_count += 1
            
            if interactions_count % self.exploration_settings.get("screenshot_intervals", 10) == 0:
                screenshot = await self.browser.take_screenshot()
                screenshots.append(screenshot)
        
        if "scroll" in safe_actions:
            for _ in range(3):
                await self.browser.scroll_page("down", 500)
                await asyncio.sleep(0.5)
            
            screenshot = await self.browser.take_screenshot(full_page=True)
            screenshots.append(screenshot)
        
        return {
            "log": exploration_log,
            "screenshots": screenshots,
            "interactions_count": interactions_count
        }
    
    async def analyze_page_visually(self, url: str) -> Dict[str, Any]:
        await self.browser.initialize()
        
        try:
            await self.browser.navigate(url)
            screenshot = await self.browser.take_screenshot(full_page=True)
            
            prompt = """Analyze this webpage screenshot and provide:
1. Main layout structure (header, navigation, content areas, footer)
2. Key UI components and their purposes
3. Color scheme and design style
4. Notable interactive elements
5. Any accessibility concerns

Provide a detailed analysis."""
            
            response = await self.llm.complete(
                prompt=prompt,
                task_type="vision",
                with_vision=True,
                images=[f"data:image/png;base64,{screenshot}"],
                temperature=0.5
            )
            
            return {
                "url": url,
                "visual_analysis": response["content"],
                "screenshot": screenshot,
                "usage": response["usage"]
            }
            
        finally:
            await self.browser.close()
    
    async def learn_element_relationships(self, dom_structure: Dict) -> Dict[str, Any]:
        prompt = f"""Analyze this DOM structure and identify:
1. Parent-child relationships that indicate logical groupings
2. Elements that likely work together (forms, navigation menus, etc.)
3. Conditional UI patterns (modals, dropdowns, tooltips)
4. Dynamic content areas that may change

DOM Structure (summary):
{json.dumps(dom_structure, indent=2)[:2000]}

Return a structured analysis of element relationships."""
        
        response = await self.llm.complete(
            prompt=prompt,
            task_type="complex",
            temperature=0.3
        )
        
        return {
            "relationships": response["content"],
            "usage": response["usage"]
        }
