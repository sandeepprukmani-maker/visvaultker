import hashlib
import json
import os
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page
from datetime import datetime
import asyncio

class WebCrawler:
    def __init__(self, screenshots_path: str = "./data/screenshots"):
        self.screenshots_path = screenshots_path
        os.makedirs(screenshots_path, exist_ok=True)
    
    async def extract_dom_structure(self, page: Page, url: str) -> Dict:
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        body_html = await page.content()
        
        structural_dom = await page.evaluate('''() => {
            function getStructure(element) {
                if (element.nodeType !== 1) return null;
                
                const tag = element.tagName.toLowerCase();
                const id = element.id || '';
                const classes = Array.from(element.classList).join(' ');
                const role = element.getAttribute('role') || '';
                const ariaLabel = element.getAttribute('aria-label') || '';
                const placeholder = element.getAttribute('placeholder') || '';
                const type = element.getAttribute('type') || '';
                const href = element.getAttribute('href') || '';
                const name = element.getAttribute('name') || '';
                
                const children = [];
                for (let child of element.children) {
                    const childStructure = getStructure(child);
                    if (childStructure) children.push(childStructure);
                }
                
                return {
                    tag,
                    id,
                    classes,
                    role,
                    ariaLabel,
                    placeholder,
                    type,
                    href,
                    name,
                    children,
                    childCount: children.length
                };
            }
            
            return getStructure(document.body);
        }''')
        
        structure_str = json.dumps(structural_dom, sort_keys=True)
        structure_hash = hashlib.sha256(structure_str.encode()).hexdigest()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"page_{structure_hash[:8]}_{timestamp}.png"
        screenshot_path = os.path.join(self.screenshots_path, screenshot_filename)
        
        await page.screenshot(path=screenshot_path, full_page=True)
        
        elements_with_text = await page.evaluate('''() => {
            function extractElements(element, path = '') {
                const elements = [];
                
                if (element.nodeType !== 1) return elements;
                
                const tag = element.tagName.toLowerCase();
                const id = element.id || '';
                const classes = Array.from(element.classList).join(' ');
                const text = element.textContent?.trim().substring(0, 100) || '';
                const role = element.getAttribute('role') || '';
                const ariaLabel = element.getAttribute('aria-label') || '';
                const placeholder = element.getAttribute('placeholder') || '';
                const type = element.getAttribute('type') || '';
                const href = element.getAttribute('href') || '';
                const name = element.getAttribute('name') || '';
                
                const currentPath = path + ' > ' + tag + (id ? '#' + id : '') + (classes ? '.' + classes.split(' ')[0] : '');
                
                const isInteractive = ['button', 'input', 'a', 'select', 'textarea'].includes(tag) || 
                                     role === 'button' || role === 'link';
                
                if (isInteractive || text || ariaLabel || placeholder) {
                    elements.push({
                        tag,
                        id,
                        classes,
                        text,
                        role,
                        ariaLabel,
                        placeholder,
                        type,
                        href,
                        name,
                        selector: currentPath,
                        isInteractive
                    });
                }
                
                for (let child of element.children) {
                    elements.push(...extractElements(child, currentPath));
                }
                
                return elements;
            }
            
            return extractElements(document.body);
        }''')
        
        return {
            "url": url,
            "structure_hash": structure_hash,
            "dom_structure": structural_dom,
            "full_html": body_html,
            "screenshot": screenshot_path,
            "elements": elements_with_text,
            "crawled_at": datetime.now().isoformat()
        }
    
    async def crawl_url(self, url: str, depth: int = 1) -> List[Dict]:
        results = []
        visited_hashes = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                page_data = await self.extract_dom_structure(page, url)
                results.append(page_data)
                visited_hashes.add(page_data['structure_hash'])
                
                if depth > 1:
                    links = await page.evaluate('''() => {
                        return Array.from(document.querySelectorAll('a[href]'))
                            .map(a => a.href)
                            .filter(href => href.startsWith(window.location.origin))
                            .slice(0, 10);
                    }''')
                    
                    for link in links:
                        try:
                            await page.goto(link, wait_until='networkidle', timeout=30000)
                            link_data = await self.extract_dom_structure(page, link)
                            
                            if link_data['structure_hash'] not in visited_hashes:
                                results.append(link_data)
                                visited_hashes.add(link_data['structure_hash'])
                        except Exception as e:
                            print(f"Error crawling {link}: {e}")
                            continue
            
            except Exception as e:
                print(f"Error crawling {url}: {e}")
                raise
            finally:
                await browser.close()
        
        return results
