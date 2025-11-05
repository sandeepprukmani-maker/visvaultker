"""
Site Crawler Service
Intelligently crawls websites using browser-use AI to learn structure and elements
"""
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from urllib.parse import urlparse, urljoin
from pathlib import Path

from app.models import db, SiteCrawl, CrawlPage, PageElement, SiteKnowledge, CredentialVault
from app.engines.browser_use import create_engine

logger = logging.getLogger(__name__)


class SiteCrawlerService:
    """
    Intelligent site crawler using browser-use AI
    
    Features:
    - Deep learning of site structure
    - Element discovery and classification
    - Form and interaction detection
    - Knowledge compilation
    - Credential-based authentication
    """
    
    def __init__(self):
        """Initialize Site Crawler Service"""
        self.current_crawl_id = None
        self.visited_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        logger.info("🕷️ Site Crawler Service initialized")
    
    async def start_crawl(self, crawl_id: int) -> Dict[str, Any]:
        """
        Start crawling a site
        
        Args:
            crawl_id: ID of the SiteCrawl record
            
        Returns:
            Dictionary with crawl results
        """
        try:
            crawl = SiteCrawl.query.get(crawl_id)
            if not crawl:
                return {"success": False, "error": "Crawl not found"}
            
            self.current_crawl_id = crawl_id
            self.visited_urls = set()
            self.discovered_urls = set()
            
            # Update status
            crawl.status = "running"
            crawl.progress = 0
            db.session.commit()
            
            logger.info(f"🕷️ Starting crawl #{crawl_id}: {crawl.name}")
            logger.info(f"📍 Start URL: {crawl.start_url}")
            logger.info(f"⚙️ Max pages: {crawl.max_pages}, Max depth: {crawl.max_depth}")
            
            # Get credentials if needed
            username = None
            password = None
            if crawl.credential_id:
                credential = CredentialVault.query.get(crawl.credential_id)
                if credential:
                    username = credential.username
                    password = credential.get_credential()
                    logger.info(f"🔐 Using credentials: {username}")
            
            # Create browser-use engine in headless mode for production
            engine = create_engine(headless=True)
            
            # Start crawling
            await self._crawl_recursive(
                engine=engine,
                crawl=crawl,
                url=crawl.start_url,
                depth=0,
                parent_url=None,
                username=username,
                password=password
            )
            
            # Compile knowledge
            await self._compile_knowledge(crawl)
            
            # Update final status
            crawl.status = "completed"
            crawl.progress = 100
            crawl.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Crawl #{crawl_id} completed: {crawl.pages_crawled} pages")
            
            return {
                "success": True,
                "crawl_id": crawl_id,
                "pages_crawled": crawl.pages_crawled,
                "knowledge_entries": len(crawl.knowledge_entries)
            }
            
        except Exception as e:
            logger.error(f"❌ Crawl #{crawl_id} failed: {str(e)}", exc_info=True)
            
            # Update error status
            crawl = SiteCrawl.query.get(crawl_id)
            if crawl:
                crawl.status = "failed"
                crawl.error_message = str(e)
                db.session.commit()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _crawl_recursive(
        self,
        engine,
        crawl: SiteCrawl,
        url: str,
        depth: int,
        parent_url: Optional[str],
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """Recursively crawl pages"""
        
        # Check limits
        if crawl.pages_crawled >= crawl.max_pages:
            logger.info(f"⚠️ Max pages limit reached: {crawl.max_pages}")
            return
        
        if depth > crawl.max_depth:
            logger.debug(f"⚠️ Max depth reached: {crawl.max_depth}")
            return
        
        # Check if already visited
        if url in self.visited_urls:
            return
        
        # Check domain restriction
        if crawl.same_domain_only:
            start_domain = urlparse(crawl.start_url).netloc
            url_domain = urlparse(url).netloc
            if start_domain != url_domain:
                logger.debug(f"⚠️ Skipping external domain: {url}")
                return
        
        self.visited_urls.add(url)
        
        logger.info(f"📄 Crawling [{depth}]: {url}")
        
        try:
            # Create page record
            page = CrawlPage(
                crawl_id=crawl.id,
                url=url,
                depth=depth,
                parent_url=parent_url,
                status="crawling"
            )
            db.session.add(page)
            db.session.commit()
            
            # Use browser-use AI to analyze the page
            instruction = self._build_crawl_instruction(url, username, password, depth == 0)
            
            result = await engine.execute_instruction(instruction)
            
            if result.get("success"):
                # Extract page info from result
                page_data = self._extract_page_data(result)
                
                # Update page
                page.title = page_data.get("title")
                page.page_type = page_data.get("page_type")
                page.status = "completed"
                page.page_metadata = json.dumps(page_data.get("metadata", {}))
                
                # Save elements
                for element_data in page_data.get("elements", []):
                    element = PageElement(
                        page_id=page.id,
                        element_type=element_data.get("type"),
                        selector=element_data.get("selector"),
                        xpath=element_data.get("xpath"),
                        text_content=element_data.get("text"),
                        attributes=json.dumps(element_data.get("attributes", {})),
                        is_interactive=element_data.get("is_interactive", False),
                        is_form_field=element_data.get("is_form_field", False),
                        is_link=element_data.get("is_link", False),
                        position=json.dumps(element_data.get("position", {})),
                        description=element_data.get("description")
                    )
                    db.session.add(element)
                
                db.session.commit()
                
                # Update progress
                crawl.pages_crawled += 1
                crawl.progress = min(100, int((crawl.pages_crawled / crawl.max_pages) * 100))
                db.session.commit()
                
                # Discover new URLs from page
                discovered_links = page_data.get("links", [])
                for link in discovered_links:
                    absolute_url = urljoin(url, link)
                    if absolute_url not in self.visited_urls and absolute_url not in self.discovered_urls:
                        self.discovered_urls.add(absolute_url)
                
                # Recursively crawl discovered links (limited by max_pages)
                for link in list(self.discovered_urls)[:5]:  # Limit concurrent crawls
                    if crawl.pages_crawled < crawl.max_pages:
                        self.discovered_urls.discard(link)
                        await self._crawl_recursive(
                            engine, crawl, link, depth + 1, url, username, password
                        )
                
            else:
                page.status = "failed"
                page.error_message = result.get("error", "Unknown error")
                db.session.commit()
                
        except Exception as e:
            logger.error(f"❌ Error crawling {url}: {str(e)}", exc_info=True)
            page.status = "failed"
            page.error_message = str(e)
            db.session.commit()
    
    def _build_crawl_instruction(
        self,
        url: str,
        username: Optional[str],
        password: Optional[str],
        is_first_page: bool
    ) -> str:
        """Build AI instruction for crawling a page"""
        
        instruction = f"""
Navigate to {url} and perform deep analysis of the page.

TASKS:
1. If login is required and credentials are provided, log in first using:
   - Username: {username if username else 'NOT PROVIDED'}
   - Password: {password if password else 'NOT PROVIDED'}

2. Analyze and document ALL elements on the page:
   - Interactive elements (buttons, links, inputs)
   - Form fields (text inputs, checkboxes, selects, etc.)
   - Navigation elements (menus, breadcrumbs, tabs)
   - Content sections and their structure
   - For each element, note: selector, type, text content, and purpose

3. Identify the page type (login page, dashboard, form, listing page, etc.)

4. Extract ALL clickable links on the page

5. Take a screenshot of the page

Provide detailed findings in your response.""".strip()
        
        return instruction
    
    def _extract_page_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from browser-use result"""
        
        # This is a simplified extraction - in production, use more sophisticated parsing
        page_data = {
            "title": "Untitled Page",
            "page_type": "general",
            "elements": [],
            "links": [],
            "metadata": {}
        }
        
        # Extract from result (browser-use provides this in various formats)
        final_response = result.get("final_response", "")
        steps = result.get("steps", [])
        
        # Parse the AI response to extract structure information
        # This would use NLP/parsing in production
        
        # For now, return basic structure
        return page_data
    
    async def _compile_knowledge(self, crawl: SiteCrawl):
        """Compile learned knowledge from crawled pages"""
        
        logger.info(f"🧠 Compiling knowledge for crawl #{crawl.id}")
        
        try:
            # Aggregate all pages and elements
            pages = CrawlPage.query.filter_by(crawl_id=crawl.id).all()
            
            # Identify patterns and create knowledge entries
            
            # 1. Site structure knowledge
            structure_knowledge = SiteKnowledge(
                crawl_id=crawl.id,
                knowledge_type="site_structure",
                category="navigation",
                title="Site Structure",
                description="Overall site navigation and structure",
                content=json.dumps({
                    "total_pages": len(pages),
                    "max_depth": max([p.depth for p in pages]) if pages else 0,
                    "page_types": list(set([p.page_type for p in pages if p.page_type]))
                }),
                confidence_score=1.0
            )
            db.session.add(structure_knowledge)
            
            # 2. Form fields knowledge
            all_form_fields = []
            for page in pages:
                form_fields = [e for e in page.elements if e.is_form_field]
                if form_fields:
                    for field in form_fields:
                        all_form_fields.append({
                            "page_url": page.url,
                            "type": field.element_type,
                            "selector": field.selector,
                            "description": field.description or field.text_content
                        })
            
            if all_form_fields:
                forms_knowledge = SiteKnowledge(
                    crawl_id=crawl.id,
                    knowledge_type="form_fields",
                    category="interactions",
                    title="Form Fields",
                    description="All form fields discovered across the site",
                    content=json.dumps(all_form_fields),
                    confidence_score=0.9
                )
                db.session.add(forms_knowledge)
            
            # 3. Interactive elements knowledge
            all_buttons = []
            for page in pages:
                buttons = [e for e in page.elements if e.is_interactive and e.element_type in ['button', 'a']]
                if buttons:
                    for btn in buttons:
                        all_buttons.append({
                            "page_url": page.url,
                            "text": btn.text_content,
                            "selector": btn.selector,
                            "type": btn.element_type
                        })
            
            if all_buttons:
                buttons_knowledge = SiteKnowledge(
                    crawl_id=crawl.id,
                    knowledge_type="interactive_elements",
                    category="interactions",
                    title="Buttons and Links",
                    description="All interactive buttons and links",
                    content=json.dumps(all_buttons),
                    confidence_score=0.95
                )
                db.session.add(buttons_knowledge)
            
            db.session.commit()
            
            logger.info(f"✅ Knowledge compilation complete: {len(crawl.knowledge_entries)} entries")
            
        except Exception as e:
            logger.error(f"❌ Knowledge compilation failed: {str(e)}", exc_info=True)
            db.session.rollback()
    
    def get_knowledge_summary(self, crawl_id: int) -> Dict[str, Any]:
        """Get a formatted knowledge summary for a crawl"""
        
        crawl = SiteCrawl.query.get(crawl_id)
        if not crawl:
            return {"success": False, "error": "Crawl not found"}
        
        knowledge_text = f"""
# Site Knowledge for: {crawl.name}
URL: {crawl.start_url}
Crawled: {crawl.pages_crawled} pages
Status: {crawl.status}

## Learned Knowledge:
"""
        
        for entry in crawl.knowledge_entries:
            knowledge_text += f"\n### {entry.title}\n"
            knowledge_text += f"Type: {entry.knowledge_type}\n"
            knowledge_text += f"Category: {entry.category}\n"
            if entry.description:
                knowledge_text += f"Description: {entry.description}\n"
            knowledge_text += f"\nDetails:\n```json\n{entry.content}\n```\n"
        
        return {
            "success": True,
            "crawl_id": crawl_id,
            "knowledge_summary": knowledge_text,
            "knowledge_count": len(crawl.knowledge_entries)
        }
