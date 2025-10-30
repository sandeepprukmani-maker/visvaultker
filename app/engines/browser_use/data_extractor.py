"""
Advanced Data Extraction Capabilities
Structured data scraping, table extraction, and content parsing
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Advanced data extraction for web automation
    Handles tables, lists, structured data, and custom selectors
    """
    
    def __init__(self):
        """Initialize data extractor"""
        logger.info("📊 Data extractor initialized")
    
    async def extract_table(self, page, selector: str = "table", 
                          include_headers: bool = True) -> Dict[str, Any]:
        """
        Extract data from HTML table
        
        Args:
            page: Playwright page object
            selector: CSS selector for table
            include_headers: Extract header row
            
        Returns:
            Dictionary with table data
        """
        try:
            table_data = await page.evaluate(f"""(selector) => {{
                const table = document.querySelector(selector);
                if (!table) return null;
                
                const rows = Array.from(table.querySelectorAll('tr'));
                const data = [];
                
                rows.forEach((row, index) => {{
                    const cells = Array.from(row.querySelectorAll('td, th'));
                    const rowData = cells.map(cell => cell.textContent.trim());
                    if (rowData.length > 0) {{
                        data.push(rowData);
                    }}
                }});
                
                return data;
            }}""", selector)
            
            if not table_data:
                return {"success": False, "error": "Table not found"}
            
            result = {
                "success": True,
                "rows": table_data,
                "row_count": len(table_data),
                "column_count": len(table_data[0]) if table_data else 0
            }
            
            if include_headers and table_data:
                result["headers"] = table_data[0]
                result["data"] = table_data[1:]
            
            logger.info(f"📊 Table extracted: {result['row_count']} rows, {result['column_count']} columns")
            return result
            
        except Exception as e:
            logger.error(f"❌ Table extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_list(self, page, selector: str, item_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract items from a list
        
        Args:
            page: Playwright page object
            selector: CSS selector for list container
            item_selector: Optional selector for individual items
            
        Returns:
            Dictionary with list items
        """
        try:
            if item_selector:
                query = f"{selector} {item_selector}"
            else:
                query = f"{selector} li"
            
            items = await page.evaluate(f"""(query) => {{
                const elements = document.querySelectorAll(query);
                return Array.from(elements).map(el => el.textContent.trim());
            }}""", query)
            
            logger.info(f"📋 List extracted: {len(items)} items")
            
            return {
                "success": True,
                "items": items,
                "item_count": len(items)
            }
            
        except Exception as e:
            logger.error(f"❌ List extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_structured_data(self, page, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract structured data using a schema
        
        Args:
            page: Playwright page object
            schema: Dictionary mapping field names to CSS selectors
            
        Returns:
            Dictionary with extracted data
        """
        try:
            extracted_data = {}
            
            for field_name, selector in schema.items():
                try:
                    value = await page.evaluate(f"""(selector) => {{
                        const element = document.querySelector(selector);
                        return element ? element.textContent.trim() : null;
                    }}""", selector)
                    
                    extracted_data[field_name] = value
                except:
                    extracted_data[field_name] = None
            
            logger.info(f"📦 Structured data extracted: {len(extracted_data)} fields")
            
            return {
                "success": True,
                "data": extracted_data,
                "field_count": len(extracted_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Structured data extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_all_links(self, page, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract all links from page
        
        Args:
            page: Playwright page object
            base_url: Optional base URL for relative links
            
        Returns:
            Dictionary with links
        """
        try:
            links = await page.evaluate("""() => {
                const anchors = document.querySelectorAll('a[href]');
                return Array.from(anchors).map(a => ({
                    text: a.textContent.trim(),
                    href: a.href,
                    rel_href: a.getAttribute('href')
                }));
            }""")
            
            logger.info(f"🔗 Links extracted: {len(links)} links")
            
            return {
                "success": True,
                "links": links,
                "link_count": len(links),
                "page_url": page.url
            }
            
        except Exception as e:
            logger.error(f"❌ Link extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_images(self, page) -> Dict[str, Any]:
        """
        Extract all images from page
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary with image data
        """
        try:
            images = await page.evaluate("""() => {
                const imgs = document.querySelectorAll('img');
                return Array.from(imgs).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    width: img.width,
                    height: img.height
                }));
            }""")
            
            logger.info(f"🖼️  Images extracted: {len(images)} images")
            
            return {
                "success": True,
                "images": images,
                "image_count": len(images)
            }
            
        except Exception as e:
            logger.error(f"❌ Image extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_metadata(self, page) -> Dict[str, Any]:
        """
        Extract page metadata (title, description, etc.)
        
        Args:
            page: Playwright page object
            
        Returns:
            Dictionary with metadata
        """
        try:
            metadata = await page.evaluate("""() => {
                const getMeta = (name) => {
                    const element = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return element ? element.content : null;
                };
                
                return {
                    title: document.title,
                    description: getMeta('description') || getMeta('og:description'),
                    keywords: getMeta('keywords'),
                    author: getMeta('author'),
                    og_title: getMeta('og:title'),
                    og_image: getMeta('og:image'),
                    canonical: document.querySelector('link[rel="canonical"]')?.href
                };
            }""")
            
            metadata["url"] = page.url
            
            logger.info(f"ℹ️  Metadata extracted from: {page.url}")
            
            return {
                "success": True,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Metadata extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def extract_text_content(self, page, selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract text content from page or specific element
        
        Args:
            page: Playwright page object
            selector: Optional CSS selector for specific element
            
        Returns:
            Dictionary with text content
        """
        try:
            if selector:
                text = await page.evaluate(f"""(selector) => {{
                    const element = document.querySelector(selector);
                    return element ? element.textContent.trim() : null;
                }}""", selector)
            else:
                text = await page.evaluate("""() => {
                    return document.body.textContent.trim();
                }""")
            
            logger.info(f"📝 Text content extracted: {len(text)} characters")
            
            return {
                "success": True,
                "text": text,
                "length": len(text) if text else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Text extraction failed: {str(e)}")
            return {"success": False, "error": str(e)}
