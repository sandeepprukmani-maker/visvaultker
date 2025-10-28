"""
Unit tests for Generator Agent
Tests smart helpers, locators, assertions, and code generation
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from app.agents.generator import GeneratorAgent


class MockEngine:
    """Mock engine for testing"""
    def __init__(self):
        self.llm = None
        self.chat_model = None


@pytest.fixture
def generator():
    """Create a Generator agent instance for testing"""
    engine = MockEngine()
    return GeneratorAgent(engine)


@pytest.fixture
def sample_plan():
    """Sample execution plan for testing"""
    return {
        'scenario_name': 'Test Login',
        'description': 'Test user login automation',
        'url': 'https://example.com/login',
        'steps': [
            {
                'step_number': 1,
                'action': 'navigate',
                'target': 'https://example.com/login',
                'expected_result': 'Login page loads',
                'locator_strategy': 'url'
            },
            {
                'step_number': 2,
                'action': 'fill',
                'target': 'Email input field',
                'value': 'test@example.com',
                'expected_result': 'Email is entered',
                'locator_strategy': 'label'
            },
            {
                'step_number': 3,
                'action': 'click',
                'target': 'Submit button',
                'expected_result': 'Form is submitted',
                'locator_strategy': 'role'
            }
        ]
    }


class TestGeneratorInitialization:
    """Test Generator agent initialization"""
    
    def test_generator_initializes_with_correct_flags(self, generator):
        """Test that Generator initializes with smart features enabled"""
        assert generator.use_smart_helpers is True
        assert generator.use_fallback_chains is True
        assert generator.auto_assertions is True
        assert generator.locator_extractor is not None
    
    def test_generator_has_locator_strategies(self, generator):
        """Test that Generator has all locator strategies defined"""
        expected_strategies = ['role', 'text', 'label', 'placeholder', 'testid', 'title', 'alt', 'auto']
        for strategy in expected_strategies:
            assert strategy in generator.LOCATOR_STRATEGIES


class TestSmartHelperGeneration:
    """Test smart helper function generation"""
    
    def test_generate_smart_helpers_returns_code(self, generator):
        """Test that smart helpers are generated"""
        helpers = generator._generate_smart_helpers()
        assert helpers is not None
        assert len(helpers) > 0
        assert isinstance(helpers, str)
    
    def test_smart_helpers_contain_all_functions(self, generator):
        """Test that all smart helper functions are included"""
        helpers = generator._generate_smart_helpers()
        assert 'def smart_click(' in helpers
        assert 'def smart_fill(' in helpers
        assert 'def wait_for_element(' in helpers
        assert 'def smart_navigate(' in helpers
    
    def test_smart_click_has_retry_logic(self, generator):
        """Test that smart_click includes retry logic"""
        helpers = generator._generate_smart_helpers()
        assert 'for attempt in range(retry)' in helpers
        assert 'retry: int = 3' in helpers
    
    def test_smart_helpers_use_safe_eval(self, generator):
        """Test that helpers use safe eval with proper scope"""
        helpers = generator._generate_smart_helpers()
        assert 'eval(locator_expr, {"page": page, "expect": expect})' in helpers


class TestRichLocatorCreation:
    """Test rich locator creation"""
    
    def test_create_role_based_locator(self, generator):
        """Test role-based locator creation"""
        locator = generator._create_rich_locator('Submit button', 'role', 'click')
        assert 'page.get_by_role(' in locator
        assert 'button' in locator
        assert 'Submit' in locator
    
    def test_create_label_based_locator(self, generator):
        """Test label-based locator creation"""
        locator = generator._create_rich_locator('Email input field', 'label', 'fill')
        assert 'page.get_by_label(' in locator
        assert 'Email' in locator
        assert 'exact=False' in locator
    
    def test_create_text_based_locator(self, generator):
        """Test text-based locator creation"""
        locator = generator._create_rich_locator('Sign In link', 'text', 'click')
        assert 'page.get_by_text(' in locator
        assert 'Sign In' in locator
        assert 'exact=False' in locator
    
    def test_create_placeholder_locator(self, generator):
        """Test placeholder-based locator creation"""
        locator = generator._create_rich_locator('Enter email', 'placeholder', 'fill')
        assert 'page.get_by_placeholder(' in locator
        assert 'Enter email' in locator
    
    def test_auto_strategy_detects_button(self, generator):
        """Test auto strategy correctly identifies buttons"""
        locator = generator._create_rich_locator('Login button', 'auto', 'click')
        assert 'page.get_by_role(' in locator
    
    def test_auto_strategy_detects_input(self, generator):
        """Test auto strategy correctly identifies input fields"""
        locator = generator._create_rich_locator('Username input field', 'auto', 'fill')
        assert 'page.get_by_label(' in locator


class TestAssertionGeneration:
    """Test auto-generated assertion logic"""
    
    def test_assertion_for_navigation(self, generator):
        """Test assertion generation for navigation"""
        step = {
            'action': 'navigate',
            'expected_result': 'Page navigates to dashboard URL'
        }
        assertions = generator._generate_assertion_for_step(step)
        assert len(assertions) > 0
        assert any('wait_for_url' in a or 'navigation' in a.lower() for a in assertions)
    
    def test_assertion_for_visibility(self, generator):
        """Test assertion generation for element visibility"""
        step = {
            'action': 'click',
            'expected_result': 'Success message is visible'
        }
        assertions = generator._generate_assertion_for_step(step)
        assert len(assertions) > 0
        assert any('visible' in a.lower() for a in assertions)
    
    def test_assertion_for_form_submit(self, generator):
        """Test assertion generation for form submission"""
        step = {
            'action': 'click',
            'expected_result': 'Form submits successfully'
        }
        assertions = generator._generate_assertion_for_step(step)
        assert len(assertions) > 0
        assert any('networkidle' in a or 'complete' in a.lower() for a in assertions)
    
    def test_no_assertion_without_expected_result(self, generator):
        """Test that no assertion is generated without expected_result"""
        step = {'action': 'click', 'target': 'button'}
        assertions = generator._generate_assertion_for_step(step)
        assert len(assertions) == 0
    
    def test_no_assertion_when_disabled(self, generator):
        """Test assertions are skipped when disabled"""
        generator.auto_assertions = False
        step = {'action': 'click', 'expected_result': 'Success'}
        assertions = generator._generate_assertion_for_step(step)
        assert len(assertions) == 0


class TestActionCodeGeneration:
    """Test action-specific code generation"""
    
    def test_generate_click_code_with_smart_helpers(self, generator):
        """Test click code uses smart helpers when enabled"""
        code = generator._gen_click_code('Submit button', 'role')
        assert isinstance(code, list)
        assert any('smart_click' in line for line in code)
        assert any('Submit button' in line for line in code)
    
    def test_generate_click_code_without_smart_helpers(self, generator):
        """Test click code works without smart helpers"""
        generator.use_smart_helpers = False
        code = generator._gen_click_code('Submit button', 'role')
        assert isinstance(code, list)
        assert any('click()' in line for line in code)
        assert not any('smart_click' in line for line in code)
    
    def test_generate_fill_code_with_smart_helpers(self, generator):
        """Test fill code uses smart helpers"""
        code = generator._gen_fill_code('Email field', 'test@example.com', 'label')
        assert isinstance(code, list)
        assert any('smart_fill' in line for line in code)
    
    def test_generate_fill_code_handles_password(self, generator):
        """Test fill code uses environment variable for passwords"""
        code = generator._gen_fill_code('Password field', 'secret123', 'label')
        code_str = ' '.join(code)
        assert 'TEST_PASSWORD' in code_str or 'os.environ' in code_str
    
    def test_generate_navigate_code_with_smart_helpers(self, generator):
        """Test navigation code uses smart helpers"""
        code = generator._gen_navigate_code('https://example.com')
        assert isinstance(code, list)
        assert any('smart_navigate' in line for line in code)
    
    def test_generate_wait_code(self, generator):
        """Test wait code generation"""
        code = generator._gen_wait_code('Wait 2 seconds')
        assert isinstance(code, list)
        assert any('wait_for_timeout' in line for line in code)


class TestCompleteCodeGeneration:
    """Test complete script generation"""
    
    @pytest.mark.asyncio
    async def test_generate_code_returns_string(self, generator, sample_plan):
        """Test that generate_code returns a string"""
        script = await generator.generate_code(sample_plan, headless=True)
        assert isinstance(script, str)
        assert len(script) > 0
    
    @pytest.mark.asyncio
    async def test_generated_code_includes_imports(self, generator, sample_plan):
        """Test that generated code includes necessary imports"""
        script = await generator.generate_code(sample_plan, headless=True)
        assert 'from playwright.sync_api import' in script
        assert 'import sys' in script
        assert 'import os' in script
    
    @pytest.mark.asyncio
    async def test_generated_code_includes_smart_helpers(self, generator, sample_plan):
        """Test that generated code includes smart helper functions"""
        script = await generator.generate_code(sample_plan, headless=True)
        assert 'def smart_click(' in script
        assert 'def smart_fill(' in script
        assert 'def smart_navigate(' in script
    
    @pytest.mark.asyncio
    async def test_generated_code_has_main_function(self, generator, sample_plan):
        """Test that generated code has main entry point"""
        script = await generator.generate_code(sample_plan, headless=True)
        assert 'def main():' in script
        assert 'if __name__ == "__main__":' in script
    
    @pytest.mark.asyncio
    async def test_generated_code_includes_docstring(self, generator, sample_plan):
        """Test that generated code includes informative docstring"""
        script = await generator.generate_code(sample_plan, headless=True)
        assert 'Generated by VisionVault' in script
        assert 'Features:' in script
        assert 'Smart helper functions' in script
    
    @pytest.mark.asyncio
    async def test_generated_code_includes_all_steps(self, generator, sample_plan):
        """Test that all plan steps are included in generated code"""
        script = await generator.generate_code(sample_plan, headless=True)
        assert 'navigate' in script.lower()
        assert 'fill' in script.lower() or 'smart_fill' in script
        assert 'click' in script.lower() or 'smart_click' in script
    
    @pytest.mark.asyncio
    async def test_headless_mode_setting(self, generator, sample_plan):
        """Test that headless mode is correctly set"""
        script_headless = await generator.generate_code(sample_plan, headless=True)
        assert 'headless=True' in script_headless
        
        script_headful = await generator.generate_code(sample_plan, headless=False)
        assert 'headless=False' in script_headful


class TestHelperFunctions:
    """Test helper utility functions"""
    
    def test_slugify(self, generator):
        """Test slugify function"""
        result = generator._slugify('Test Login Scenario')
        assert result == 'test-login-scenario'
        assert ' ' not in result
    
    def test_extract_element_name(self, generator):
        """Test element name extraction"""
        result = generator._extract_element_name('the Submit button')
        assert 'Submit' in result
        assert 'the' not in result
        assert 'button' not in result
    
    def test_infer_role_from_target(self, generator):
        """Test role inference from target description"""
        assert generator._infer_role_from_target('Login button', 'click') == 'button'
        assert generator._infer_role_from_target('Home link', 'click') == 'link'
        assert generator._infer_role_from_target('Email textbox', 'fill') == 'textbox'
        assert generator._infer_role_from_target('Remember me checkbox', 'click') == 'checkbox'
