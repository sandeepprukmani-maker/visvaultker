"""
Selector Validator for Playwright MCP Code Generator
Validates and scores selectors for stability and CI/CD compatibility

Rejects brittle patterns:
- nth-child() selectors
- XPath with numeric indices
- Hashed/dynamic CSS classes
- ID selectors with timestamps or UUIDs
"""

import re
from typing import Dict, Tuple, Optional
from enum import Enum


class SelectorConfidence(Enum):
    """Confidence levels for selector stability"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECTED = "rejected"


class SelectorValidator:
    """Validates selectors for stability and best practices"""
    
    BRITTLE_PATTERNS = [
        (r'nth-child\(', "nth-child is brittle and order-dependent"),
        (r'nth-of-type\(', "nth-of-type is brittle and order-dependent"),
        (r':nth-\w+\(', "nth-based selectors are fragile"),
        (r'\[\d+\]', "XPath numeric indices break with DOM changes"),
        (r'//\w+\[\d+\]', "XPath with numeric indices is unstable"),
        (r'\b[a-f0-9]{6,}\b', "Hashed classnames change with builds"),
        (r'css-[a-z0-9]+', "CSS-in-JS hashed classes are unstable"),
        (r'\w+-\d{13,}', "Timestamp-based identifiers are dynamic"),
        (r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', "UUID selectors are unreliable"),
    ]
    
    SEMANTIC_PATTERNS = [
        (r'get_by_test_id', SelectorConfidence.HIGH),
        (r'get_by_role.*name=', SelectorConfidence.HIGH),
        (r'get_by_label', SelectorConfidence.HIGH),
        (r'get_by_placeholder', SelectorConfidence.HIGH),
        (r'get_by_text', SelectorConfidence.MEDIUM),
        (r'get_by_role', SelectorConfidence.MEDIUM),
        (r'data-testid', SelectorConfidence.HIGH),
        (r'aria-label=', SelectorConfidence.HIGH),
        (r'role=', SelectorConfidence.MEDIUM),
    ]
    
    @classmethod
    def validate_selector(cls, selector: str) -> Tuple[SelectorConfidence, Optional[str]]:
        """
        Validate a selector and return confidence score with reasoning
        
        Args:
            selector: The selector string to validate
            
        Returns:
            Tuple of (confidence_level, reason)
        """
        if not selector or not isinstance(selector, str):
            return SelectorConfidence.REJECTED, "Empty or invalid selector"
        
        selector_lower = selector.lower()
        
        for pattern, reason in cls.BRITTLE_PATTERNS:
            if re.search(pattern, selector_lower, re.IGNORECASE):
                return SelectorConfidence.REJECTED, reason
        
        for pattern, confidence in cls.SEMANTIC_PATTERNS:
            if re.search(pattern, selector_lower, re.IGNORECASE):
                return confidence, f"Uses {pattern.replace('.*', '')} (stable)"
        
        if selector.startswith('#') and re.search(r'[a-zA-Z]', selector):
            return SelectorConfidence.MEDIUM, "ID selector (stable if ID is static)"
        
        if 'button' in selector_lower or 'input' in selector_lower:
            return SelectorConfidence.LOW, "Generic tag selector (may be ambiguous)"
        
        return SelectorConfidence.LOW, "CSS selector without semantic attributes"
    
    @classmethod
    def is_acceptable(cls, selector: str) -> bool:
        """Check if selector is acceptable for CI/CD use"""
        confidence, _ = cls.validate_selector(selector)
        return confidence != SelectorConfidence.REJECTED
    
    @classmethod
    def score_locator_code(cls, locator_code: str) -> Tuple[SelectorConfidence, Optional[str]]:
        """
        Score a complete Playwright locator code snippet
        
        Args:
            locator_code: Full Playwright locator like 'page.get_by_role("button", name="Submit")'
            
        Returns:
            Tuple of (confidence_level, reason)
        """
        if not locator_code:
            return SelectorConfidence.REJECTED, "No locator code provided"
        
        if 'get_by_test_id' in locator_code:
            return SelectorConfidence.HIGH, "data-testid is the most stable selector"
        
        if 'get_by_role' in locator_code and 'name=' in locator_code:
            return SelectorConfidence.HIGH, "Role with accessible name is very stable"
        
        if 'get_by_label' in locator_code:
            return SelectorConfidence.HIGH, "Label-based selector is stable"
        
        if 'get_by_placeholder' in locator_code:
            return SelectorConfidence.HIGH, "Placeholder is a stable attribute"
        
        if 'get_by_role' in locator_code:
            return SelectorConfidence.MEDIUM, "Role without name is moderately stable"
        
        if 'get_by_text' in locator_code:
            return SelectorConfidence.MEDIUM, "Text-based selectors can break if content changes"
        
        if '.locator(' in locator_code:
            selector_match = re.search(r'\.locator\(["\']([^"\']+)["\']', locator_code)
            if selector_match:
                selector = selector_match.group(1)
                return cls.validate_selector(selector)
        
        return SelectorConfidence.LOW, "Unknown locator type"
    
    @classmethod
    def get_improvement_suggestion(cls, current_selector: str, element_info: Dict) -> Optional[str]:
        """
        Suggest improvements for a selector based on available element information
        
        Args:
            current_selector: Current selector being used
            element_info: Dict with element attributes (role, aria-label, data-testid, etc.)
            
        Returns:
            Suggestion string or None
        """
        suggestions = []
        
        if element_info.get('data_testid'):
            suggestions.append(f"Add data-testid='{element_info['data_testid']}' for best stability")
        
        if element_info.get('role') and element_info.get('name'):
            suggestions.append(f"Use getByRole('{element_info['role']}', name='{element_info['name']}')")
        
        if element_info.get('aria_label'):
            suggestions.append(f"Use getByLabel('{element_info['aria_label']}')")
        
        if suggestions:
            return "Consider: " + "; ".join(suggestions)
        
        return None


def calculate_selector_confidence(
    role: Optional[str],
    name: Optional[str],
    aria_label: Optional[str],
    placeholder: Optional[str],
    test_id: Optional[str],
    text: Optional[str],
    selector: Optional[str]
) -> Tuple[SelectorConfidence, str]:
    """
    Calculate overall confidence based on available element attributes
    
    Returns:
        Tuple of (confidence_level, explanation)
    """
    if test_id:
        return SelectorConfidence.HIGH, "Has data-testid attribute (best for automation)"
    
    if role and name:
        return SelectorConfidence.HIGH, f"Has role='{role}' with accessible name"
    
    if aria_label:
        return SelectorConfidence.HIGH, "Has aria-label attribute"
    
    if placeholder:
        return SelectorConfidence.HIGH, "Has placeholder attribute"
    
    if role:
        return SelectorConfidence.MEDIUM, "Has role but no accessible name"
    
    if text and len(text) < 50:
        return SelectorConfidence.MEDIUM, "Uses visible text (may change)"
    
    if selector:
        confidence, reason = SelectorValidator.validate_selector(selector)
        return confidence, reason or "Using fallback CSS selector"
    
    return SelectorConfidence.LOW, "No stable attributes available"
