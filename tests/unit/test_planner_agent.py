"""
Unit tests for Planner Agent
Tests plan creation, timeout strategies, and locator strategy selection
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from app.agents.planner import PlannerAgent


class MockEngine:
    """Mock engine for testing"""
    def __init__(self):
        self.llm = None


@pytest.fixture
def planner():
    """Create a Planner agent instance for testing"""
    engine = MockEngine()
    return PlannerAgent(engine)


class TestPlannerInitialization:
    """Test Planner agent initialization"""
    
    def test_planner_initializes_with_engine(self, planner):
        """Test that Planner initializes correctly"""
        assert planner.engine is not None
    
    def test_planner_has_system_prompt(self, planner):
        """Test that Planner has a system prompt"""
        assert hasattr(planner, 'PLANNER_SYSTEM_PROMPT')
        assert len(planner.PLANNER_SYSTEM_PROMPT) > 0


class TestPlanCreation:
    """Test plan creation logic"""
    
    @pytest.mark.asyncio
    async def test_create_plan_returns_dict(self, planner):
        """Test that create_plan returns a dictionary"""
        plan = await planner.create_plan('Navigate to Google', {})
        assert isinstance(plan, dict)
    
    @pytest.mark.asyncio
    async def test_plan_has_required_fields(self, planner):
        """Test that plan has all required fields"""
        plan = await planner.create_plan('Login to website', {})
        assert 'scenario_name' in plan
        assert 'description' in plan
        assert 'steps' in plan
        assert isinstance(plan['steps'], list)
    
    @pytest.mark.asyncio
    async def test_plan_steps_have_required_fields(self, planner):
        """Test that plan steps have required fields"""
        plan = await planner.create_plan('Click login button', {})
        if len(plan['steps']) > 0:
            step = plan['steps'][0]
            assert 'step_number' in step
            assert 'action' in step
            assert 'target' in step


class TestIntelligentParsing:
    """Test intelligent instruction parsing"""
    
    def test_parse_navigation_instruction(self, planner):
        """Test parsing of navigation instructions"""
        plan = planner._intelligent_parse_instruction('Navigate to https://google.com', {})
        assert len(plan['steps']) > 0
        assert any(step['action'] == 'navigate' for step in plan['steps'])
    
    def test_parse_login_instruction(self, planner):
        """Test parsing of login instructions"""
        plan = planner._intelligent_parse_instruction('Login with user@example.com and password123', {})
        assert len(plan['steps']) >= 2  # Should have fill steps for email and password
    
    def test_parse_search_instruction(self, planner):
        """Test parsing of search instructions"""
        plan = planner._intelligent_parse_instruction('Search for python tutorials', {})
        assert len(plan['steps']) > 0
    
    def test_parse_download_instruction(self, planner):
        """Test parsing of download instructions"""
        plan = planner._intelligent_parse_instruction('Download the PDF report', {})
        assert len(plan['steps']) > 0


class TestPromptEnhancements:
    """Test system prompt enhancements"""
    
    def test_prompt_includes_best_practices(self, planner):
        """Test that prompt includes best practices"""
        prompt = planner.PLANNER_SYSTEM_PROMPT
        assert 'Best Practices' in prompt
        assert 'role-based locators' in prompt
        assert 'timeout' in prompt
    
    def test_prompt_includes_timeout_guidance(self, planner):
        """Test that prompt includes timeout guidance"""
        prompt = planner.PLANNER_SYSTEM_PROMPT
        assert '10000' in prompt or '30000' in prompt  # Timeout values
        assert 'ms' in prompt.lower() or 'millisecond' in prompt.lower()
    
    def test_prompt_includes_critical_step_marking(self, planner):
        """Test that prompt includes critical step marking"""
        prompt = planner.PLANNER_SYSTEM_PROMPT
        assert 'critical' in prompt.lower()


class TestFallbackPlan:
    """Test fallback plan creation"""
    
    def test_fallback_plan_is_valid(self, planner):
        """Test that fallback plan is valid"""
        plan = planner._create_fallback_plan('Test instruction', {})
        assert isinstance(plan, dict)
        assert 'steps' in plan
        assert 'scenario_name' in plan
    
    def test_fallback_plan_has_steps(self, planner):
        """Test that fallback plan has at least one step"""
        plan = planner._create_fallback_plan('Navigate to website', {})
        assert len(plan['steps']) > 0
