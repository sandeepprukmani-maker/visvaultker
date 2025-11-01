"""
Agentic Loop - Chains planner → generator → healer for full test automation

This orchestrates the three agents in sequence or as an iterative loop:
1. Planner explores and creates test specs
2. Generator converts specs to executable tests
3. Healer runs and repairs tests

Can run in single-pass or continuous improvement mode.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path


class AgenticLoop:
    """Orchestrates the planner, generator, and healer agents"""
    
    def __init__(self, planner_agent, generator_agent, healer_agent):
        self.planner = planner_agent
        self.generator = generator_agent
        self.healer = healer_agent
        self.loop_dir = Path("data/loop_results")
        self.loop_dir.mkdir(parents=True, exist_ok=True)
    
    async def run_full_loop(
        self,
        url: str,
        scenarios: List[str],
        seed_context: Optional[Dict] = None,
        prd: Optional[str] = None,
        max_heal_attempts: int = 3,
        confidence_threshold: float = 0.75
    ) -> Dict[str, Any]:
        """
        Run complete agentic loop: planner → generator → healer
        
        Args:
            url: Starting URL to test
            scenarios: List of test scenarios to generate
            seed_context: Optional seed test context
            prd: Optional product requirements document
            max_heal_attempts: Max healing iterations per test
            confidence_threshold: Minimum confidence for healing
        
        Returns:
            Complete loop results including all agent outputs
        """
        loop_result = {
            "url": url,
            "scenarios": scenarios,
            "start_time": datetime.now().isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 1: Planning
            print(f"🎭 Planner: Exploring {url} and generating test plan...")
            planner_result = await self.planner.explore_and_plan(
                url=url,
                scenarios=scenarios,
                seed_context=seed_context,
                prd=prd
            )
            
            loop_result["stages"]["planning"] = {
                "status": "success",
                "result": planner_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Stage 2: Generation
            print(f"🎭 Generator: Converting specs to executable tests...")
            
            # Read the generated spec
            spec_path = planner_result["spec_path"]
            with open(spec_path, "r") as f:
                spec_content = f.read()
            
            generator_result = await self.generator.generate_from_spec(
                spec_content=spec_content,
                spec_filename=Path(spec_path).name,
                seed_url=url,
                verify_selectors=True
            )
            
            loop_result["stages"]["generation"] = {
                "status": "success",
                "result": generator_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Stage 3: Healing
            print(f"🎭 Healer: Running tests with automatic healing...")
            
            healer_result = await self.healer.heal_and_run(
                test_suite=generator_result,
                max_heal_attempts=max_heal_attempts,
                confidence_threshold=confidence_threshold
            )
            
            loop_result["stages"]["healing"] = {
                "status": "success",
                "result": healer_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # Calculate overall success
            loop_result["success"] = True
            loop_result["test_success_rate"] = healer_result.get("success_rate", 0)
            
        except Exception as e:
            loop_result["success"] = False
            loop_result["error"] = str(e)
            loop_result["error_stage"] = self._determine_error_stage(loop_result)
        
        loop_result["end_time"] = datetime.now().isoformat()
        
        # Save loop results
        result_path = self._save_loop_result(loop_result)
        loop_result["result_path"] = str(result_path)
        
        return loop_result
    
    async def run_planner_only(
        self,
        url: str,
        scenarios: List[str],
        seed_context: Optional[Dict] = None,
        prd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run only the planner agent"""
        return await self.planner.explore_and_plan(
            url=url,
            scenarios=scenarios,
            seed_context=seed_context,
            prd=prd
        )
    
    async def run_generator_only(
        self,
        spec_filename: str,
        seed_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run only the generator agent on an existing spec"""
        
        # Read spec
        spec_path = self.planner.specs_dir / spec_filename
        
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec not found: {spec_filename}")
        
        with open(spec_path, "r") as f:
            spec_content = f.read()
        
        return await self.generator.generate_from_spec(
            spec_content=spec_content,
            spec_filename=spec_filename,
            seed_url=seed_url,
            verify_selectors=True
        )
    
    async def run_healer_only(
        self,
        test_filename: str,
        max_heal_attempts: int = 3,
        confidence_threshold: float = 0.75
    ) -> Dict[str, Any]:
        """Run only the healer agent on an existing test suite"""
        
        # Read test suite
        test_path = self.generator.tests_dir / test_filename
        
        if not test_path.exists():
            raise FileNotFoundError(f"Test suite not found: {test_filename}")
        
        with open(test_path, "r") as f:
            test_suite = json.load(f)
        
        return await self.healer.heal_and_run(
            test_suite=test_suite,
            max_heal_attempts=max_heal_attempts,
            confidence_threshold=confidence_threshold
        )
    
    def _determine_error_stage(self, loop_result: Dict) -> str:
        """Determine which stage the error occurred in"""
        if "planning" not in loop_result["stages"]:
            return "planning"
        elif "generation" not in loop_result["stages"]:
            return "generation"
        elif "healing" not in loop_result["stages"]:
            return "healing"
        return "unknown"
    
    def _save_loop_result(self, loop_result: Dict) -> Path:
        """Save complete loop results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"loop_result_{timestamp}.json"
        
        result_path = self.loop_dir / filename
        
        with open(result_path, "w") as f:
            json.dump(loop_result, f, indent=2)
        
        return result_path
    
    def list_loop_results(self) -> List[Dict]:
        """List all loop execution results"""
        results = []
        
        for result_file in self.loop_dir.glob("*.json"):
            with open(result_file) as f:
                data = json.load(f)
                results.append({
                    "filename": result_file.name,
                    "url": data.get("url"),
                    "scenarios": data.get("scenarios"),
                    "success": data.get("success"),
                    "test_success_rate": data.get("test_success_rate"),
                    "start_time": data.get("start_time")
                })
        
        return sorted(results, key=lambda x: x.get("start_time", ""), reverse=True)
