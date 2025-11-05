"""
Knowledge Retriever Service
Retrieves and formats site knowledge for use in automation tasks
"""
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from app.models import SiteCrawl, SiteKnowledge, CrawlPage, PageElement

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """
    Retrieves site knowledge and formats it for automation
    
    Features:
    - URL matching for relevant knowledge
    - Knowledge formatting for AI prompts
    - Context-aware retrieval
    - Confidence-based filtering
    """
    
    def __init__(self):
        """Initialize Knowledge Retriever"""
        logger.info("🧠 Knowledge Retriever initialized")
    
    def find_relevant_crawl(self, url: str) -> Optional[SiteCrawl]:
        """
        Find the most relevant crawl for a given URL
        
        Args:
            url: Target URL
            
        Returns:
            SiteCrawl object or None
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Find crawls that match this domain
        all_crawls = SiteCrawl.query.filter_by(status='completed').all()
        
        for crawl in all_crawls:
            crawl_domain = urlparse(crawl.start_url).netloc
            if crawl_domain == domain:
                logger.info(f"✅ Found relevant crawl: {crawl.name} (ID: {crawl.id})")
                return crawl
        
        logger.warning(f"⚠️ No crawl found for domain: {domain}")
        return None
    
    def get_knowledge_for_url(self, url: str, min_confidence: float = 0.5) -> Dict[str, Any]:
        """
        Get all relevant knowledge for a specific URL
        
        Args:
            url: Target URL
            min_confidence: Minimum confidence score for knowledge
            
        Returns:
            Dictionary with knowledge data
        """
        crawl = self.find_relevant_crawl(url)
        
        if not crawl:
            return {
                "success": False,
                "error": "No knowledge available for this site",
                "has_knowledge": False
            }
        
        # Get all knowledge entries
        knowledge_entries = SiteKnowledge.query.filter(
            SiteKnowledge.crawl_id == crawl.id,
            SiteKnowledge.confidence_score >= min_confidence
        ).all()
        
        # Find the most relevant page
        relevant_page = self._find_matching_page(crawl, url)
        
        result = {
            "success": True,
            "has_knowledge": True,
            "crawl_id": crawl.id,
            "crawl_name": crawl.name,
            "knowledge_entries": [entry.to_dict() for entry in knowledge_entries],
            "relevant_page": relevant_page.to_dict(include_elements=True) if relevant_page else None,
            "site_structure": self._get_site_structure(crawl)
        }
        
        return result
    
    def format_knowledge_for_prompt(self, url: str, task_description: str = "") -> str:
        """
        Format knowledge as a context string for AI prompts
        
        Args:
            url: Target URL
            task_description: Description of the task to perform
            
        Returns:
            Formatted knowledge string
        """
        knowledge = self.get_knowledge_for_url(url)
        
        if not knowledge.get("has_knowledge"):
            return ""
        
        context = f"""
# SITE KNOWLEDGE CONTEXT

The following information was learned by previously crawling this website:

## Site: {knowledge.get('crawl_name')}
Crawled Pages: {knowledge['site_structure'].get('total_pages', 0)}

"""
        
        # Add relevant page information
        if knowledge.get("relevant_page"):
            page = knowledge["relevant_page"]
            context += f"""
## Current Page Information
URL: {page['url']}
Title: {page.get('title', 'N/A')}
Type: {page.get('page_type', 'general')}

### Elements on This Page:
"""
            elements = page.get("elements", [])
            if elements:
                # Group by type
                form_fields = [e for e in elements if e.get('is_form_field')]
                buttons = [e for e in elements if e.get('is_interactive') and not e.get('is_form_field')]
                links = [e for e in elements if e.get('is_link')]
                
                if form_fields:
                    context += "\n**Form Fields:**\n"
                    for field in form_fields[:20]:  # Limit to 20
                        context += f"- {field.get('element_type')}: {field.get('text_content') or field.get('selector')} (selector: {field.get('selector')})\n"
                
                if buttons:
                    context += "\n**Buttons/Interactive Elements:**\n"
                    for btn in buttons[:15]:  # Limit to 15
                        context += f"- {btn.get('text_content')} (selector: {btn.get('selector')})\n"
                
                if links:
                    context += "\n**Links:**\n"
                    for link in links[:15]:  # Limit to 15
                        context += f"- {link.get('text_content')} (selector: {btn.get('selector')})\n"
        
        # Add knowledge entries
        knowledge_entries = knowledge.get("knowledge_entries", [])
        if knowledge_entries:
            context += "\n## Learned Knowledge:\n"
            
            for entry in knowledge_entries:
                context += f"\n### {entry['title']}\n"
                context += f"Category: {entry.get('category', 'N/A')}\n"
                
                # Parse content
                try:
                    content_data = json.loads(entry['content'])
                    if isinstance(content_data, dict):
                        for key, value in content_data.items():
                            if isinstance(value, list) and len(value) > 10:
                                context += f"{key}: {len(value)} items available\n"
                            else:
                                context += f"{key}: {value}\n"
                    elif isinstance(content_data, list):
                        context += f"Items: {len(content_data)} available\n"
                        if content_data and len(content_data) > 0:
                            context += f"Sample: {content_data[0]}\n"
                except:
                    context += f"Content: {entry['content'][:200]}...\n"
        
        context += f"""

---
INSTRUCTIONS:
Use the above site knowledge to help you accomplish this task: {task_description}

The knowledge includes:
- Known elements and their selectors
- Form fields and interactive buttons
- Site structure and navigation
- Previously successful interaction patterns

Leverage this knowledge to navigate and interact with the site more accurately.
"""
        
        return context.strip()
    
    def _find_matching_page(self, crawl: SiteCrawl, url: str) -> Optional[CrawlPage]:
        """Find the most matching page for a URL"""
        
        # Try exact match first
        page = CrawlPage.query.filter_by(crawl_id=crawl.id, url=url).first()
        if page:
            return page
        
        # Try partial match (same path)
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        pages = CrawlPage.query.filter_by(crawl_id=crawl.id).all()
        for page in pages:
            if urlparse(page.url).path == path:
                return page
        
        # Return the start page as fallback
        return CrawlPage.query.filter_by(crawl_id=crawl.id, depth=0).first()
    
    def _get_site_structure(self, crawl: SiteCrawl) -> Dict[str, Any]:
        """Get site structure summary"""
        
        pages = CrawlPage.query.filter_by(crawl_id=crawl.id, status='completed').all()
        
        return {
            "total_pages": len(pages),
            "max_depth": max([p.depth for p in pages]) if pages else 0,
            "page_types": list(set([p.page_type for p in pages if p.page_type])),
            "domains": list(set([urlparse(p.url).netloc for p in pages]))
        }
    
    def enhance_instruction_with_knowledge(self, instruction: str, url: Optional[str] = None) -> str:
        """
        Enhance an automation instruction with relevant site knowledge
        
        Args:
            instruction: Original user instruction
            url: Optional URL to get knowledge for (extracted from instruction if not provided)
            
        Returns:
            Enhanced instruction with knowledge context
        """
        
        # Extract URL from instruction if not provided
        if not url:
            # Simple URL extraction (can be improved with regex)
            words = instruction.split()
            for word in words:
                if word.startswith('http://') or word.startswith('https://'):
                    url = word.strip('.,;')
                    break
        
        if not url:
            logger.debug("No URL found in instruction, skipping knowledge enhancement")
            return instruction
        
        # Get knowledge context
        knowledge_context = self.format_knowledge_for_prompt(url, instruction)
        
        if not knowledge_context:
            return instruction
        
        # Enhance the instruction
        enhanced = f"""
{knowledge_context}

---
USER TASK:
{instruction}
""".strip()
        
        logger.info(f"✅ Enhanced instruction with site knowledge ({len(knowledge_context)} chars)")
        
        return enhanced
