"""
Enhanced Prompt Generation Service
Generates detailed prompts with accurate element locators and actions
instead of directly generating code
"""
import logging
from typing import Dict, Any, List
from dataclasses import dataclass
from app.services.intelligent_validator import IntelligentValidator, validate_task_sync

logger = logging.getLogger(__name__)


@dataclass
class DetailedPrompt:
    """Detailed prompt with validated element information"""
    task_description: str
    url: str
    steps: List[Dict[str, Any]]
    validation_results: Dict[str, Any]
    prompt_text: str
    confidence_score: float
    

class EnhancedPromptGenerator:
    """
    Generates detailed, validated prompts for AI script generation
    
    Instead of directly generating code (which may have errors),
    this creates detailed prompts with:
    - Validated element locators
    - Accurate actions to perform
    - Confidence scoring
    - Alternative strategies
    - Context about page structure
    """
    
    def __init__(self):
        """Initialize the prompt generator"""
        self.validator = IntelligentValidator()
        
    async def generate_detailed_prompt(
        self,
        task_description: str,
        url: str,
        steps: List[Dict[str, Any]],
        headless: bool = True
    ) -> DetailedPrompt:
        """
        Generate a detailed prompt by validating elements and actions
        
        Args:
            task_description: High-level task description
            url: Target URL
            steps: List of steps from planner
            headless: Run validation in headless mode
            
        Returns:
            DetailedPrompt with validated information
        """
        logger.info(f"🎯 Generating detailed prompt for: {task_description}")
        
        # Validate the task
        validation_results = await self.validator.validate_task(url, steps, headless)
        
        if not validation_results.get('success'):
            logger.warning("⚠️  Validation failed, generating prompt anyway")
        
        # Build detailed prompt text
        prompt_text = self._build_prompt_text(
            task_description,
            url,
            validation_results
        )
        
        # Calculate overall confidence
        confidence = self._calculate_overall_confidence(validation_results)
        
        logger.info(f"✅ Detailed prompt generated (confidence: {confidence:.2%})")
        
        return DetailedPrompt(
            task_description=task_description,
            url=url,
            steps=validation_results.get('validated_steps', steps),
            validation_results=validation_results,
            prompt_text=prompt_text,
            confidence_score=confidence
        )
    
    def _build_prompt_text(
        self,
        task: str,
        url: str,
        validation: Dict[str, Any]
    ) -> str:
        """Build detailed prompt text for AI script generation"""
        
        page_val = validation.get('page_validation', {})
        validated_steps = validation.get('validated_steps', [])
        
        prompt_parts = []
        
        # Header
        prompt_parts.append("# Browser Automation Script Requirements\n")
        prompt_parts.append(f"**Task**: {task}\n")
        prompt_parts.append(f"**Target URL**: {url}\n")
        
        # Page information
        if page_val:
            prompt_parts.append(f"\n## Page Information")
            prompt_parts.append(f"- Title: {page_val.get('title', 'N/A')}")
            
            structure = page_val.get('page_structure', {})
            if structure:
                interactive = structure.get('interactive_elements', {})
                prompt_parts.append(f"\n### Page Structure")
                prompt_parts.append(f"- Buttons: {interactive.get('buttons', 0)}")
                prompt_parts.append(f"- Links: {interactive.get('links', 0)}")
                prompt_parts.append(f"- Inputs: {interactive.get('inputs', 0)}")
                prompt_parts.append(f"- Forms: {interactive.get('forms', 0)}")
                
                frameworks = structure.get('frameworks', [])
                if frameworks:
                    prompt_parts.append(f"- Detected Frameworks: {', '.join(frameworks)}")
        
        # Steps with validated locators
        prompt_parts.append(f"\n## Automation Steps\n")
        
        for i, step in enumerate(validated_steps, 1):
            action = step.get('action', 'unknown')
            target = step.get('target', '')
            value = step.get('value', '')
            
            prompt_parts.append(f"### Step {i}: {action.upper()}")
            
            if action == 'navigate':
                prompt_parts.append(f"- **Action**: Navigate to URL")
                prompt_parts.append(f"- **URL**: {target}")
                
            elif action in ['click', 'fill', 'select', 'verify']:
                prompt_parts.append(f"- **Action**: {action.capitalize()}")
                prompt_parts.append(f"- **Target**: {target}")
                
                # Add validation information
                validation_info = step.get('validation')
                if validation_info and validation_info.exists:
                    prompt_parts.append(f"- **Element Found**: Yes ✓")
                    prompt_parts.append(f"- **Validated Locator**: `{validation_info.locator}`")
                    prompt_parts.append(f"- **Locator Strategy**: {validation_info.locator_strategy}")
                    prompt_parts.append(f"- **Confidence**: {validation_info.confidence:.1%}")
                    
                    # Element details
                    elem_info = validation_info.element_info
                    if elem_info:
                        prompt_parts.append(f"- **Element Details**:")
                        if elem_info.get('tag'):
                            prompt_parts.append(f"  - Tag: `{elem_info.get('tag')}`")
                        if elem_info.get('text'):
                            prompt_parts.append(f"  - Text: \"{elem_info.get('text')[:50]}\"")
                        if elem_info.get('type'):
                            prompt_parts.append(f"  - Type: `{elem_info.get('type')}`")
                        if elem_info.get('visible'):
                            prompt_parts.append(f"  - Visible: Yes ✓")
                    
                    # Alternative locators
                    alternatives = validation_info.alternatives
                    if alternatives:
                        prompt_parts.append(f"- **Alternative Locators**:")
                        for alt in alternatives[:2]:  # Show top 2 alternatives
                            prompt_parts.append(
                                f"  - `{alt.get('locator')}` "
                                f"(strategy: {alt.get('strategy')}, "
                                f"confidence: {alt.get('confidence', 0):.1%})"
                            )
                else:
                    prompt_parts.append(f"- **Element Found**: No ✗")
                    prompt_parts.append(f"- **Suggested Approach**: Use flexible text-based or role-based locator")
                
                if value:
                    prompt_parts.append(f"- **Value**: {value}")
                    
            elif action == 'wait':
                prompt_parts.append(f"- **Action**: Wait")
                prompt_parts.append(f"- **Duration**: {target}")
                
            else:
                prompt_parts.append(f"- **Action**: {action}")
                prompt_parts.append(f"- **Target**: {target}")
            
            expected = step.get('expected_result')
            if expected:
                prompt_parts.append(f"- **Expected Result**: {expected}")
            
            prompt_parts.append("")  # Blank line
        
        # Code generation instructions
        prompt_parts.append("\n## Code Generation Instructions\n")
        prompt_parts.append("Generate a Python Playwright script that:")
        prompt_parts.append("1. Uses the **validated locators** provided above")
        prompt_parts.append("2. Includes proper error handling and waits")
        prompt_parts.append("3. Uses the locator strategies with highest confidence")
        prompt_parts.append("4. Adds .first or proper filtering if needed for uniqueness")
        prompt_parts.append("5. Implements smart helper functions for reliability")
        prompt_parts.append("6. Uses async/await for all Playwright operations")
        prompt_parts.append("7. Includes comments showing the validated element details")
        
        return "\n".join(prompt_parts)
    
    def _calculate_overall_confidence(self, validation: Dict[str, Any]) -> float:
        """Calculate overall confidence score from validation results"""
        if not validation.get('success'):
            return 0.3
        
        validated_steps = validation.get('validated_steps', [])
        if not validated_steps:
            return 0.5
        
        # Calculate average confidence of validated elements
        confidences = []
        for step in validated_steps:
            val = step.get('validation')
            if val and hasattr(val, 'confidence'):
                confidences.append(val.confidence)
        
        if not confidences:
            return 0.6
        
        return sum(confidences) / len(confidences)
    
    def generate_prompt_sync(
        self,
        task_description: str,
        url: str,
        steps: List[Dict[str, Any]],
        headless: bool = True
    ) -> DetailedPrompt:
        """Synchronous version of generate_detailed_prompt"""
        import asyncio
        return asyncio.run(
            self.generate_detailed_prompt(task_description, url, steps, headless)
        )
    
    def create_simplified_instructions(self, detailed_prompt: DetailedPrompt) -> str:
        """
        Create simplified, human-readable instructions from detailed prompt
        
        This is useful for displaying to users or for AI model input
        """
        lines = []
        
        lines.append(f"Task: {detailed_prompt.task_description}")
        lines.append(f"URL: {detailed_prompt.url}")
        lines.append(f"Confidence: {detailed_prompt.confidence_score:.1%}\n")
        
        lines.append("Steps:")
        for i, step in enumerate(detailed_prompt.steps, 1):
            action = step.get('action', '')
            target = step.get('target', '')
            
            val = step.get('validation')
            if val and val.exists:
                lines.append(
                    f"{i}. {action.upper()} {target} "
                    f"[locator: {val.locator_strategy}, "
                    f"confidence: {val.confidence:.0%}]"
                )
            else:
                lines.append(f"{i}. {action.upper()} {target}")
        
        return "\n".join(lines)


def generate_detailed_prompt_from_plan(
    plan: Dict[str, Any],
    headless: bool = True
) -> DetailedPrompt:
    """
    Generate detailed prompt from a planner's plan
    
    Args:
        plan: Plan dict from PlannerAgent
        headless: Run validation headless
        
    Returns:
        DetailedPrompt
    """
    generator = EnhancedPromptGenerator()
    
    return generator.generate_prompt_sync(
        task_description=plan.get('description', 'Automation task'),
        url=plan.get('url', ''),
        steps=plan.get('steps', []),
        headless=headless
    )
