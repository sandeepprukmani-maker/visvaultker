"""
🎭 Generator Agent - Transforms Markdown plans into executable automation

Inspired by Playwright's generator, this agent:
1. Parses Markdown test specifications
2. Generates executable automation plans with verified selectors
3. Validates elements exist during generation
4. Produces structured JSON automation scripts
"""

import asyncio
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class GeneratorAgent:
    """Converts Markdown specs into executable automation plans"""
    
    def __init__(self, context_retriever, openai_client, crawler):
        self.context_retriever = context_retriever
        self.openai_client = openai_client
        self.crawler = crawler
        self.tests_dir = Path("data/tests")
        self.tests_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_from_spec(
        self,
        spec_content: str,
        spec_filename: str,
        seed_url: Optional[str] = None,
        verify_selectors: bool = True
    ) -> Dict[str, Any]:
        """
        Generate executable automation from Markdown spec
        
        Args:
            spec_content: Markdown specification content
            spec_filename: Original spec filename for reference
            seed_url: Starting URL (extracted from spec if not provided)
            verify_selectors: Whether to verify selectors exist during generation
        
        Returns:
            Dictionary with generated test metadata and file path
        """
        # Step 1: Parse the spec to extract scenarios and steps
        parsed_scenarios = self._parse_spec(spec_content)
        
        # Step 2: Extract or use provided seed URL
        if not seed_url:
            seed_url = self._extract_url_from_spec(spec_content)
        
        # Ensure we have a URL
        if not seed_url:
            raise ValueError("No seed URL provided or found in spec")
        
        # Step 3: Get current page context if selector verification is enabled
        page_context = None
        if verify_selectors:
            page_context = await self._get_page_context(seed_url)
        
        # Step 4: Generate executable plans for each scenario
        generated_tests = []
        for scenario in parsed_scenarios:
            test = await self._generate_test(
                scenario, 
                seed_url, 
                page_context,
                verify_selectors
            )
            generated_tests.append(test)
        
        # Step 5: Save the generated tests
        test_path = self._save_tests(
            spec_filename,
            seed_url,
            generated_tests
        )
        
        return {
            "test_path": str(test_path),
            "spec_source": spec_filename,
            "scenarios_generated": len(generated_tests),
            "seed_url": seed_url,
            "selector_verification": verify_selectors,
            "created_at": datetime.now().isoformat(),
            "tests": generated_tests
        }
    
    def _parse_spec(self, spec_content: str) -> List[Dict]:
        """Parse Markdown spec to extract structured scenarios"""
        scenarios = []
        
        # Split by scenario headers (### X. Scenario Name)
        scenario_pattern = r'###\s+\d+\.\s+(.+?)\n(.*?)(?=###|\Z)'
        matches = re.finditer(scenario_pattern, spec_content, re.DOTALL)
        
        for match in matches:
            scenario_name = match.group(1).strip()
            scenario_content = match.group(2).strip()
            
            # Extract steps (look for numbered lists or "Steps:" section)
            steps = self._extract_steps(scenario_content)
            
            # Extract expected results
            expected_results = self._extract_expected_results(scenario_content)
            
            scenarios.append({
                "name": scenario_name,
                "content": scenario_content,
                "steps": steps,
                "expected_results": expected_results
            })
        
        return scenarios
    
    def _extract_steps(self, content: str) -> List[str]:
        """Extract step-by-step actions from scenario content"""
        steps = []
        
        # Look for numbered lists (1., 2., 3., etc.)
        step_pattern = r'^\d+\.\s+(.+?)$'
        
        for line in content.split('\n'):
            match = re.match(step_pattern, line.strip())
            if match:
                steps.append(match.group(1).strip())
        
        return steps
    
    def _extract_expected_results(self, content: str) -> List[str]:
        """Extract expected results from scenario content"""
        results = []
        
        # Look for "Expected Results:" section or bullet points after steps
        in_results = False
        
        for line in content.split('\n'):
            if 'expected result' in line.lower():
                in_results = True
                continue
            
            if in_results and line.strip().startswith('-'):
                results.append(line.strip()[1:].strip())
        
        return results
    
    def _extract_url_from_spec(self, spec_content: str) -> Optional[str]:
        """Extract URL from spec content"""
        # Look for URL in metadata or content
        url_pattern = r'https?://[^\s)]+'
        match = re.search(url_pattern, spec_content)
        
        return match.group(0) if match else None
    
    async def _get_page_context(self, url: str) -> Dict:
        """Get current page context for selector verification"""
        try:
            crawl_result = await self.crawler.crawl(url, depth=1)
            
            if crawl_result.get("pages"):
                page = crawl_result["pages"][0]
                return {
                    "url": url,
                    "dom_elements": page.get("dom_elements", []),
                    "screenshot": page.get("screenshot")
                }
        except Exception as e:
            print(f"Warning: Could not get page context: {e}")
        
        return {"url": url, "dom_elements": []}
    
    async def _generate_test(
        self,
        scenario: Dict,
        seed_url: str,
        page_context: Optional[Dict],
        verify_selectors: bool
    ) -> Dict:
        """Generate executable test from parsed scenario"""
        
        # Build prompt for GPT to generate automation steps
        prompt = self._build_generation_prompt(scenario, seed_url, page_context)
        
        # Call OpenAI
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an automation code generator. Convert test scenarios into 
                        executable automation steps using this JSON format:
                        
                        {
                          "actions": [
                            {"action": "navigate", "url": "https://example.com"},
                            {"action": "click", "selector": "button.login", "description": "Click login button"},
                            {"action": "fill", "selector": "input[name='email']", "value": "test@example.com"},
                            {"action": "expect", "selector": ".success-message", "condition": "visible"}
                          ]
                        }
                        
                        Use semantic, robust selectors. Verify each selector if page context is provided.
                        Be precise and include assertions."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
        )
        
        # Parse the generated automation plan
        automation_plan = json.loads(response.choices[0].message.content)
        
        # Verify selectors if enabled
        if verify_selectors and page_context:
            automation_plan = await self._verify_and_fix_selectors(
                automation_plan,
                page_context
            )
        
        return {
            "scenario_name": scenario["name"],
            "automation_plan": automation_plan,
            "steps_count": len(automation_plan.get("actions", [])),
            "verified": verify_selectors
        }
    
    def _build_generation_prompt(
        self,
        scenario: Dict,
        seed_url: str,
        page_context: Optional[Dict]
    ) -> str:
        """Build prompt for automation generation"""
        
        prompt = f"""Generate executable automation for this scenario:

SCENARIO: {scenario['name']}

STEPS:
"""
        
        for idx, step in enumerate(scenario.get("steps", []), 1):
            prompt += f"{idx}. {step}\n"
        
        if scenario.get("expected_results"):
            prompt += "\nEXPECTED RESULTS:\n"
            for result in scenario["expected_results"]:
                prompt += f"- {result}\n"
        
        prompt += f"\nSTARTING URL: {seed_url}\n"
        
        if page_context and page_context.get("dom_elements"):
            prompt += "\nAVAILABLE PAGE ELEMENTS:\n"
            for elem in page_context["dom_elements"][:20]:
                prompt += f"- {elem.get('tag', 'element')}: {elem.get('text', '')[:50]} [{elem.get('selector', 'N/A')}]\n"
        
        prompt += """
Generate a JSON automation plan with actions array. Include:
- navigate, click, fill, select, press actions for user steps
- expect, waitFor actions for validations
- Use the most robust selectors from available elements when possible
"""
        
        return prompt
    
    async def _verify_and_fix_selectors(
        self,
        automation_plan: Dict,
        page_context: Dict
    ) -> Dict:
        """Verify selectors exist and suggest fixes if needed"""
        
        available_selectors = {
            elem.get("selector"): elem 
            for elem in page_context.get("dom_elements", [])
            if elem.get("selector")
        }
        
        for action in automation_plan.get("actions", []):
            if "selector" in action:
                selector = action["selector"]
                
                # Check if exact selector exists
                if selector not in available_selectors:
                    # Try to find a similar selector
                    fixed_selector = self._find_similar_selector(
                        selector,
                        available_selectors,
                        action.get("description", "")
                    )
                    
                    if fixed_selector:
                        action["selector"] = fixed_selector
                        action["selector_verified"] = True
                    else:
                        action["selector_verified"] = False
                        action["selector_warning"] = "Selector not found on page"
                else:
                    action["selector_verified"] = True
        
        return automation_plan
    
    def _find_similar_selector(
        self,
        target_selector: str,
        available_selectors: Dict,
        description: str
    ) -> Optional[str]:
        """Find a similar selector from available options"""
        
        # Simple heuristic: look for selectors containing similar text or attributes
        target_lower = target_selector.lower()
        
        for selector, elem in available_selectors.items():
            selector_lower = selector.lower()
            
            # Check if selectors share common parts
            if any(part in selector_lower for part in target_lower.split() if len(part) > 3):
                return selector
            
            # Check if element text matches description
            if description.lower() in elem.get("text", "").lower():
                return selector
        
        return None
    
    def _save_tests(
        self,
        spec_filename: str,
        seed_url: str,
        tests: List[Dict]
    ) -> Path:
        """Save generated tests to file"""
        
        # Create filename based on spec
        spec_base = Path(spec_filename).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{spec_base}_generated_{timestamp}.json"
        
        test_path = self.tests_dir / filename
        
        test_suite = {
            "spec_source": spec_filename,
            "seed_url": seed_url,
            "generated_at": datetime.now().isoformat(),
            "tests": tests
        }
        
        with open(test_path, "w") as f:
            json.dump(test_suite, f, indent=2)
        
        return test_path
    
    def list_tests(self) -> List[Dict]:
        """List all generated tests"""
        tests = []
        
        for test_file in self.tests_dir.glob("*.json"):
            with open(test_file) as f:
                data = json.load(f)
                tests.append({
                    "filename": test_file.name,
                    "spec_source": data.get("spec_source"),
                    "seed_url": data.get("seed_url"),
                    "generated_at": data.get("generated_at"),
                    "test_count": len(data.get("tests", []))
                })
        
        return sorted(tests, key=lambda x: x.get("generated_at", ""), reverse=True)
    
    def get_test(self, filename: str) -> Optional[Dict]:
        """Retrieve a specific test suite by filename"""
        test_path = self.tests_dir / filename
        
        if test_path.exists():
            with open(test_path) as f:
                return json.load(f)
        
        return None
