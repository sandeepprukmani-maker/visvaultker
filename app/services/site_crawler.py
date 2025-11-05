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
                
                # Discover new URLs from page (excluding pagination)
                discovered_links = page_data.get("links", [])
                pagination_links = page_data.get("pagination_links", [])
                
                # Log pagination info but don't crawl them
                if pagination_links:
                    logger.info(f"📄 Found {len(pagination_links)} pagination links (skipping to avoid duplicates)")
                
                # Only add non-pagination links to the crawl queue
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
Navigate to {url} and perform comprehensive page analysis.

TASKS:
1. If login is required and credentials are provided, log in first using:
   - Username: {username if username else 'NOT PROVIDED'}
   - Password: {password if password else 'NOT PROVIDED'}

2. After the page loads completely, execute this JavaScript to extract ALL page elements and return the JSON result:
```javascript
(function() {{
    const elements = [];
    const links = new Set();
    
    // Get page title
    const pageTitle = document.title;
    
    // Extract all interactive elements
    const interactiveSelectors = 'a, button, input, select, textarea, [role="button"], [onclick], [role="link"]';
    document.querySelectorAll(interactiveSelectors).forEach((el, index) => {{
        const rect = el.getBoundingClientRect();
        const isVisible = rect.width > 0 && rect.height > 0;
        
        if (isVisible) {{
            // Generate unique selector
            let selector = el.id ? `#${{el.id}}` : '';
            if (!selector && el.className) {{
                const classes = Array.from(el.classList).filter(c => c && !c.startsWith('_')).slice(0, 2);
                if (classes.length > 0) {{
                    selector = el.tagName.toLowerCase() + '.' + classes.join('.');
                }}
            }}
            if (!selector && el.parentElement) {{
                // Calculate actual nth-of-type position among siblings
                const siblings = Array.from(el.parentElement.children).filter(
                    sibling => sibling.tagName === el.tagName
                );
                const nthIndex = siblings.indexOf(el) + 1;
                selector = el.tagName.toLowerCase() + `:nth-of-type(${{nthIndex}})`;
            }}
            if (!selector) {{
                selector = el.tagName.toLowerCase();
            }}
            
            // Check if this is a pagination link (before creating elementInfo)
            let isPaginationLink = false;
            if (el.tagName.toLowerCase() === 'a' && el.href) {{
                try {{
                    const linkUrl = new URL(el.href, window.location.href);
                    if (linkUrl.protocol === 'http:' || linkUrl.protocol === 'https:') {{
                        const linkText = (el.textContent || '').trim().toLowerCase();
                        isPaginationLink = 
                            // URL patterns
                            linkUrl.href.match(/[?&](page|p|pg|pagenum|pagenumber)=/i) ||
                            linkUrl.pathname.match(/\/page\/\d+/i) ||
                            // Text patterns
                            ['next', 'previous', 'prev', '›', '»', '‹', '«'].includes(linkText) ||
                            /^(page\s*)?\d+$/.test(linkText) || // "1", "2", "Page 1"
                            // Class/ID patterns
                            (el.className && el.className.match(/pag(e|ination)/i)) ||
                            (el.id && el.id.match(/pag(e|ination)/i));
                        
                        links.add(linkUrl.href);
                    }}
                }} catch (e) {{}}
            }}
            
            const elementInfo = {{
                type: el.tagName.toLowerCase(),
                selector: selector,
                xpath: getXPath(el),
                text: (el.textContent || el.value || el.placeholder || '').trim().substring(0, 200),
                attributes: {{
                    id: el.id || '',
                    className: el.className || '',
                    name: el.name || '',
                    type: el.type || '',
                    href: el.href || '',
                    role: el.getAttribute('role') || '',
                    ariaLabel: el.getAttribute('aria-label') || ''
                }},
                is_interactive: true,
                is_form_field: ['input', 'select', 'textarea'].includes(el.tagName.toLowerCase()),
                is_link: el.tagName.toLowerCase() === 'a' && el.href,
                is_pagination: isPaginationLink,
                position: {{
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                }},
                parent_selector: el.parentElement ? (el.parentElement.id ? `#${{el.parentElement.id}}` : el.parentElement.tagName.toLowerCase()) : ''
            }};
            
            elements.push(elementInfo);
        }}
    }});
    
    // Helper function to get XPath
    function getXPath(element) {{
        if (element.id) return `//*[@id="${{element.id}}"]`;
        if (element === document.body) return '/html/body';
        
        let ix = 0;
        const siblings = element.parentNode?.childNodes || [];
        for (let i = 0; i < siblings.length; i++) {{
            const sibling = siblings[i];
            if (sibling === element) {{
                return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
            }}
            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {{
                ix++;
            }}
        }}
        return '';
    }}
    
    // Detect page type
    let pageType = 'general';
    if (document.querySelector('form[action*="login"]') || document.querySelector('input[type="password"]')) {{
        pageType = 'login';
    }} else if (document.querySelector('form')) {{
        pageType = 'form';
    }} else if (document.querySelector('[role="navigation"]') || document.querySelector('nav')) {{
        pageType = 'navigation';
    }} else if (document.querySelectorAll('article, .post, .product').length > 3) {{
        pageType = 'listing';
    }}
    
    return JSON.stringify({{
        title: pageTitle,
        pageType: pageType,
        elements: elements,
        links: Array.from(links),
        elementCount: elements.length,
        linkCount: links.size
    }}, null, 2);
}})();
```

3. Return the complete JSON output from the JavaScript execution above.

4. Take a screenshot of the page for visual reference.""".strip()
        
        return instruction
    
    def _extract_page_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from browser-use result"""
        
        # Default structure
        page_data = {
            "title": "Untitled Page",
            "page_type": "general",
            "elements": [],
            "links": [],
            "pagination_links": [],
            "metadata": {}
        }
        
        try:
            # Try to extract JSON from the final result or steps
            final_result = result.get("final_result", "")
            steps = result.get("steps", [])
            
            # Look for JSON in final_result or in step results
            json_data = None
            
            # Check final_result first
            if final_result:
                json_data = self._parse_json_from_text(str(final_result))
            
            # If not found, check steps
            if not json_data:
                for step in reversed(steps):  # Check from last step backwards
                    step_result = step.get("result", {})
                    if isinstance(step_result, dict):
                        state = step_result.get("state", "")
                        json_data = self._parse_json_from_text(str(state))
                        if json_data:
                            break
            
            # If we found JSON data, use it
            if json_data and isinstance(json_data, dict):
                page_data["title"] = json_data.get("title", "Untitled Page")
                page_data["page_type"] = json_data.get("pageType", "general")
                page_data["elements"] = json_data.get("elements", [])
                all_links = json_data.get("links", [])
                
                # Separate regular links from pagination links using element flags
                pagination_links = []
                regular_links = []
                
                # Build a set of pagination links from elements marked as pagination
                pagination_hrefs = set()
                for element in page_data["elements"]:
                    if element.get("is_pagination") and element.get("is_link"):
                        href = element.get("attributes", {}).get("href", "")
                        if href:
                            pagination_hrefs.add(href)
                
                # Categorize links
                for link in all_links:
                    if link in pagination_hrefs:
                        pagination_links.append(link)
                    else:
                        # Additional URL-based detection as backup
                        link_lower = link.lower()
                        if any(pattern in link_lower for pattern in [
                            'page=', 'p=', '/page/', 'pagination', 
                            '&pg=', 'pagenum', 'pagenumber'
                        ]):
                            pagination_links.append(link)
                        else:
                            regular_links.append(link)
                
                page_data["links"] = regular_links
                page_data["pagination_links"] = pagination_links
                page_data["metadata"] = {
                    "element_count": json_data.get("elementCount", 0),
                    "link_count": json_data.get("linkCount", 0),
                    "pagination_count": len(pagination_links)
                }
                
                logger.info(f"✅ Extracted {len(page_data['elements'])} elements, "
                          f"{len(regular_links)} links, {len(pagination_links)} pagination links")
            else:
                logger.warning("⚠️ Could not parse JSON from browser-use response, using empty data")
                
        except Exception as e:
            logger.error(f"❌ Error extracting page data: {str(e)}", exc_info=True)
        
        return page_data
    
    def _parse_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from text that may contain other content"""
        if not text:
            return None
        
        try:
            # Try direct JSON parse first
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON in text using regex
        import re
        
        # Look for JSON object patterns
        json_patterns = [
            r'\{[\s\S]*"title"[\s\S]*\}',  # Object with "title" key
            r'\{[\s\S]*"elements"[\s\S]*\}',  # Object with "elements" key
            r'\{[\s\S]*"pageType"[\s\S]*\}',  # Object with "pageType" key
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Try to find the complete JSON object
                    # Count braces to find matching pairs
                    brace_count = 0
                    json_start = match.find('{')
                    if json_start == -1:
                        continue
                    
                    for i in range(json_start, len(match)):
                        if match[i] == '{':
                            brace_count += 1
                        elif match[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                potential_json = match[json_start:i+1]
                                return json.loads(potential_json)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return None
    
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
