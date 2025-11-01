from playwright.async_api import async_playwright, Page
from typing import List, Dict, Optional
import os
from datetime import datetime

class AutomationRunner:
    def __init__(self, screenshots_path: str = "./data/screenshots"):
        self.screenshots_path = screenshots_path
        os.makedirs(screenshots_path, exist_ok=True)
    
    async def execute_plan(self, plan: List[Dict], start_url: Optional[str] = None) -> Dict:
        results = {
            "status": "success",
            "steps_completed": 0,
            "steps_failed": 0,
            "logs": [],
            "screenshots": []
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            try:
                for step in plan:
                    step_num = step.get('step', 0)
                    action_type = step.get('action_type', '')
                    selector = step.get('selector', '')
                    value = step.get('value', '')
                    description = step.get('description', '')
                    
                    try:
                        results['logs'].append(f"Step {step_num}: {description}")
                        
                        if action_type == 'navigate':
                            url = value or start_url
                            await page.goto(url, wait_until='networkidle', timeout=30000)
                            results['logs'].append(f"  ✓ Navigated to {url}")
                        
                        elif action_type == 'click':
                            await page.click(selector, timeout=10000)
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            results['logs'].append(f"  ✓ Clicked {selector}")
                        
                        elif action_type == 'input':
                            await page.fill(selector, value, timeout=10000)
                            results['logs'].append(f"  ✓ Entered text into {selector}")
                        
                        elif action_type == 'wait':
                            wait_time = int(value) if value else 1000
                            await page.wait_for_timeout(wait_time)
                            results['logs'].append(f"  ✓ Waited {wait_time}ms")
                        
                        elif action_type == 'extract':
                            text = await page.text_content(selector, timeout=10000)
                            results['logs'].append(f"  ✓ Extracted: {text}")
                        
                        elif action_type == 'scroll':
                            await page.evaluate(f'window.scrollBy(0, {value or 500})')
                            results['logs'].append(f"  ✓ Scrolled")
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = os.path.join(
                            self.screenshots_path, 
                            f"step_{step_num}_{timestamp}.png"
                        )
                        await page.screenshot(path=screenshot_path)
                        results['screenshots'].append(screenshot_path)
                        
                        results['steps_completed'] += 1
                    
                    except Exception as e:
                        results['logs'].append(f"  ✗ Error: {str(e)}")
                        results['steps_failed'] += 1
                        results['status'] = 'partial_success' if results['steps_completed'] > 0 else 'failed'
            
            except Exception as e:
                results['logs'].append(f"Fatal error: {str(e)}")
                results['status'] = 'failed'
            
            finally:
                await browser.close()
        
        return results
