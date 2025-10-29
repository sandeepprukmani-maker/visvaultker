"""
Intelligent Validation Service
Performs web scraping and validation to ensure accurate element locators and actions
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Page, ElementHandle
import re

logger = logging.getLogger(__name__)


@dataclass
class ElementValidation:
    """Result of element validation"""
    exists: bool
    locator: str
    locator_strategy: str
    confidence: float
    element_info: Dict[str, Any]
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    

@dataclass
class PageValidation:
    """Result of page validation"""
    url: str
    title: str
    is_accessible: bool
    elements_found: List[ElementValidation]
    page_structure: Dict[str, Any]
    validation_time: float
    

class IntelligentValidator:
    """
    Validates web pages and elements through intelligent scraping
    
    Features:
    - Scrapes pages to validate element existence
    - Detects accurate locators with confidence scoring
    - Provides alternative locators for robustness
    - Analyzes page structure for better automation
    - Suggests improvements for element targeting
    """
    
    def __init__(self):
        """Initialize the validator"""
        self.browser = None
        self.context = None
        self.page = None
        
    async def validate_task(
        self,
        url: str,
        steps: List[Dict[str, Any]],
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a complete automation task by scraping and verifying elements
        
        Args:
            url: Target URL to validate
            steps: List of steps with actions and targets
            headless: Run browser in headless mode
            
        Returns:
            Validation result with detailed element information
        """
        logger.info(f"🔍 Starting intelligent validation for {url}")
        
        try:
            # Initialize browser
            await self._init_browser(headless)
            
            # Navigate and validate page
            page_validation = await self._validate_page(url)
            
            if not page_validation.is_accessible:
                return {
                    'success': False,
                    'error': f'Page {url} is not accessible',
                    'page_validation': page_validation
                }
            
            # Validate each step's elements
            validated_steps = []
            for step in steps:
                validated_step = await self._validate_step(step, self.page)
                validated_steps.append(validated_step)
            
            logger.info(f"✅ Validation complete: {len(validated_steps)} steps validated")
            
            return {
                'success': True,
                'url': url,
                'page_validation': page_validation,
                'validated_steps': validated_steps,
                'total_elements': len([s for s in validated_steps if s.get('element_valid')])
            }
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            await self._cleanup()
    
    async def _init_browser(self, headless: bool = True):
        """Initialize browser for validation"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def _cleanup(self):
        """Cleanup browser resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def _validate_page(self, url: str) -> PageValidation:
        """Validate page accessibility and structure"""
        import time
        start_time = time.time()
        
        try:
            # Navigate to page
            response = await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Get page info
            title = await self.page.title()
            
            # Analyze page structure
            structure = await self._analyze_page_structure()
            
            elapsed = time.time() - start_time
            
            return PageValidation(
                url=url,
                title=title,
                is_accessible=response.ok if response else False,
                elements_found=[],
                page_structure=structure,
                validation_time=elapsed
            )
            
        except Exception as e:
            logger.error(f"Page validation failed: {e}")
            return PageValidation(
                url=url,
                title='',
                is_accessible=False,
                elements_found=[],
                page_structure={},
                validation_time=time.time() - start_time
            )
    
    async def _analyze_page_structure(self) -> Dict[str, Any]:
        """Analyze page structure for better automation"""
        try:
            # Count interactive elements
            buttons = await self.page.locator('button').count()
            links = await self.page.locator('a').count()
            inputs = await self.page.locator('input').count()
            selects = await self.page.locator('select').count()
            
            # Get forms
            forms = await self.page.locator('form').count()
            
            # Check for common frameworks
            frameworks = await self._detect_frameworks()
            
            return {
                'interactive_elements': {
                    'buttons': buttons,
                    'links': links,
                    'inputs': inputs,
                    'selects': selects,
                    'forms': forms
                },
                'frameworks': frameworks,
                'has_spa': await self._detect_spa()
            }
            
        except Exception as e:
            logger.warning(f"Page structure analysis failed: {e}")
            return {}
    
    async def _detect_frameworks(self) -> List[str]:
        """Detect frontend frameworks"""
        frameworks = []
        
        try:
            # Check for React
            react_check = await self.page.evaluate(
                "() => !!window.React || !!document.querySelector('[data-reactroot]')"
            )
            if react_check:
                frameworks.append('React')
            
            # Check for Vue
            vue_check = await self.page.evaluate(
                "() => !!window.Vue || !!document.querySelector('[data-v-]')"
            )
            if vue_check:
                frameworks.append('Vue')
            
            # Check for Angular
            angular_check = await self.page.evaluate(
                "() => !!window.angular || !!document.querySelector('[ng-app], [ng-version]')"
            )
            if angular_check:
                frameworks.append('Angular')
                
        except Exception as e:
            logger.debug(f"Framework detection error: {e}")
        
        return frameworks
    
    async def _detect_spa(self) -> bool:
        """Detect if page is a Single Page Application"""
        try:
            # Check for common SPA indicators
            has_client_routing = await self.page.evaluate(
                "() => !!window.history.pushState && window.location.hash.length > 1"
            )
            return has_client_routing
        except:
            return False
    
    async def _validate_step(
        self,
        step: Dict[str, Any],
        page: Page
    ) -> Dict[str, Any]:
        """
        Validate a single step by finding and verifying the target element
        
        Args:
            step: Step dict with action, target, value, etc.
            page: Playwright page object
            
        Returns:
            Validated step with element information
        """
        action = step.get('action', '').lower()
        target = step.get('target', '')
        
        # Skip validation for navigation and wait actions
        if action in ['navigate', 'wait', 'screenshot']:
            return {
                **step,
                'element_valid': True,
                'validation': ElementValidation(
                    exists=True,
                    locator='N/A',
                    locator_strategy='N/A',
                    confidence=1.0,
                    element_info={}
                )
            }
        
        # Find and validate element
        validation = await self._find_and_validate_element(page, target, action)
        
        return {
            **step,
            'element_valid': validation.exists,
            'validation': validation,
            'suggested_locator': validation.locator if validation.exists else None
        }
    
    async def _find_and_validate_element(
        self,
        page: Page,
        target: str,
        action: str
    ) -> ElementValidation:
        """
        Find an element using multiple strategies and validate it
        
        Args:
            page: Playwright page
            target: Element description
            action: Action type (click, fill, etc.)
            
        Returns:
            ElementValidation result
        """
        # Try multiple locator strategies in order of preference
        strategies = [
            ('role', self._try_role_locator),
            ('text', self._try_text_locator),
            ('label', self._try_label_locator),
            ('placeholder', self._try_placeholder_locator),
            ('css', self._try_css_locator)
        ]
        
        alternatives = []
        
        for strategy_name, strategy_func in strategies:
            try:
                element, locator = await strategy_func(page, target, action)
                
                if element:
                    # Get element information
                    element_info = await self._extract_element_info(element)
                    
                    # Calculate confidence
                    confidence = self._calculate_strategy_confidence(
                        strategy_name, element_info, target
                    )
                    
                    # This is our primary match
                    if confidence > 0.7:
                        return ElementValidation(
                            exists=True,
                            locator=locator,
                            locator_strategy=strategy_name,
                            confidence=confidence,
                            element_info=element_info,
                            alternatives=alternatives
                        )
                    else:
                        # Add as alternative
                        alternatives.append({
                            'locator': locator,
                            'strategy': strategy_name,
                            'confidence': confidence
                        })
                        
            except Exception as e:
                logger.debug(f"Strategy {strategy_name} failed: {e}")
                continue
        
        # No good match found
        return ElementValidation(
            exists=False,
            locator='',
            locator_strategy='none',
            confidence=0.0,
            element_info={},
            alternatives=alternatives,
            warnings=[f'Could not find element: {target}']
        )
    
    async def _try_role_locator(
        self,
        page: Page,
        target: str,
        action: str
    ) -> Tuple[Optional[ElementHandle], str]:
        """Try to find element using role-based locator"""
        role = self._infer_role(target, action)
        name = self._extract_name_from_target(target)
        
        if name:
            locator = page.get_by_role(role, name=name)
            locator_str = f'page.get_by_role("{role}", name="{name}")'
        else:
            locator = page.get_by_role(role).first
            locator_str = f'page.get_by_role("{role}").first'
        
        try:
            await locator.wait_for(state='attached', timeout=2000)
            element = await locator.element_handle(timeout=1000)
            return element, locator_str
        except:
            return None, locator_str
    
    async def _try_text_locator(
        self,
        page: Page,
        target: str,
        action: str
    ) -> Tuple[Optional[ElementHandle], str]:
        """Try to find element using text content"""
        text = self._extract_name_from_target(target)
        
        if not text:
            return None, ''
        
        locator = page.get_by_text(text, exact=False).first
        locator_str = f'page.get_by_text("{text}", exact=False).first'
        
        try:
            await locator.wait_for(state='attached', timeout=2000)
            element = await locator.element_handle(timeout=1000)
            return element, locator_str
        except:
            return None, locator_str
    
    async def _try_label_locator(
        self,
        page: Page,
        target: str,
        action: str
    ) -> Tuple[Optional[ElementHandle], str]:
        """Try to find element using label"""
        label = self._extract_name_from_target(target)
        
        if not label or action not in ['fill', 'select']:
            return None, ''
        
        locator = page.get_by_label(label, exact=False)
        locator_str = f'page.get_by_label("{label}", exact=False)'
        
        try:
            await locator.wait_for(state='attached', timeout=2000)
            element = await locator.element_handle(timeout=1000)
            return element, locator_str
        except:
            return None, locator_str
    
    async def _try_placeholder_locator(
        self,
        page: Page,
        target: str,
        action: str
    ) -> Tuple[Optional[ElementHandle], str]:
        """Try to find element using placeholder"""
        placeholder = self._extract_name_from_target(target)
        
        if not placeholder or action != 'fill':
            return None, ''
        
        locator = page.get_by_placeholder(placeholder, exact=False)
        locator_str = f'page.get_by_placeholder("{placeholder}", exact=False)'
        
        try:
            await locator.wait_for(state='attached', timeout=2000)
            element = await locator.element_handle(timeout=1000)
            return element, locator_str
        except:
            return None, locator_str
    
    async def _try_css_locator(
        self,
        page: Page,
        target: str,
        action: str
    ) -> Tuple[Optional[ElementHandle], str]:
        """Try to find element using CSS selector (last resort)"""
        # Generate simple CSS based on action
        if action == 'click':
            selector = 'button, a, [role="button"]'
        elif action == 'fill':
            selector = 'input[type="text"], input[type="email"], input[type="password"], textarea'
        elif action == 'select':
            selector = 'select'
        else:
            selector = '*'
        
        text = self._extract_name_from_target(target)
        if text:
            selector = f'{selector}:has-text("{text[:30]}")'
        
        locator = page.locator(selector).first
        locator_str = f'page.locator("{selector}").first'
        
        try:
            await locator.wait_for(state='attached', timeout=2000)
            element = await locator.element_handle(timeout=1000)
            return element, locator_str
        except:
            return None, locator_str
    
    async def _extract_element_info(self, element: ElementHandle) -> Dict[str, Any]:
        """Extract detailed information about an element"""
        try:
            info = await element.evaluate('''(el) => ({
                tag: el.tagName.toLowerCase(),
                text: el.textContent?.trim() || '',
                value: el.value || '',
                type: el.type || '',
                name: el.name || '',
                id: el.id || '',
                className: el.className || '',
                placeholder: el.placeholder || '',
                ariaLabel: el.getAttribute('aria-label') || '',
                role: el.getAttribute('role') || '',
                disabled: el.disabled || false,
                visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                href: el.href || ''
            })''')
            return info
        except Exception as e:
            logger.warning(f"Failed to extract element info: {e}")
            return {}
    
    def _calculate_strategy_confidence(
        self,
        strategy: str,
        element_info: Dict[str, Any],
        target: str
    ) -> float:
        """Calculate confidence score for a strategy match"""
        base_scores = {
            'role': 0.90,
            'label': 0.85,
            'placeholder': 0.80,
            'text': 0.75,
            'css': 0.50
        }
        
        score = base_scores.get(strategy, 0.50)
        
        # Bonus if element is visible
        if element_info.get('visible'):
            score += 0.05
        
        # Bonus if text matches well
        elem_text = element_info.get('text', '').lower()
        target_lower = target.lower()
        if elem_text and target_lower in elem_text:
            score += 0.05
        
        return min(1.0, score)
    
    def _infer_role(self, target: str, action: str) -> str:
        """Infer ARIA role from target and action"""
        target_lower = target.lower()
        
        if any(kw in target_lower for kw in ['button', 'btn', 'submit']):
            return 'button'
        elif any(kw in target_lower for kw in ['link', 'anchor']):
            return 'link'
        elif any(kw in target_lower for kw in ['input', 'field', 'textbox']):
            return 'textbox'
        elif action == 'click':
            return 'button'
        elif action == 'fill':
            return 'textbox'
        else:
            return 'button'
    
    def _extract_name_from_target(self, target: str) -> str:
        """Extract meaningful name from target description"""
        # Remove noise words
        noise = ['the', 'a', 'an', 'button', 'link', 'field', 'input', 
                 'box', 'element', 'form', 'select', 'dropdown']
        
        words = target.split()
        filtered = [w for w in words if w.lower() not in noise]
        
        return ' '.join(filtered).strip() if filtered else target.strip()


def validate_task_sync(url: str, steps: List[Dict[str, Any]], headless: bool = True) -> Dict[str, Any]:
    """
    Synchronous wrapper for validate_task
    
    Args:
        url: Target URL
        steps: List of automation steps
        headless: Run headless
        
    Returns:
        Validation result
    """
    validator = IntelligentValidator()
    return asyncio.run(validator.validate_task(url, steps, headless))
