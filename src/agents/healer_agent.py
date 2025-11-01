"""
🎭 Healer Agent - Executes tests and automatically repairs failures

Inspired by Playwright's healer, this agent:
1. Executes automation plans
2. Detects failures and broken selectors
3. Applies iterative healing with guardrails
4. Re-runs tests until they pass or reach max attempts
5. Skips tests that appear to have broken functionality
"""

import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime
import json
from pathlib import Path


class HealerAgent:
    """Enhanced self-healing with iterative repair loops and guardrails"""
    
    def __init__(self, runner, self_healer, openai_client):
        self.runner = runner
        self.self_healer = self_healer
        self.openai_client = openai_client
        self.reports_dir = Path("data/healing_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def heal_and_run(
        self,
        test_suite: Dict,
        max_heal_attempts: int = 3,
        confidence_threshold: float = 0.75,
        skip_on_functional_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Execute test suite with automatic healing
        
        Args:
            test_suite: Generated test suite from generator agent
            max_heal_attempts: Maximum healing iterations per test (default: 3)
            confidence_threshold: Minimum confidence for healing (default: 0.75)
            skip_on_functional_failure: Skip tests that appear functionally broken (default: True)
        
        Returns:
            Comprehensive healing report
        """
        results = {
            "test_suite_name": test_suite.get("spec_source", "unknown"),
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "healed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
        
        # Run each test with healing
        for test in test_suite.get("tests", []):
            test_result = await self._run_test_with_healing(
                test,
                test_suite.get("seed_url"),
                max_heal_attempts,
                confidence_threshold,
                skip_on_functional_failure
            )
            
            results["tests"].append(test_result)
            
            # Update summary
            results["summary"]["total"] += 1
            status = test_result.get("final_status")
            if status == "passed":
                results["summary"]["passed"] += 1
            elif status == "healed":
                results["summary"]["healed"] += 1
            elif status == "failed":
                results["summary"]["failed"] += 1
            elif status == "skipped":
                results["summary"]["skipped"] += 1
        
        results["end_time"] = datetime.now().isoformat()
        results["success_rate"] = (
            (results["summary"]["passed"] + results["summary"]["healed"]) / 
            max(results["summary"]["total"], 1)
        )
        
        # Save report
        report_path = self._save_report(results)
        results["report_path"] = str(report_path)
        
        return results
    
    async def _run_test_with_healing(
        self,
        test: Dict,
        seed_url: str,
        max_attempts: int,
        confidence_threshold: float,
        skip_on_functional_failure: bool
    ) -> Dict:
        """Run a single test with iterative healing"""
        
        test_result = {
            "scenario_name": test.get("scenario_name"),
            "attempts": [],
            "final_status": "unknown",
            "healing_applied": False,
            "healed_actions": []
        }
        
        automation_plan = test.get("automation_plan")
        
        for attempt_num in range(1, max_attempts + 1):
            attempt_result = await self._execute_test_attempt(
                automation_plan,
                seed_url,
                attempt_num
            )
            
            test_result["attempts"].append(attempt_result)
            
            # Check if test passed
            if attempt_result.get("status") == "success":
                test_result["final_status"] = "healed" if attempt_num > 1 else "passed"
                break
            
            # Check if failure is due to broken selectors or functional issue
            failure_analysis = await self._analyze_failure(
                attempt_result,
                automation_plan
            )
            
            if failure_analysis.get("is_functional_failure") and skip_on_functional_failure:
                test_result["final_status"] = "skipped"
                test_result["skip_reason"] = "Functionality appears broken"
                test_result["failure_analysis"] = failure_analysis
                break
            
            # If not last attempt, try healing
            if attempt_num < max_attempts:
                healed_plan = await self._heal_automation_plan(
                    automation_plan,
                    attempt_result,
                    confidence_threshold
                )
                
                if healed_plan.get("healing_applied"):
                    automation_plan = healed_plan["plan"]
                    test_result["healing_applied"] = True
                    test_result["healed_actions"].extend(healed_plan.get("healed_actions", []))
                else:
                    # Can't heal further, mark as failed
                    test_result["final_status"] = "failed"
                    test_result["failure_reason"] = "Unable to heal selectors"
                    break
        
        # If we exhausted all attempts
        if test_result["final_status"] == "unknown":
            test_result["final_status"] = "failed"
            test_result["failure_reason"] = "Max healing attempts reached"
        
        return test_result
    
    async def _execute_test_attempt(
        self,
        automation_plan: Dict,
        seed_url: str,
        attempt_num: int
    ) -> Dict:
        """Execute a single test attempt"""
        
        try:
            # Run the automation plan
            result = await self.runner.run_automation(
                plan=automation_plan.get("actions", []),
                start_url=seed_url
            )
            
            return {
                "attempt": attempt_num,
                "status": result.get("status", "failed"),
                "steps_completed": result.get("steps_completed", 0),
                "steps_total": len(automation_plan.get("actions", [])),
                "error": result.get("error"),
                "failed_action": result.get("failed_action"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "attempt": attempt_num,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_failure(
        self,
        attempt_result: Dict,
        automation_plan: Dict
    ) -> Dict:
        """Analyze whether failure is due to broken selectors or broken functionality"""
        
        failed_action = attempt_result.get("failed_action")
        error_message = attempt_result.get("error", "")
        
        # Check for selector-related errors
        selector_errors = [
            "timeout", "not found", "no element", 
            "selector", "locator", "unable to find"
        ]
        
        is_selector_issue = any(
            keyword in error_message.lower() 
            for keyword in selector_errors
        )
        
        # Use GPT to analyze if it seems like a functional failure
        if not is_selector_issue and failed_action:
            analysis = await self._gpt_analyze_failure(
                failed_action,
                error_message,
                automation_plan
            )
            
            return {
                "is_functional_failure": analysis.get("is_functional"),
                "is_selector_failure": False,
                "confidence": analysis.get("confidence"),
                "reason": analysis.get("reason")
            }
        
        return {
            "is_functional_failure": False,
            "is_selector_failure": is_selector_issue,
            "confidence": 0.9 if is_selector_issue else 0.5,
            "reason": "Selector error detected" if is_selector_issue else "Unknown failure"
        }
    
    async def _gpt_analyze_failure(
        self,
        failed_action: Dict,
        error_message: str,
        automation_plan: Dict
    ) -> Dict:
        """Use GPT to determine if failure is functional vs selector issue"""
        
        prompt = f"""Analyze this test failure:

FAILED ACTION: {json.dumps(failed_action, indent=2)}
ERROR MESSAGE: {error_message}

Determine if this is:
1. A SELECTOR ISSUE (element moved/changed but functionality works)
2. A FUNCTIONAL ISSUE (the feature itself is broken)

Respond in JSON format:
{{
  "is_functional": true/false,
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}}
"""
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a test failure analyst. Analyze failures precisely."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"is_functional": False, "confidence": 0.5, "reason": "Analysis failed"}
    
    async def _heal_automation_plan(
        self,
        automation_plan: Dict,
        attempt_result: Dict,
        confidence_threshold: float
    ) -> Dict:
        """Heal broken selectors in automation plan"""
        
        healed_plan = {"actions": []}
        healed_actions = []
        healing_applied = False
        
        failed_step_idx = attempt_result.get("steps_completed", 0)
        
        for idx, action in enumerate(automation_plan.get("actions", [])):
            # If this action failed and has a selector, try to heal it
            if idx == failed_step_idx and "selector" in action:
                description = action.get("description", "")
                
                # Use the existing self-healer
                healed = await self._heal_selector(
                    action.get("selector"),
                    description,
                    confidence_threshold
                )
                
                if healed and healed.get("confidence", 0) >= confidence_threshold:
                    # Apply healing
                    healed_action = action.copy()
                    healed_action["selector"] = healed["selector"]
                    healed_action["healed"] = True
                    healed_action["healing_confidence"] = healed["confidence"]
                    healed_action["original_selector"] = action["selector"]
                    
                    healed_plan["actions"].append(healed_action)
                    healed_actions.append({
                        "action_index": idx,
                        "original_selector": action["selector"],
                        "healed_selector": healed["selector"],
                        "confidence": healed["confidence"]
                    })
                    healing_applied = True
                else:
                    # Can't heal with sufficient confidence
                    healed_plan["actions"].append(action)
            else:
                # Keep action as-is
                healed_plan["actions"].append(action)
        
        return {
            "plan": healed_plan,
            "healing_applied": healing_applied,
            "healed_actions": healed_actions
        }
    
    async def _heal_selector(
        self,
        selector: str,
        description: str,
        confidence_threshold: float
    ) -> Optional[Dict]:
        """Heal a single selector using the self-healer"""
        
        # This would use the existing self-healer with page context
        # For now, return a placeholder - this will integrate with actual page
        return None
    
    def _save_report(self, results: Dict) -> Path:
        """Save healing report to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"healing_report_{timestamp}.json"
        
        report_path = self.reports_dir / filename
        
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)
        
        return report_path
    
    def list_reports(self) -> List[Dict]:
        """List all healing reports"""
        reports = []
        
        for report_file in self.reports_dir.glob("*.json"):
            with open(report_file) as f:
                data = json.load(f)
                reports.append({
                    "filename": report_file.name,
                    "test_suite": data.get("test_suite_name"),
                    "start_time": data.get("start_time"),
                    "success_rate": data.get("success_rate"),
                    "summary": data.get("summary")
                })
        
        return sorted(reports, key=lambda x: x.get("start_time", ""), reverse=True)
