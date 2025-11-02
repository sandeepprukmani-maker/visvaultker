"""
Website Learning Utilities
Intelligently learns from website interactions to improve future automations
"""
import json
import logging
import re
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.models import db, WebsiteKnowledgeBase

logger = logging.getLogger(__name__)


def extract_domain(url: str) -> str:
    """
    Extract domain from URL
    
    Args:
        url: Full URL
        
    Returns:
        Domain name (e.g., 'example.com')
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        domain = re.sub(r'^www\.', '', domain)
        return domain.lower()
    except Exception as e:
        logger.error(f"Failed to extract domain from {url}: {e}")
        return url.lower()


def get_website_knowledge(url: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve learned knowledge about a website
    
    Args:
        url: Website URL or domain
        
    Returns:
        Dictionary of learned knowledge or None if not found
    """
    try:
        domain = extract_domain(url)
        knowledge = WebsiteKnowledgeBase.query.filter_by(domain=domain).first()
        
        if knowledge:
            # Update last accessed time (don't increment visits here - done in learn_from_execution)
            knowledge.last_accessed = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"📚 Retrieved knowledge for {domain} (visited {knowledge.total_visits} times)")
            return knowledge.to_dict()
        
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve knowledge for {url}: {e}")
        db.session.rollback()
        return None


def learn_from_execution(url: str, instruction: str, steps: List[Dict], success: bool):
    """
    Learn from an automation execution and update knowledge base
    
    Args:
        url: Website URL that was automated
        instruction: The automation instruction
        steps: List of steps taken during automation
        success: Whether the automation succeeded
    """
    try:
        domain = extract_domain(url)
        
        # Get or create knowledge entry
        knowledge = WebsiteKnowledgeBase.query.filter_by(domain=domain).first()
        
        if not knowledge:
            knowledge = WebsiteKnowledgeBase(
                domain=domain,
                website_name=domain,
                common_elements='{}',
                navigation_patterns='{}',
                form_patterns='{}'
            )
            db.session.add(knowledge)
            logger.info(f"📝 Created new knowledge entry for {domain}")
        
        # Update visit count and last accessed time
        knowledge.total_visits += 1
        knowledge.last_accessed = datetime.utcnow()
        
        # Update success metrics
        if success:
            knowledge.successful_automations += 1
        else:
            knowledge.failed_automations += 1
        
        # Learn patterns from successful executions
        if success and steps:
            _learn_patterns_from_steps(knowledge, instruction, steps)
        
        knowledge.updated_at = datetime.utcnow()
        db.session.commit()
        
        success_rate = knowledge.successful_automations / max(knowledge.total_visits, 1) * 100
        logger.info(f"✅ Updated knowledge for {domain} (success rate: {success_rate:.1f}%)")
        
    except Exception as e:
        logger.error(f"Failed to learn from execution for {url}: {e}")
        db.session.rollback()


def _learn_patterns_from_steps(knowledge: WebsiteKnowledgeBase, instruction: str, steps: List[Dict]):
    """
    Extract patterns from successful automation steps
    
    Args:
        knowledge: Knowledge base entry to update
        instruction: Original instruction
        steps: Steps taken during automation
    """
    try:
        # Load existing patterns
        navigation_patterns = json.loads(knowledge.navigation_patterns or '{}')
        common_elements = json.loads(knowledge.common_elements or '{}')
        
        # Detect instruction type
        instruction_lower = instruction.lower()
        
        # Learn login patterns
        if any(keyword in instruction_lower for keyword in ['login', 'sign in', 'log in', 'authenticate']):
            navigation_patterns['login'] = {
                'description': 'How to log in',
                'steps': _simplify_steps(steps),
                'last_updated': datetime.utcnow().isoformat()
            }
            knowledge.authentication_method = 'username_password'
        
        # Learn search patterns
        elif any(keyword in instruction_lower for keyword in ['search', 'find', 'look for']):
            navigation_patterns['search'] = {
                'description': 'How to search',
                'steps': _simplify_steps(steps),
                'last_updated': datetime.utcnow().isoformat()
            }
        
        # Learn navigation patterns
        elif any(keyword in instruction_lower for keyword in ['navigate', 'go to', 'open', 'visit']):
            navigation_patterns['navigate'] = {
                'description': 'Navigation pattern',
                'steps': _simplify_steps(steps),
                'last_updated': datetime.utcnow().isoformat()
            }
        
        # Extract common element patterns from steps
        for step in steps:
            action = step.get('action', '')
            
            # Learn about buttons
            if 'click' in action.lower() and 'button' in action.lower():
                button_text = _extract_element_text(step)
                if button_text:
                    common_elements[f'button_{button_text.lower().replace(" ", "_")}'] = {
                        'type': 'button',
                        'text': button_text,
                        'action': 'click'
                    }
            
            # Learn about input fields
            elif 'fill' in action.lower() or 'type' in action.lower():
                field_type = _infer_field_type(step)
                if field_type:
                    common_elements[field_type] = {
                        'type': 'input',
                        'action': 'fill'
                    }
        
        # Save updated patterns
        knowledge.navigation_patterns = json.dumps(navigation_patterns, indent=2)
        knowledge.common_elements = json.dumps(common_elements, indent=2)
        
        logger.debug(f"📖 Learned {len(navigation_patterns)} navigation patterns and {len(common_elements)} common elements")
        
    except Exception as e:
        logger.error(f"Failed to learn patterns from steps: {e}")


def _simplify_steps(steps: List[Dict]) -> List[Dict]:
    """Simplify steps to essential actions for pattern matching"""
    simplified = []
    for step in steps:
        simplified.append({
            'action': step.get('action', ''),
            'description': step.get('description', step.get('action', ''))[:100]
        })
    return simplified


def _extract_element_text(step: Dict) -> Optional[str]:
    """Extract text from step description"""
    try:
        description = step.get('description', '') or step.get('action', '')
        # Extract text between quotes
        match = re.search(r"['\"]([^'\"]+)['\"]", description)
        if match:
            return match.group(1)
        
        # Extract button/link text
        match = re.search(r'(?:button|link|element).*?:\s*(\w+(?:\s+\w+)*)', description, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    except Exception:
        return None


def _infer_field_type(step: Dict) -> Optional[str]:
    """Infer the type of input field from step"""
    try:
        description = (step.get('description', '') or step.get('action', '')).lower()
        
        if any(keyword in description for keyword in ['email', 'e-mail']):
            return 'email_field'
        elif any(keyword in description for keyword in ['password', 'pass']):
            return 'password_field'
        elif any(keyword in description for keyword in ['username', 'user']):
            return 'username_field'
        elif any(keyword in description for keyword in ['search']):
            return 'search_field'
        
        return None
    except Exception:
        return None


def format_knowledge_for_prompt(url: str) -> str:
    """
    Format learned knowledge as context for LLM prompts
    
    Args:
        url: Website URL
        
    Returns:
        Formatted string with learned knowledge
    """
    knowledge = get_website_knowledge(url)
    
    if not knowledge:
        return ""
    
    context_parts = [f"\n🧠 LEARNED KNOWLEDGE ABOUT {knowledge['domain'].upper()}:"]
    context_parts.append(f"(Based on {knowledge['total_visits']} previous visits, {knowledge['successful_automations']} successful)")
    
    # Add navigation patterns (already parsed by to_dict())
    nav_patterns = knowledge.get('navigation_patterns', {})
    if nav_patterns and isinstance(nav_patterns, dict) and len(nav_patterns) > 0:
        context_parts.append("\nKnown Patterns:")
        for pattern_name, pattern_data in nav_patterns.items():
            if isinstance(pattern_data, dict):
                context_parts.append(f"  • {pattern_name}: {pattern_data.get('description', 'N/A')}")
    
    # Add common elements (already parsed by to_dict())
    common_elems = knowledge.get('common_elements', {})
    if common_elems and isinstance(common_elems, dict) and len(common_elems) > 0:
        context_parts.append("\nCommon Elements:")
        for elem_name, elem_data in common_elems.items():
            if isinstance(elem_data, dict):
                elem_type = elem_data.get('type', 'N/A')
                elem_text = elem_data.get('text', '')
                context_parts.append(f"  • {elem_name}: {elem_type} - {elem_text}")
    
    # Add authentication method
    if knowledge.get('authentication_method'):
        context_parts.append(f"\nAuth Method: {knowledge['authentication_method']}")
    
    # Add quirks/notes
    if knowledge.get('quirks'):
        context_parts.append(f"\n⚠️ Known Quirks: {knowledge['quirks']}")
    
    if knowledge.get('notes'):
        context_parts.append(f"\n📝 Notes: {knowledge['notes']}")
    
    context_parts.append("\nUse this knowledge to be more efficient and accurate!\n")
    
    return "\n".join(context_parts)
