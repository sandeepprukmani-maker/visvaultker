"""
Intelligent Automation Coordinator
Makes browser automation intelligent enough to handle ANY task by:
- Adaptive strategy selection
- Multi-approach fallback mechanisms
- Real-time learning from failures
- Dynamic LLM configuration based on complexity
- Intelligent instruction decomposition
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"  # Single action: "click button"
    MODERATE = "moderate"  # 2-3 steps: "login to website"
    COMPLEX = "complex"  # Multi-step: "login, search, extract data"
    ADVANCED = "advanced"  # Requires reasoning: "compare prices across sites"


class IntelligentCoordinator:
    """
    Coordinates intelligent browser automation by analyzing tasks,
    selecting optimal strategies, and providing fallback mechanisms
    """
    
    def __init__(self):
        """Initialize intelligent coordinator"""
        self.task_patterns = self._initialize_task_patterns()
        self.strategy_success_rates = {}  # Track which strategies work best
        
    def analyze_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Deeply analyze instruction to understand intent, complexity, and requirements
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Analysis dictionary with task breakdown and recommendations
        """
        logger.info(f"🧠 Analyzing instruction: {instruction[:100]}...")
        
        # Determine complexity
        complexity = self._assess_complexity(instruction)
        
        # Detect task type
        task_type = self._detect_task_type(instruction)
        
        # Break down into sub-tasks
        subtasks = self._decompose_instruction(instruction)
        
        # Detect verification requirements
        needs_verification = self._detect_verification_needs(instruction)
        
        # Recommend engine and configuration
        engine_recommendation = self._recommend_engine(complexity, task_type)
        
        # Suggest LLM temperature based on task
        temperature = self._recommend_temperature(complexity, task_type)
        
        analysis = {
            'complexity': complexity.value,
            'task_type': task_type,
            'subtasks': subtasks,
            'subtask_count': len(subtasks),
            'needs_verification': needs_verification,
            'verification_type': self._get_verification_type(instruction) if needs_verification else None,
            'recommended_engine': engine_recommendation,
            'recommended_temperature': temperature,
            'estimated_steps': self._estimate_steps(subtasks, complexity),
            'risk_factors': self._identify_risk_factors(instruction),
            'fallback_strategies': self._generate_fallback_strategies(task_type, complexity)
        }
        
        logger.info(f"📊 Analysis: {complexity.value} task, {len(subtasks)} subtasks, "
                   f"engine={engine_recommendation}, temp={temperature}")
        
        return analysis
    
    def _assess_complexity(self, instruction: str) -> TaskComplexity:
        """Assess instruction complexity"""
        instruction_lower = instruction.lower()
        
        # Count action words
        action_words = ['click', 'type', 'fill', 'select', 'navigate', 'go to', 
                       'search', 'find', 'extract', 'download', 'upload', 'scroll',
                       'wait', 'verify', 'check', 'compare', 'login', 'logout']
        
        action_count = sum(1 for word in action_words if word in instruction_lower)
        
        # Check for complex indicators
        complex_indicators = [
            'compare', 'analyze', 'multiple', 'all', 'each', 'every',
            'different', 'various', 'several', 'if', 'when', 'unless',
            'until', 'while', 'repeat', 'loop', 'for each'
        ]
        has_complex_logic = any(indicator in instruction_lower for indicator in complex_indicators)
        
        # Check for multi-site operations
        url_count = len(re.findall(r'https?://|\.com|\.org|\.net', instruction_lower))
        
        # Determine complexity
        if has_complex_logic or url_count > 2:
            return TaskComplexity.ADVANCED
        elif action_count > 5 or url_count > 1:
            return TaskComplexity.COMPLEX
        elif action_count > 2 or 'login' in instruction_lower:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE
    
    def _detect_task_type(self, instruction: str) -> str:
        """Detect the primary task type"""
        instruction_lower = instruction.lower()
        
        for pattern_type, patterns in self.task_patterns.items():
            if any(pattern in instruction_lower for pattern in patterns):
                return pattern_type
        
        return 'general'
    
    def _initialize_task_patterns(self) -> Dict[str, List[str]]:
        """Initialize common task patterns"""
        return {
            'login': ['login', 'log in', 'sign in', 'authenticate', 'credentials'],
            'search': ['search', 'find', 'look for', 'query'],
            'data_extraction': ['extract', 'scrape', 'get data', 'collect', 'download'],
            'form_filling': ['fill', 'submit', 'enter', 'complete form', 'application'],
            'navigation': ['navigate', 'go to', 'visit', 'open', 'browse to'],
            'verification': ['verify', 'check', 'confirm', 'validate', 'ensure'],
            'comparison': ['compare', 'difference', 'vs', 'versus', 'contrast'],
            'purchase': ['buy', 'purchase', 'checkout', 'add to cart', 'order'],
            'booking': ['book', 'reserve', 'schedule', 'appointment'],
            'upload': ['upload', 'attach', 'add file'],
            'download': ['download', 'save', 'export']
        }
    
    def _decompose_instruction(self, instruction: str) -> List[str]:
        """
        Break complex instruction into subtasks
        Handles conjunctions and sequential indicators
        """
        # Split on common separators
        separators = [
            r'\s+then\s+', r'\s+and then\s+', r'\s+after that\s+',
            r'\s+next\s+', r'\s+finally\s+', r'\s+afterwards\s+',
            r',\s+then\s+', r'\.\s+', r';\s+'
        ]
        
        subtasks = [instruction]
        for separator in separators:
            new_subtasks = []
            for task in subtasks:
                parts = re.split(separator, task, flags=re.IGNORECASE)
                new_subtasks.extend([p.strip() for p in parts if p.strip()])
            subtasks = new_subtasks
        
        # Filter out very short tasks (likely artifacts)
        subtasks = [task for task in subtasks if len(task) > 10]
        
        return subtasks if len(subtasks) > 1 else [instruction]
    
    def _detect_verification_needs(self, instruction: str) -> bool:
        """Detect if instruction requires verification"""
        verification_keywords = [
            'verify', 'check', 'ensure', 'validate', 'confirm',
            'make sure', 'assert', 'test', 'should contain',
            'should have', 'must', 'required', 'expect'
        ]
        
        instruction_lower = instruction.lower()
        return any(keyword in instruction_lower for keyword in verification_keywords)
    
    def _get_verification_type(self, instruction: str) -> str:
        """Determine what type of verification is needed"""
        instruction_lower = instruction.lower()
        
        if 'text' in instruction_lower or 'contains' in instruction_lower:
            return 'text_content'
        elif 'url' in instruction_lower or 'page' in instruction_lower:
            return 'navigation'
        elif 'visible' in instruction_lower or 'appears' in instruction_lower:
            return 'element_visibility'
        elif 'count' in instruction_lower or 'number' in instruction_lower:
            return 'count'
        else:
            return 'general'
    
    def _recommend_engine(self, complexity: TaskComplexity, task_type: str) -> str:
        """
        Recommend best engine based on task characteristics
        
        Browser Use: Better for visual/interactive tasks
        Playwright MCP: Better for precise control and data extraction
        """
        # Playwright MCP for precise tasks
        if task_type in ['data_extraction', 'verification', 'comparison']:
            return 'playwright_mcp'
        
        # Playwright MCP for complex multi-step workflows
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED]:
            return 'playwright_mcp'
        
        # Browser Use for simple interactive tasks
        return 'browser_use'
    
    def _recommend_temperature(self, complexity: TaskComplexity, task_type: str) -> float:
        """
        Recommend LLM temperature based on task
        
        Lower temp (0.1-0.3): Precise, deterministic tasks
        Medium temp (0.4-0.6): Balanced tasks
        Higher temp (0.7-0.9): Creative, flexible tasks
        """
        # Precise tasks need low temperature
        if task_type in ['data_extraction', 'verification', 'form_filling']:
            return 0.2
        
        # Complex reasoning needs medium-high temperature
        if complexity == TaskComplexity.ADVANCED:
            return 0.7
        
        # Complex tasks need medium temperature
        if complexity == TaskComplexity.COMPLEX:
            return 0.5
        
        # Simple tasks can use medium temperature
        return 0.6
    
    def _estimate_steps(self, subtasks: List[str], complexity: TaskComplexity) -> int:
        """Estimate number of steps needed"""
        base_steps = len(subtasks) * 2  # Each subtask typically needs 2-3 steps
        
        complexity_multiplier = {
            TaskComplexity.SIMPLE: 1.0,
            TaskComplexity.MODERATE: 1.5,
            TaskComplexity.COMPLEX: 2.0,
            TaskComplexity.ADVANCED: 2.5
        }
        
        estimated = int(base_steps * complexity_multiplier[complexity])
        return max(5, min(estimated, 50))  # Clamp between 5 and 50
    
    def _identify_risk_factors(self, instruction: str) -> List[str]:
        """Identify potential failure points"""
        risks = []
        instruction_lower = instruction.lower()
        
        if 'login' in instruction_lower or 'password' in instruction_lower:
            risks.append('authentication_required')
        
        if 'captcha' in instruction_lower:
            risks.append('captcha_challenge')
        
        if 'dynamic' in instruction_lower or 'ajax' in instruction_lower:
            risks.append('dynamic_content')
        
        if 'popup' in instruction_lower or 'modal' in instruction_lower:
            risks.append('popup_handling')
        
        if 'download' in instruction_lower or 'file' in instruction_lower:
            risks.append('file_handling')
        
        if 'multiple' in instruction_lower or 'all' in instruction_lower:
            risks.append('multiple_elements')
        
        return risks
    
    def _generate_fallback_strategies(self, task_type: str, complexity: TaskComplexity) -> List[str]:
        """Generate fallback strategies if primary approach fails"""
        strategies = ['retry_with_longer_waits']
        
        # Add task-specific fallbacks
        if task_type == 'login':
            strategies.extend([
                'try_alternative_login_method',
                'check_for_security_prompts',
                'verify_credentials_format'
            ])
        
        elif task_type == 'search':
            strategies.extend([
                'try_alternative_search_methods',
                'check_autocomplete_suggestions',
                'verify_search_box_focus'
            ])
        
        elif task_type == 'data_extraction':
            strategies.extend([
                'try_alternative_selectors',
                'wait_for_content_load',
                'check_pagination'
            ])
        
        # Add complexity-based fallbacks
        if complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED]:
            strategies.extend([
                'break_into_smaller_steps',
                'increase_max_steps_limit',
                'use_alternative_engine'
            ])
        
        return strategies
    
    def enhance_instruction(self, instruction: str, analysis: Dict[str, Any]) -> str:
        """
        Enhance instruction with intelligent context and guidance
        
        Args:
            instruction: Original instruction
            analysis: Task analysis from analyze_instruction
            
        Returns:
            Enhanced instruction with strategic guidance
        """
        enhancements = []
        
        # Add complexity-aware guidance
        if analysis['complexity'] in ['complex', 'advanced']:
            enhancements.append(
                "⚠️ COMPLEX TASK DETECTED - Take your time and verify each step.\n"
                "Break this into smaller sequential operations."
            )
        
        # Add verification guidance
        if analysis['needs_verification']:
            enhancements.append(
                f"🔍 VERIFICATION REQUIRED ({analysis['verification_type']})\n"
                "You MUST explicitly report verification results (PASS/FAIL)."
            )
        
        # Add risk mitigation
        if analysis['risk_factors']:
            risk_guidance = "⚠️ RISK FACTORS:\n"
            for risk in analysis['risk_factors']:
                risk_guidance += f"  - {risk.replace('_', ' ').title()}\n"
            risk_guidance += "Handle these carefully with appropriate waits and checks."
            enhancements.append(risk_guidance)
        
        # Add subtask breakdown for complex tasks
        if len(analysis['subtasks']) > 1:
            subtask_list = "\n".join([f"  {i+1}. {task}" for i, task in enumerate(analysis['subtasks'])])
            enhancements.append(
                f"📋 TASK BREAKDOWN ({len(analysis['subtasks'])} steps):\n{subtask_list}\n"
                "Execute these in order, completing each before moving to the next."
            )
        
        # Add strategic guidance
        strategies = self._get_strategic_guidance(analysis['task_type'])
        if strategies:
            enhancements.append(f"💡 STRATEGY:\n{strategies}")
        
        # Combine enhancements with original instruction
        if enhancements:
            enhanced = "\n\n".join(enhancements) + "\n\n" + "🎯 YOUR TASK:\n" + instruction
            logger.info(f"✨ Enhanced instruction with {len(enhancements)} intelligence layers")
            return enhanced
        
        return instruction
    
    def _get_strategic_guidance(self, task_type: str) -> str:
        """Get strategic guidance for specific task types"""
        strategies = {
            'login': (
                "- Locate username/email field first, then password field\n"
                "- Wait for page to fully load before entering credentials\n"
                "- Look for 'Login', 'Sign In', or 'Submit' button\n"
                "- Check for security prompts or CAPTCHA after submission"
            ),
            'search': (
                "- Locate search input/box with high confidence\n"
                "- Click to focus before typing\n"
                "- Wait briefly after typing for autocomplete\n"
                "- Press Enter or click search button\n"
                "- Wait for results to load completely"
            ),
            'data_extraction': (
                "- Wait for all dynamic content to load\n"
                "- Identify container elements first\n"
                "- Extract data systematically (don't rush)\n"
                "- Verify data completeness before returning\n"
                "- Handle pagination if present"
            ),
            'form_filling': (
                "- Fill fields in logical order (top to bottom)\n"
                "- Wait for each field to accept input\n"
                "- Handle dropdowns and selects carefully\n"
                "- Verify required fields are filled\n"
                "- Double-check before final submission"
            )
        }
        
        return strategies.get(task_type, "")


def create_intelligent_execution_plan(instruction: str) -> Dict[str, Any]:
    """
    Convenience function to create a full execution plan
    
    Args:
        instruction: User's natural language instruction
        
    Returns:
        Complete execution plan with analysis and enhanced instruction
    """
    coordinator = IntelligentCoordinator()
    analysis = coordinator.analyze_instruction(instruction)
    enhanced_instruction = coordinator.enhance_instruction(instruction, analysis)
    
    return {
        'original_instruction': instruction,
        'enhanced_instruction': enhanced_instruction,
        'analysis': analysis,
        'execution_config': {
            'engine': analysis['recommended_engine'],
            'temperature': analysis['recommended_temperature'],
            'estimated_max_steps': analysis['estimated_steps']
        }
    }
