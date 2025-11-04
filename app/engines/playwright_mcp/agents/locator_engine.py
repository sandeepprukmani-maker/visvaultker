"""
Strict-Mode Locator Engine
Multi-strategy locator generation with priority: data-testid > ARIA roles > unique attributes > text content > CSS
"""
import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LocatorStrategy:
    """Represents a locator strategy with priority"""
    priority: int
    strategy_type: str
    locator: str
    selector_type: str  # 'role', 'text', 'css', 'xpath', 'data-testid'
    is_unique: bool
    confidence: float


class StrictModeLocatorEngine:
    """
    Generates strict-mode locators with automatic duplicate handling
    Priority: data-testid > ARIA roles > unique attributes > text content > CSS with filters
    """
    
    PRIORITY_ORDER = {
        'data-testid': 1,
        'data-test': 1,
        'aria-label': 2,
        'role': 2,
        'id': 3,
        'name': 4,
        'placeholder': 5,
        'text': 6,
        'css': 7,
        'xpath': 8
    }
    
    def __init__(self, mcp_client=None):
        """
        Initialize locator engine
        
        Args:
            mcp_client: MCP client for live element validation
        """
        self.mcp_client = mcp_client
    
    def generate_locators(self, element_data: Dict) -> List[LocatorStrategy]:
        """
        Generate multiple locator strategies for an element, ordered by priority
        
        Args:
            element_data: Dictionary containing element attributes and properties
            
        Returns:
            List of LocatorStrategy objects, ordered by priority (highest first)
        """
        strategies = []
        
        # Strategy 1: data-testid or data-test attributes (highest priority)
        if 'data-testid' in element_data.get('attributes', {}):
            testid = element_data['attributes']['data-testid']
            strategies.append(LocatorStrategy(
                priority=self.PRIORITY_ORDER['data-testid'],
                strategy_type='data-testid',
                locator=f"page.get_by_test_id('{testid}')",
                selector_type='data-testid',
                is_unique=True,
                confidence=0.95
            ))
        
        if 'data-test' in element_data.get('attributes', {}):
            testid = element_data['attributes']['data-test']
            strategies.append(LocatorStrategy(
                priority=self.PRIORITY_ORDER['data-test'],
                strategy_type='data-test',
                locator=f"page.locator('[data-test=\"{testid}\"]')",
                selector_type='css',
                is_unique=True,
                confidence=0.95
            ))
        
        # Strategy 2: ARIA role + accessible name
        role = element_data.get('role')
        aria_label = element_data.get('attributes', {}).get('aria-label')
        
        if role:
            if aria_label:
                strategies.append(LocatorStrategy(
                    priority=self.PRIORITY_ORDER['role'],
                    strategy_type='role-with-name',
                    locator=f"page.get_by_role('{role}', name='{self._escape_quotes(aria_label)}')",
                    selector_type='role',
                    is_unique=True,
                    confidence=0.90
                ))
            else:
                strategies.append(LocatorStrategy(
                    priority=self.PRIORITY_ORDER['role'],
                    strategy_type='role-only',
                    locator=f"page.get_by_role('{role}')",
                    selector_type='role',
                    is_unique=False,
                    confidence=0.70
                ))
        
        # Strategy 3: Unique ID attribute
        if 'id' in element_data.get('attributes', {}):
            elem_id = element_data['attributes']['id']
            strategies.append(LocatorStrategy(
                priority=self.PRIORITY_ORDER['id'],
                strategy_type='id',
                locator=f"page.locator('#{elem_id}')",
                selector_type='css',
                is_unique=True,
                confidence=0.85
            ))
        
        # Strategy 4: Name attribute (for form inputs)
        if 'name' in element_data.get('attributes', {}):
            name = element_data['attributes']['name']
            strategies.append(LocatorStrategy(
                priority=self.PRIORITY_ORDER['name'],
                strategy_type='name',
                locator=f"page.locator('[name=\"{name}\"]')",
                selector_type='css',
                is_unique=False,
                confidence=0.75
            ))
        
        # Strategy 5: Placeholder (for inputs)
        if 'placeholder' in element_data.get('attributes', {}):
            placeholder = element_data['attributes']['placeholder']
            strategies.append(LocatorStrategy(
                priority=self.PRIORITY_ORDER['placeholder'],
                strategy_type='placeholder',
                locator=f"page.get_by_placeholder('{self._escape_quotes(placeholder)}')",
                selector_type='text',
                is_unique=False,
                confidence=0.70
            ))
        
        # Strategy 6: Text content
        text_content = element_data.get('text', '').strip()
        if text_content and len(text_content) < 100:
            strategies.append(LocatorStrategy(
                priority=self.PRIORITY_ORDER['text'],
                strategy_type='text',
                locator=f"page.get_by_text('{self._escape_quotes(text_content)}')",
                selector_type='text',
                is_unique=False,
                confidence=0.65
            ))
        
        # Strategy 7: CSS selector with tag and classes
        css_selector = self._build_css_selector(element_data)
        if css_selector:
            strategies.append(LocatorStrategy(
                priority=self.PRIORITY_ORDER['css'],
                strategy_type='css',
                locator=f"page.locator('{css_selector}')",
                selector_type='css',
                is_unique=False,
                confidence=0.60
            ))
        
        # Sort by priority (lower number = higher priority)
        strategies.sort(key=lambda s: (s.priority, -s.confidence))
        
        return strategies
    
    def generate_best_locator(self, element_data: Dict, duplicate_count: Optional[int] = None) -> str:
        """
        Generate the best locator for an element, handling duplicates automatically
        
        Args:
            element_data: Dictionary containing element attributes and properties
            duplicate_count: If element has duplicates, which index to target (0-based)
            
        Returns:
            Python Playwright locator code as string
        """
        strategies = self.generate_locators(element_data)
        
        if not strategies:
            # Fallback to XPath
            return "page.locator('//body')"
        
        # Get the best strategy (first in sorted list)
        best_strategy = strategies[0]
        locator = best_strategy.locator
        
        # Handle duplicates
        if duplicate_count is not None and duplicate_count > 0:
            if not best_strategy.is_unique:
                # Use .nth() for non-unique locators
                locator = f"{locator}.nth({duplicate_count})"
            else:
                logger.warning(f"Element marked as unique but has duplicates, using .nth({duplicate_count})")
                locator = f"{locator}.nth({duplicate_count})"
        
        # Add .first() for non-unique locators without specific index
        elif not best_strategy.is_unique and duplicate_count is None:
            locator = f"{locator}.first()"
        
        return locator
    
    def generate_with_filter(self, element_data: Dict, filter_options: Dict) -> str:
        """
        Generate locator with additional filter options
        
        Args:
            element_data: Dictionary containing element attributes
            filter_options: Filter criteria (has_text, has_not_text, has, has_not)
            
        Returns:
            Filtered locator code
        """
        base_locator = self.generate_best_locator(element_data)
        
        filters = []
        if 'has_text' in filter_options:
            filters.append(f"has_text='{self._escape_quotes(filter_options['has_text'])}'")
        if 'has_not_text' in filter_options:
            filters.append(f"has_not_text='{self._escape_quotes(filter_options['has_not_text'])}'")
        
        if filters:
            filter_str = ', '.join(filters)
            return f"{base_locator}.filter({filter_str})"
        
        return base_locator
    
    def validate_locator(self, locator: str, page_snapshot: Dict) -> Tuple[bool, int]:
        """
        Validate if locator matches exactly one element or multiple
        
        Args:
            locator: Playwright locator code
            page_snapshot: Current page DOM snapshot
            
        Returns:
            Tuple of (is_unique, element_count)
        """
        # This would integrate with MCP client to count matching elements
        # For now, return placeholder
        return (True, 1)
    
    def _build_css_selector(self, element_data: Dict) -> str:
        """Build a CSS selector from element data"""
        tag = element_data.get('tag', 'div')
        classes = element_data.get('classes', [])
        
        if classes:
            class_str = '.' + '.'.join(classes[:3])  # Limit to first 3 classes
            return f"{tag}{class_str}"
        
        return tag
    
    def _escape_quotes(self, text: str) -> str:
        """Escape quotes in text for Python string literals"""
        return text.replace("'", "\\'").replace('"', '\\"')
    
    def chain_locators(self, parent_locator: str, child_locator: str) -> str:
        """
        Chain locators for nested elements
        
        Args:
            parent_locator: Parent element locator
            child_locator: Child element locator relative to parent
            
        Returns:
            Chained locator code
        """
        # Extract the selector from child_locator
        # Example: page.get_by_role('button') -> get_by_role('button')
        if child_locator.startswith('page.'):
            child_method = child_locator[5:]  # Remove 'page.'
            return f"{parent_locator}.{child_method}"
        
        return f"{parent_locator}.locator('{child_locator}')"
