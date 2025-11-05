"""
Intelligent Locator Extraction System
Generates high-quality Playwright locators with smart prioritization and confidence scoring
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LocatorStrategy(Enum):
    """Locator strategies in priority order"""
    ROLE = "role"  # Highest priority - semantic, accessible
    LABEL = "label"  # Form elements with labels
    PLACEHOLDER = "placeholder"  # Input placeholders
    TEST_ID = "testid"  # Explicit test identifiers
    TEXT = "text"  # Visible text content
    ALT_TEXT = "alt"  # Image alt text
    TITLE = "title"  # Title attribute
    CSS = "css"  # CSS selectors (lowest priority)


@dataclass
class LocatorResult:
    """Result of locator extraction"""
    strategy: LocatorStrategy
    locator: str
    confidence: float  # 0.0 to 1.0
    is_unique: bool
    alternatives: List[Tuple[LocatorStrategy, str, float]]  # Alternative locators
    warnings: List[str]  # Potential issues


class IntelligentLocatorExtractor:
    """
    Extracts intelligent locators from DOM elements with quality scoring
    
    Features:
    - Smart prioritization (role > label > testid > text > css)
    - Avoids brittle selectors (nth-child, complex paths)
    - Provides confidence scores for each locator
    - Suggests alternative locators
    - Warns about potential stability issues
    """
    
    # Confidence scores for each strategy
    CONFIDENCE_SCORES = {
        LocatorStrategy.ROLE: 0.95,
        LocatorStrategy.LABEL: 0.90,
        LocatorStrategy.PLACEHOLDER: 0.85,
        LocatorStrategy.TEST_ID: 0.88,
        LocatorStrategy.TEXT: 0.75,
        LocatorStrategy.ALT_TEXT: 0.80,
        LocatorStrategy.TITLE: 0.70,
        LocatorStrategy.CSS: 0.50
    }
    
    # Brittle selector patterns to avoid
    BRITTLE_PATTERNS = [
        r':nth-child\(',
        r':nth-of-type\(',
        r'>\s*div\s*>\s*div',  # Deep div nesting
        r'\[class\*="[^"]*random[^"]*"\]',  # Randomized classes
        r'\[class\*="[^"]*hash[^"]*"\]',
    ]
    
    # Semantic HTML roles
    ARIA_ROLES = {
        'button', 'link', 'checkbox', 'radio', 'textbox', 'searchbox',
        'combobox', 'listbox', 'option', 'menu', 'menuitem', 'tab',
        'tabpanel', 'dialog', 'alert', 'navigation', 'main', 'heading',
        'img', 'list', 'listitem', 'row', 'cell', 'table', 'banner',
        'contentinfo', 'complementary', 'form', 'search', 'region'
    }
    
    def __init__(self):
        """Initialize the locator extractor"""
        self.locator_cache = {}
    
    def extract_locator(
        self,
        element_info: Dict,
        action_type: Optional[str] = None
    ) -> LocatorResult:
        """
        Extract the best locator for an element
        
        Args:
            element_info: Dictionary containing element properties
                {
                    'tag': 'button',
                    'text': 'Click me',
                    'role': 'button',
                    'aria_label': 'Submit form',
                    'placeholder': 'Enter text',
                    'test_id': 'submit-btn',
                    'id': 'btn-123',
                    'class': 'btn btn-primary',
                    'name': 'submit',
                    'type': 'submit',
                    'alt': 'Logo',
                    'title': 'Submit the form'
                }
            action_type: Type of action (click, fill, etc.)
        
        Returns:
            LocatorResult with best locator and alternatives
        """
        all_locators = []
        warnings = []
        
        # Try each strategy in priority order
        locator_functions = [
            self._extract_role_locator,
            self._extract_label_locator,
            self._extract_placeholder_locator,
            self._extract_testid_locator,
            self._extract_text_locator,
            self._extract_alt_locator,
            self._extract_title_locator,
            self._extract_css_locator
        ]
        
        for func in locator_functions:
            result = func(element_info)
            if result:
                strategy, locator = result
                confidence = self._calculate_confidence(strategy, locator, element_info)
                all_locators.append((strategy, locator, confidence))
        
        if not all_locators:
            # Fallback to basic CSS
            tag = element_info.get('tag', 'div')
            return LocatorResult(
                strategy=LocatorStrategy.CSS,
                locator=f"page.locator('{tag}')",
                confidence=0.30,
                is_unique=False,
                alternatives=[],
                warnings=["No semantic locators found, using generic tag selector"]
            )
        
        # Best locator is first one (highest priority with highest confidence)
        best = all_locators[0]
        alternatives = all_locators[1:] if len(all_locators) > 1 else []
        
        # Check for brittle patterns
        brittle_warnings = self._check_brittle_patterns(best[1])
        warnings.extend(brittle_warnings)
        
        return LocatorResult(
            strategy=best[0],
            locator=best[1],
            confidence=best[2],
            is_unique=True,  # Assume unique for now (would need DOM context to verify)
            alternatives=alternatives,
            warnings=warnings
        )
    
    def _extract_role_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract role-based locator (highest priority)"""
        role = element_info.get('role') or self._infer_role(element_info)
        
        if not role or role not in self.ARIA_ROLES:
            return None
        
        # Check for accessible name (aria-label, label, text)
        name = (
            element_info.get('aria_label') or
            element_info.get('label') or
            element_info.get('text', '').strip()
        )
        
        if name:
            # Clean and escape the name
            name = self._clean_text(name)
            if role == 'button':
                return (LocatorStrategy.ROLE, f"page.getByRole('button', {{ name: '{name}' }})")
            elif role == 'link':
                return (LocatorStrategy.ROLE, f"page.getByRole('link', {{ name: '{name}' }})")
            elif role == 'textbox':
                return (LocatorStrategy.ROLE, f"page.getByRole('textbox', {{ name: '{name}' }})")
            elif role == 'checkbox':
                return (LocatorStrategy.ROLE, f"page.getByRole('checkbox', {{ name: '{name}' }})")
            elif role == 'heading':
                return (LocatorStrategy.ROLE, f"page.getByRole('heading', {{ name: '{name}' }})")
            else:
                return (LocatorStrategy.ROLE, f"page.getByRole('{role}', {{ name: '{name}' }})")
        else:
            # Role without name (less specific)
            return (LocatorStrategy.ROLE, f"page.getByRole('{role}')")
    
    def _extract_label_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract label-based locator (good for forms)"""
        label = element_info.get('label') or element_info.get('aria_label')
        
        if label:
            label = self._clean_text(label)
            return (LocatorStrategy.LABEL, f"page.getByLabel('{label}')")
        
        return None
    
    def _extract_placeholder_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract placeholder-based locator (for inputs)"""
        placeholder = element_info.get('placeholder')
        
        if placeholder:
            placeholder = self._clean_text(placeholder)
            return (LocatorStrategy.PLACEHOLDER, f"page.getByPlaceholder('{placeholder}')")
        
        return None
    
    def _extract_testid_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract test ID locator (explicit test identifiers)"""
        test_id = (
            element_info.get('data-testid') or
            element_info.get('data-test-id') or
            element_info.get('data-test') or
            element_info.get('test_id')
        )
        
        if test_id:
            return (LocatorStrategy.TEST_ID, f"page.getByTestId('{test_id}')")
        
        return None
    
    def _extract_text_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract text-based locator"""
        text = element_info.get('text', '').strip()
        
        if text and len(text) > 0 and len(text) < 100:  # Reasonable text length
            text = self._clean_text(text)
            # Check if it's exact match or partial
            if len(text) < 50:
                return (LocatorStrategy.TEXT, f"page.getByText('{text}')")
            else:
                # Use partial match for long text
                partial = text[:30]
                return (LocatorStrategy.TEXT, f"page.getByText('{partial}', {{ exact: false }})")
        
        return None
    
    def _extract_alt_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract alt text locator (for images)"""
        alt = element_info.get('alt')
        
        if alt:
            alt = self._clean_text(alt)
            return (LocatorStrategy.ALT_TEXT, f"page.getByAltText('{alt}')")
        
        return None
    
    def _extract_title_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract title-based locator"""
        title = element_info.get('title')
        
        if title:
            title = self._clean_text(title)
            return (LocatorStrategy.TITLE, f"page.getByTitle('{title}')")
        
        return None
    
    def _extract_css_locator(self, element_info: Dict) -> Optional[Tuple[LocatorStrategy, str]]:
        """Extract CSS locator (last resort)"""
        # Priority: ID > stable class > tag + attributes
        
        elem_id = element_info.get('id')
        if elem_id and not self._looks_dynamic(elem_id):
            return (LocatorStrategy.CSS, f"page.locator('#{elem_id}')")
        
        # Use stable classes (avoid hashed/random ones)
        classes = element_info.get('class', '').split()
        stable_classes = [c for c in classes if not self._looks_dynamic(c)]
        
        if stable_classes:
            class_selector = '.' + '.'.join(stable_classes[:2])  # Max 2 classes
            tag = element_info.get('tag', '')
            if tag:
                return (LocatorStrategy.CSS, f"page.locator('{tag}{class_selector}')")
            else:
                return (LocatorStrategy.CSS, f"page.locator('{class_selector}')")
        
        # Fallback to tag + type/name
        tag = element_info.get('tag', 'div')
        elem_type = element_info.get('type')
        name = element_info.get('name')
        
        if elem_type:
            return (LocatorStrategy.CSS, f"page.locator('{tag}[type=\"{elem_type}\"]')")
        elif name:
            return (LocatorStrategy.CSS, f"page.locator('{tag}[name=\"{name}\"]')")
        else:
            return (LocatorStrategy.CSS, f"page.locator('{tag}')")
    
    def _infer_role(self, element_info: Dict) -> Optional[str]:
        """Infer ARIA role from element properties"""
        tag = element_info.get('tag', '').lower()
        elem_type = element_info.get('type', '').lower()
        
        # Map HTML elements to ARIA roles
        role_map = {
            'button': 'button',
            'a': 'link',
            'input': {
                'text': 'textbox',
                'email': 'textbox',
                'password': 'textbox',
                'search': 'searchbox',
                'tel': 'textbox',
                'url': 'textbox',
                'number': 'textbox',
                'checkbox': 'checkbox',
                'radio': 'radio',
                'submit': 'button',
                'button': 'button'
            },
            'textarea': 'textbox',
            'select': 'combobox',
            'img': 'img',
            'nav': 'navigation',
            'main': 'main',
            'header': 'banner',
            'footer': 'contentinfo',
            'aside': 'complementary',
            'form': 'form',
            'h1': 'heading',
            'h2': 'heading',
            'h3': 'heading',
            'h4': 'heading',
            'h5': 'heading',
            'h6': 'heading',
            'ul': 'list',
            'ol': 'list',
            'li': 'listitem',
            'table': 'table',
            'tr': 'row',
            'td': 'cell',
            'th': 'cell'
        }
        
        if tag in role_map:
            role_value = role_map[tag]
            if isinstance(role_value, dict):
                return role_value.get(elem_type, 'textbox' if tag == 'input' else None)
            return role_value
        
        return None
    
    def _calculate_confidence(
        self,
        strategy: LocatorStrategy,
        locator: str,
        element_info: Dict
    ) -> float:
        """Calculate confidence score for a locator"""
        base_confidence = self.CONFIDENCE_SCORES[strategy]
        
        # Adjust based on locator characteristics
        adjustments = 0.0
        
        # Bonus for specific attributes
        if 'name:' in locator or "name: '" in locator:
            adjustments += 0.05  # Has accessible name
        
        # Penalty for generic selectors
        if locator.count('div') > 1:
            adjustments -= 0.10  # Multiple divs
        
        # Penalty for complex selectors
        if locator.count('>') > 2:
            adjustments -= 0.15  # Deep nesting
        
        # Bonus for test IDs
        if 'getByTestId' in locator:
            adjustments += 0.10  # Explicit test identifier
        
        # Check for brittle patterns
        for pattern in self.BRITTLE_PATTERNS:
            if re.search(pattern, locator):
                adjustments -= 0.20
                break
        
        return max(0.0, min(1.0, base_confidence + adjustments))
    
    def _check_brittle_patterns(self, locator: str) -> List[str]:
        """Check for brittle selector patterns"""
        warnings = []
        
        for pattern in self.BRITTLE_PATTERNS:
            if re.search(pattern, locator):
                warnings.append(f"Brittle pattern detected: {pattern}")
        
        if locator.count('>') > 3:
            warnings.append("Deep selector nesting may be fragile")
        
        if ':nth-child(' in locator or ':nth-of-type(' in locator:
            warnings.append("Position-based selector may break if DOM changes")
        
        return warnings
    
    def _looks_dynamic(self, value: str) -> bool:
        """Check if a class or ID looks dynamically generated"""
        # Patterns that indicate dynamic values
        dynamic_patterns = [
            r'[a-f0-9]{8,}',  # Long hex strings
            r'_[0-9a-z]{6,}$',  # Trailing hash
            r'^[a-z]{1,2}[0-9]+$',  # Short prefix + numbers
            r'random|hash|uuid|guid',
        ]
        
        for pattern in dynamic_patterns:
            if re.search(pattern, value.lower()):
                return True
        
        return False
    
    def _clean_text(self, text: str) -> str:
        """Clean and escape text for use in selectors"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Escape single quotes
        text = text.replace("'", "\\'")
        # Limit length
        if len(text) > 100:
            text = text[:97] + '...'
        return text
    
    def get_quality_indicator(self, confidence: float) -> Dict[str, str]:
        """
        Get visual quality indicator for UI display
        
        Returns:
            {
                'level': 'excellent' | 'good' | 'fair' | 'poor',
                'color': 'green' | 'yellow' | 'orange' | 'red',
                'emoji': '🟢' | '🟡' | '🟠' | '🔴'
            }
        """
        if confidence >= 0.85:
            return {'level': 'excellent', 'color': 'green', 'emoji': '🟢'}
        elif confidence >= 0.70:
            return {'level': 'good', 'color': 'yellow', 'emoji': '🟡'}
        elif confidence >= 0.50:
            return {'level': 'fair', 'color': 'orange', 'emoji': '🟠'}
        else:
            return {'level': 'poor', 'color': 'red', 'emoji': '🔴'}


def extract_locator_from_action(action_data: Dict) -> LocatorResult:
    """
    Convenience function to extract locator from action data
    
    Args:
        action_data: Action data with element information
    
    Returns:
        LocatorResult
    """
    extractor = IntelligentLocatorExtractor()
    element_info = action_data.get('element', {})
    action_type = action_data.get('action_type', None)
    
    return extractor.extract_locator(element_info, action_type)
