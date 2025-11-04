import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from .browser_automation import BrowserAutomation
from .llm_manager import LLMManager
import json

class TaskManager:
    def __init__(self):
        self.llm = LLMManager()
        self.browser = BrowserAutomation()
    
    async def teach_task(
        self,
        name: str,
        description: str,
        website_url: str,
        demonstration: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        steps = []
        
        for action in demonstration:
            step = {
                "action_type": action.get("type"),
                "selector": action.get("selector"),
                "value": action.get("value"),
                "description": action.get("description"),
                "wait_condition": action.get("wait_condition")
            }
            steps.append(step)
        
        generalized_steps = await self._generalize_steps_with_ai(steps, website_url)
        
        parameters = await self._extract_parameters(generalized_steps)
        
        task = {
            "name": name,
            "description": description,
            "websiteUrl": website_url,
            "steps": generalized_steps,
            "parameters": parameters,
            "category": await self._categorize_task(name, description),
            "tags": await self._generate_tags(name, description)
        }
        
        return task
    
    async def _generalize_steps_with_ai(self, steps: List[Dict], url: str) -> List[Dict]:
        steps_description = json.dumps(steps, indent=2)
        
        prompt = f"""Analyze these automation steps and make them reusable:

Steps: {steps_description}
Website: {url}

Transform these specific steps into generalized, parametric steps that can work with different inputs.
Identify which values should be parameters vs hardcoded.

Return JSON array of generalized steps with:
- action_type: type of action
- selector: CSS selector (generalized if possible)
- value: value or parameter placeholder like {{username}}
- description: what this step does
- wait_condition: what to wait for after this action
- fallback_selectors: alternative selectors if primary fails

Example output:
[
  {{
    "action_type": "fill",
    "selector": "input[name='username']",
    "value": "{{username}}",
    "description": "Enter username",
    "wait_condition": "element_visible",
    "fallback_selectors": ["#username", ".username-input"]
  }}
]
"""
        
        response = await self.llm.complete(
            prompt=prompt,
            task_type="complex",
            temperature=0.3
        )
        
        try:
            generalized = json.loads(response["content"])
            return generalized
        except:
            return steps
    
    async def _extract_parameters(self, steps: List[Dict]) -> List[Dict]:
        params = []
        seen_params = set()
        
        for step in steps:
            value = step.get("value", "")
            if isinstance(value, str) and "{{" in value and "}}" in value:
                import re
                matches = re.findall(r'\{\{(\w+)\}\}', value)
                for param_name in matches:
                    if param_name not in seen_params:
                        params.append({
                            "name": param_name,
                            "type": "string",
                            "required": True,
                            "description": f"Value for {param_name}"
                        })
                        seen_params.add(param_name)
        
        return params
    
    async def _categorize_task(self, name: str, description: str) -> str:
        prompt = f"""Categorize this automation task into ONE category:

Task: {name}
Description: {description}

Categories:
- data_extraction: scraping, extracting information
- social_media: posting, liking, following on social platforms
- form_submission: filling forms, submitting data
- navigation: browsing, clicking through pages
- monitoring: checking for changes, alerts
- communication: sending messages, emails
- e-commerce: shopping, purchasing
- other: doesn't fit other categories

Return only the category name."""
        
        response = await self.llm.complete(
            prompt=prompt,
            task_type="speed",
            temperature=0.1
        )
        
        return response["content"].strip().lower()
    
    async def _generate_tags(self, name: str, description: str) -> List[str]:
        prompt = f"""Generate 3-5 relevant tags for this automation task:

Task: {name}
Description: {description}

Return comma-separated tags. Tags should be lowercase, single words or short phrases.
Example: linkedin, connection, networking, automation
"""
        
        response = await self.llm.complete(
            prompt=prompt,
            task_type="speed",
            temperature=0.3
        )
        
        tags = [tag.strip().lower() for tag in response["content"].split(",")]
        return tags[:5]
    
    async def execute_task(
        self,
        task: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        await self.browser.initialize()
        
        execution_log = []
        screenshots = []
        
        try:
            nav_result = await self.browser.navigate(task["websiteUrl"])
            if not nav_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to navigate to website",
                    "details": nav_result
                }
            
            execution_log.append({
                "step": "navigation",
                "result": nav_result
            })
            
            for i, step in enumerate(task["steps"]):
                step_result = await self._execute_step(step, parameters or {})
                
                execution_log.append({
                    "step_index": i,
                    "step": step,
                    "result": step_result
                })
                
                if not step_result.get("success", False):
                    retries = 3
                    for retry in range(retries):
                        await asyncio.sleep(2)
                        step_result = await self._execute_step_with_fallback(step, parameters or {})
                        if step_result.get("success", False):
                            break
                    
                    if not step_result.get("success", False):
                        screenshot = await self.browser.take_screenshot()
                        screenshots.append(screenshot)
                        
                        return {
                            "success": False,
                            "error": f"Failed at step {i}",
                            "execution_log": execution_log,
                            "screenshots": screenshots
                        }
                
                if (i + 1) % 5 == 0:
                    screenshot = await self.browser.take_screenshot()
                    screenshots.append(screenshot)
                
                await asyncio.sleep(0.5)
            
            final_screenshot = await self.browser.take_screenshot()
            screenshots.append(final_screenshot)
            
            return {
                "success": True,
                "execution_log": execution_log,
                "screenshots": screenshots
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_log": execution_log,
                "screenshots": screenshots
            }
        finally:
            await self.browser.close()
    
    async def _execute_step(self, step: Dict, parameters: Dict) -> Dict[str, Any]:
        action_type = step.get("action_type")
        selector = step.get("selector")
        value = step.get("value", "")
        
        if isinstance(value, str):
            for param_name, param_value in parameters.items():
                value = value.replace(f"{{{{{param_name}}}}}", str(param_value))
        
        if action_type == "click":
            return await self.browser.click_element(selector)
        elif action_type == "fill":
            return await self.browser.fill_input(selector, value)
        elif action_type == "hover":
            return await self.browser.hover_element(selector)
        elif action_type == "scroll":
            direction = step.get("direction", "down")
            amount = step.get("amount", 500)
            return await self.browser.scroll_page(direction, amount)
        elif action_type == "wait":
            timeout = step.get("timeout", 5000)
            return {"success": await self.browser.wait_for_selector(selector, timeout)}
        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}
    
    async def _execute_step_with_fallback(self, step: Dict, parameters: Dict) -> Dict[str, Any]:
        result = await self._execute_step(step, parameters)
        
        if not result.get("success") and step.get("fallback_selectors"):
            for fallback_selector in step["fallback_selectors"]:
                fallback_step = step.copy()
                fallback_step["selector"] = fallback_selector
                result = await self._execute_step(fallback_step, parameters)
                if result.get("success"):
                    return result
        
        return result
