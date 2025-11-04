"""
AI-Powered Task Execution Engine
Executes automation tasks using natural language interpretation
"""

from typing import Dict, List, Any, Optional
from backend.browser_engine import BrowserEngine
from backend.llm_manager import llm_manager, TaskType
from backend.credential_manager import credential_manager
from datetime import datetime
import json
import asyncio
import uuid

class TaskExecutor:
    def __init__(self, browser_engine: BrowserEngine):
        self.browser = browser_engine
        self.execution_logs: Dict[str, List[str]] = {}
        self.screenshots: Dict[str, List[str]] = {}
    
    async def execute_task(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a single automation task
        
        Args:
            task_id: Unique task identifier
            task_data: Task configuration
            profile_data: Website profile data
            parameters: Runtime parameters for parametric tasks
            credentials: Login credentials if needed
        
        Returns:
            Execution result with status, logs, screenshots, extracted data
        """
        execution_id = str(uuid.uuid4())
        self.execution_logs[execution_id] = []
        self.screenshots[execution_id] = []
        
        context_id = f"task_{execution_id}"
        page_id = f"page_{execution_id}"
        
        try:
            self._log(execution_id, f"Starting task: {task_data.get('title')}")
            
            # Initialize browser
            await self.browser.initialize()
            
            # Create context with session if available
            session_file = f"profile_{profile_data['id']}_session.json"
            await self.browser.create_context(
                context_id,
                session_file=session_file
            )
            await self.browser.create_page(context_id, page_id)
            
            # Navigate to website
            url = profile_data['url']
            self._log(execution_id, f"Navigating to {url}")
            await self.browser.navigate(page_id, url)
            
            # Take initial screenshot
            screenshot = await self.browser.take_screenshot(
                page_id,
                f"task_{execution_id}_start"
            )
            self.screenshots[execution_id].append(screenshot)
            
            # Handle login if credentials provided
            if credentials:
                self._log(execution_id, "Performing login...")
                await self._handle_login(page_id, credentials, execution_id)
            
            # Get automation script
            automation_script = task_data.get('automation_script')
            
            if not automation_script:
                # Generate automation script using AI
                self._log(execution_id, "Generating automation script with AI...")
                automation_script = await self._generate_automation_script(
                    task_data,
                    profile_data,
                    page_id
                )
            
            # Execute automation steps
            self._log(execution_id, "Executing automation steps...")
            extracted_data = await self._execute_automation_steps(
                page_id,
                automation_script,
                parameters or {},
                execution_id
            )
            
            # Take final screenshot
            final_screenshot = await self.browser.take_screenshot(
                page_id,
                f"task_{execution_id}_end",
                full_page=True
            )
            self.screenshots[execution_id].append(final_screenshot)
            
            # Save session
            await self.browser.save_session(context_id, f"profile_{profile_data['id']}_session")
            
            self._log(execution_id, "Task completed successfully")
            
            return {
                'execution_id': execution_id,
                'status': 'success',
                'logs': self.execution_logs[execution_id],
                'screenshots': self.screenshots[execution_id],
                'extracted_data': extracted_data,
                'completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self._log(execution_id, f"Error: {str(e)}")
            
            # Take error screenshot
            try:
                error_screenshot = await self.browser.take_screenshot(
                    page_id,
                    f"task_{execution_id}_error"
                )
                self.screenshots[execution_id].append(error_screenshot)
            except:
                pass
            
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'logs': self.execution_logs[execution_id],
                'screenshots': self.screenshots[execution_id],
                'completed_at': datetime.utcnow().isoformat()
            }
            
        finally:
            # Cleanup
            await self.browser.cleanup(page_id=page_id, context_id=context_id)
    
    async def _handle_login(
        self,
        page_id: str,
        credentials: Dict[str, Any],
        execution_id: str
    ) -> None:
        """Handle website login"""
        login_url = credentials.get('login_url')
        selectors = credentials.get('selectors', {})
        
        # Navigate to login page if specified
        if login_url:
            await self.browser.navigate(page_id, login_url)
            await asyncio.sleep(2)
        
        # Fill username
        if selectors.get('username'):
            self._log(execution_id, "Filling username...")
            await self.browser.fill(
                page_id,
                selectors['username'],
                credentials['username']
            )
        
        # Fill password
        if selectors.get('password'):
            self._log(execution_id, "Filling password...")
            await self.browser.fill(
                page_id,
                selectors['password'],
                credentials['password']
            )
        
        # Click submit
        if selectors.get('submit'):
            self._log(execution_id, "Submitting login form...")
            await self.browser.click(page_id, selectors['submit'])
            await asyncio.sleep(3)
        
        self._log(execution_id, "Login completed")
    
    async def _generate_automation_script(
        self,
        task_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        page_id: str
    ) -> List[Dict[str, Any]]:
        """Use AI to generate automation script from task description"""
        
        # Get current page state
        page_content = await self.browser.get_page_content(page_id)
        
        # Extract selectors from profile
        selectors = profile_data.get('selectors', {})
        
        prompt = f"""Generate an automation script for this task:

Task Title: {task_data.get('title')}
Task Description: {task_data.get('description')}

Available selectors from learned profile:
{json.dumps(list(selectors.keys())[:20], indent=2)}

Generate a JSON array of automation steps. Each step should have:
- action: click, fill, wait, extract, navigate
- selector: CSS selector to target
- value: value for fill actions
- description: what this step does

Example:
[
  {{"action": "fill", "selector": "input[name='search']", "value": "{{search_query}}", "description": "Enter search query"}},
  {{"action": "click", "selector": "button[type='submit']", "description": "Submit search"}},
  {{"action": "wait", "selector": ".results", "description": "Wait for results"}},
  {{"action": "extract", "selector": ".result-item", "description": "Extract result items"}}
]

Return only the JSON array."""
        
        try:
            response = await asyncio.to_thread(
                llm_manager.complete,
                prompt,
                task_type=TaskType.REASONING
            )
            
            # Parse AI response
            script = json.loads(response)
            return script
            
        except Exception as e:
            # Fallback to basic script
            return [
                {
                    "action": "wait",
                    "selector": "body",
                    "description": "Wait for page load"
                }
            ]
    
    async def _execute_automation_steps(
        self,
        page_id: str,
        automation_script: List[Dict[str, Any]],
        parameters: Dict[str, Any],
        execution_id: str
    ) -> Dict[str, Any]:
        """Execute automation steps"""
        
        extracted_data = {}
        
        for idx, step in enumerate(automation_script):
            action = step.get('action')
            selector = step.get('selector')
            value = step.get('value')
            description = step.get('description', f'Step {idx + 1}')
            
            self._log(execution_id, f"Step {idx + 1}: {description}")
            
            # Replace parameters in value
            if value and isinstance(value, str):
                for param_name, param_value in parameters.items():
                    value = value.replace(f"{{{{{param_name}}}}}", str(param_value))
            
            try:
                if action == 'navigate':
                    await self.browser.navigate(page_id, value)
                
                elif action == 'click':
                    await self.browser.click(page_id, selector)
                    await asyncio.sleep(1)
                
                elif action == 'fill':
                    await self.browser.fill(page_id, selector, value)
                
                elif action == 'wait':
                    await self.browser.wait_for_selector(page_id, selector)
                
                elif action == 'extract':
                    # Extract data from elements
                    extract_script = f"""
                    Array.from(document.querySelectorAll('{selector}')).map(el => ({{
                        text: el.textContent?.trim(),
                        href: el.href || null,
                        src: el.src || null
                    }}))
                    """
                    data = await self.browser.execute_script(page_id, extract_script)
                    extracted_data[f'step_{idx}'] = data
                
                elif action == 'screenshot':
                    screenshot = await self.browser.take_screenshot(
                        page_id,
                        f"step_{idx}_{execution_id}"
                    )
                    self.screenshots[execution_id].append(screenshot)
                
            except Exception as e:
                self._log(execution_id, f"Step {idx + 1} failed: {str(e)}")
                # Continue with next step (resilient execution)
        
        return extracted_data
    
    def _log(self, execution_id: str, message: str) -> None:
        """Add log entry"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.execution_logs[execution_id].append(log_entry)
        print(log_entry)


async def get_task_executor(browser_engine: BrowserEngine) -> TaskExecutor:
    return TaskExecutor(browser_engine)
