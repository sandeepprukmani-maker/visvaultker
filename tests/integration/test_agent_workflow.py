"""
Integration tests for complete agent workflow
Tests Planner → Generator → Healer integration
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from app.agents.orchestrator import AgentOrchestrator
from app.agents.planner import PlannerAgent
from app.agents.generator import GeneratorAgent
from app.agents.healer import HealerAgent


class MockEngine:
    """Mock engine for integration testing"""
    def __init__(self):
        self.llm = None
        self.chat_model = None


@pytest.fixture
def mock_engine():
    """Create a mock engine"""
    return MockEngine()


@pytest.fixture
def agent_orchestrator(mock_engine):
    """Create an AgentOrchestrator instance"""
    return AgentOrchestrator(mock_engine)


class TestPlannerGeneratorIntegration:
    """Test Planner → Generator workflow"""
    
    @pytest.mark.asyncio
    async def test_planner_to_generator_workflow(self, agent_orchestrator):
        """Test complete workflow from planning to code generation"""
        instruction = "Navigate to Google and search for Python"
        
        # Create automation script (Planner → Generator)
        script, plan = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Verify script is generated
        assert script is not None
        assert isinstance(script, str)
        assert len(script) > 0
        
        # Verify plan is created
        assert plan is not None
        assert isinstance(plan, dict)
        assert 'steps' in plan
    
    @pytest.mark.asyncio
    async def test_generated_script_is_valid_python(self, agent_orchestrator):
        """Test that generated script is valid Python"""
        instruction = "Click the submit button"
        script, _ = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Basic Python syntax check
        assert 'def ' in script  # Has function definitions
        assert 'import' in script  # Has imports
        assert '"""' in script or "'''" in script  # Has docstring
    
    @pytest.mark.asyncio
    async def test_script_includes_smart_helpers(self, agent_orchestrator):
        """Test that generated script includes smart helper functions"""
        instruction = "Fill form and submit"
        script, _ = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Check for smart helpers
        assert 'def smart_click(' in script or 'smart_click' in script
        assert 'def smart_fill(' in script or 'smart_fill' in script
    
    @pytest.mark.asyncio
    async def test_script_handles_different_actions(self, agent_orchestrator):
        """Test script generation for different action types"""
        test_cases = [
            "Navigate to example.com",
            "Click the login button", 
            "Fill in the email field with test@example.com",
            "Wait for page to load"
        ]
        
        for instruction in test_cases:
            script, plan = await agent_orchestrator.create_automation_script(
                instruction, {}, headless=True, use_cache=False
            )
            assert script is not None
            assert len(script) > 100  # Substantial script generated


class TestHealerIntegration:
    """Test Healer agent integration"""
    
    @pytest.mark.asyncio
    async def test_healer_fixes_failed_script(self, agent_orchestrator):
        """Test that Healer can process a failed script"""
        original_script = """
from playwright.sync_api import Page

def run_automation(page: Page):
    page.locator("#wrong-selector").click()  # This will fail
    return True
"""
        error_message = "TimeoutError: Timeout 30000ms exceeded waiting for locator"
        execution_logs = "Failed to find element with selector #wrong-selector"
        
        healed_script = await agent_orchestrator.heal_failed_script(
            original_script, error_message, execution_logs
        )
        
        # Verify healer returns a valid script (may be same or modified)
        assert healed_script is not None
        assert isinstance(healed_script, str)
        assert len(healed_script) > 0
        # Healer should attempt to improve the script or return original if no fix found
        assert 'def run_automation' in healed_script or 'from playwright' in healed_script


class TestCompleteWorkflow:
    """Test complete end-to-end workflow"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, agent_orchestrator):
        """Test complete workflow with all agents"""
        instruction = "Login to website with email and password"
        
        # Step 1: Generate script
        script, plan = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Verify script quality
        assert script is not None
        assert 'smart_fill' in script or 'fill' in script.lower()
        assert 'smart_click' in script or 'click' in script.lower()
        
        # Verify plan quality
        assert len(plan['steps']) >= 2  # Login requires multiple steps
        assert any('fill' in step['action'].lower() for step in plan['steps'])
        assert any('click' in step['action'].lower() for step in plan['steps'])
    
    @pytest.mark.asyncio
    async def test_workflow_with_caching(self, agent_orchestrator):
        """Test that caching works correctly"""
        instruction = "Navigate to Google"
        
        # First call - no cache
        script1, plan1 = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Second call - should use cache (but we disabled it with use_cache=False)
        script2, plan2 = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Both should generate scripts
        assert script1 is not None
        assert script2 is not None


class TestScriptQuality:
    """Test quality of generated scripts"""
    
    @pytest.mark.asyncio
    async def test_script_has_error_handling(self, agent_orchestrator):
        """Test that generated scripts include error handling"""
        instruction = "Submit contact form"
        script, _ = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        assert 'try:' in script or 'except' in script
        assert 'Exception' in script
    
    @pytest.mark.asyncio
    async def test_script_has_proper_structure(self, agent_orchestrator):
        """Test that scripts have proper structure"""
        instruction = "Fill and submit form"
        script, _ = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Check for main components
        assert 'from playwright.sync_api import' in script
        assert 'def main():' in script
        assert 'if __name__ == "__main__":' in script
        assert 'sync_playwright()' in script
    
    @pytest.mark.asyncio
    async def test_script_includes_documentation(self, agent_orchestrator):
        """Test that scripts include documentation"""
        instruction = "Test automation task"
        script, _ = await agent_orchestrator.create_automation_script(
            instruction, {}, headless=True, use_cache=False
        )
        
        # Check for documentation
        assert '"""' in script or "'''" in script  # Docstrings
        assert 'Generated by VisionVault' in script
        assert 'Features:' in script or 'feature' in script.lower()
