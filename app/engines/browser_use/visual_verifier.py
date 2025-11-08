"""
Visual + Textual Goal Checking
Uses vision models to verify presence of UI elements or texts on screen
"""
import base64
import logging
from typing import Dict, Any
from PIL import Image
import io

logger = logging.getLogger(__name__)


class VisualVerifier:
    """
    Uses vision models to verify presence of UI elements or texts on screen.
    Note: Requires a vision-capable LLM model
    """

    def __init__(self, llm):
        """
        Initialize visual verifier
        
        Args:
            llm: Language model (should support vision for image analysis)
        """
        self.llm = llm
        self.verification_history = []
        logger.info("🖼️  Visual Verifier initialized")

    async def validate_goal(self, page, goal_text: str) -> Dict[str, Any]:
        """
        Validate whether the goal has been achieved using visual and textual analysis
        
        Args:
            page: Playwright page object
            goal_text: Goal description to validate
            
        Returns:
            Dictionary with success status and reasoning
        """
        try:
            logger.info(f"🖼️  Validating goal: {goal_text[:100]}")
            
            # Take screenshot
            screenshot_bytes = await page.screenshot()
            image_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            
            # Also get page text for context
            page_text = await page.evaluate("() => document.body.innerText")
            page_text_snippet = page_text[:2000] if len(page_text) > 2000 else page_text
            
            # Create verification prompt
            prompt = f"""
Analyze this screenshot and page content to determine if the following goal has been achieved:
Goal: "{goal_text}"

Page text content (first 2000 chars):
{page_text_snippet}

Based on the screenshot and page text:
1. Does the screen indicate success toward the goal?
2. Are there any visual or textual indicators of completion?
3. Are there any error messages or failure indicators?

Answer "yes" or "no" with clear reasoning.
Format your response as:
SUCCESS: yes/no
REASONING: [your explanation]
"""
            
            # For vision models, we would pass the image
            # For text-only models, we rely on page text
            try:
                # Try vision-capable invocation first
                response = await self.llm.ainvoke(prompt, images=[image_b64])
            except (TypeError, AttributeError):
                # Fallback to text-only if vision not supported
                logger.warning("Vision model not supported, using text-only validation")
                response = await self.llm.ainvoke(prompt)
            
            response_text = str(response).lower()
            
            # Parse response
            success = "success: yes" in response_text or (
                "yes" in response_text and "no" not in response_text[:50]
            )
            
            # Extract reasoning
            reasoning = str(response).strip()
            if "reasoning:" in response_text:
                reasoning = str(response).split("REASONING:", 1)[1].strip() if "REASONING:" in str(response) else reasoning
            
            result = {
                "success": success,
                "reasoning": reasoning,
                "goal": goal_text,
                "has_screenshot": True
            }
            
            # Record verification
            self.verification_history.append(result)
            
            status_emoji = "✅" if success else "❌"
            logger.info(f"{status_emoji} Verification result: {success}")
            logger.debug(f"Reasoning: {reasoning[:200]}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Visual verification failed: {e}")
            return {
                "success": False,
                "reasoning": f"Verification error: {str(e)}",
                "goal": goal_text,
                "error": str(e),
                "has_screenshot": False
            }

    async def validate_element_present(self, page, element_description: str) -> Dict[str, Any]:
        """
        Validate whether a specific element is present on the page
        
        Args:
            page: Playwright page object
            element_description: Description of the element to find
            
        Returns:
            Dictionary with presence status and reasoning
        """
        return await self.validate_goal(
            page, 
            f"Verify that the following element is present: {element_description}"
        )

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        if not self.verification_history:
            return {
                "total_verifications": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0
            }
        
        successful = sum(1 for v in self.verification_history if v.get("success", False))
        total = len(self.verification_history)
        
        return {
            "total_verifications": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total if total > 0 else 0.0
        }

    def reset_stats(self):
        """Reset verification history"""
        self.verification_history.clear()
        logger.info("🔄 Verification history reset")
