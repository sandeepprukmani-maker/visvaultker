"""
Intelligent Data Extraction
Uses LLM reasoning to extract structured data from HTML or JSON
"""
import json
import logging
from typing import Any, List, Dict, Optional

logger = logging.getLogger(__name__)


class SemanticExtractor:
    """
    Uses LLM reasoning to extract structured data from HTML or JSON.
    """

    def __init__(self, llm):
        """
        Initialize semantic extractor
        
        Args:
            llm: Language model for extraction
        """
        self.llm = llm
        logger.info("🔍 Semantic Extractor initialized")

    async def extract(self, html: str, schema: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract structured information from HTML
        
        Args:
            html: HTML content to extract from
            schema: Optional list of fields to extract
            
        Returns:
            List of extracted data dictionaries
        """
        schema_text = ", ".join(schema) if schema else "auto-detect relevant data"
        
        # Truncate HTML to avoid token limits
        html_snippet = html[:8000] if len(html) > 8000 else html
        
        prompt = f"""
Extract structured information from the following HTML.
Target schema: {schema_text}
Return as a JSON array of objects.

HTML:
{html_snippet}

Output format:
[
  {{"field1": "value1", "field2": "value2"}},
  {{"field1": "value3", "field2": "value4"}}
]

If no structured data is found, return an empty array: []
"""
        try:
            logger.info(f"🔍 Extracting data with schema: {schema_text}")
            response = await self.llm.ainvoke(prompt)
            response_text = str(response)
            
            # Extract JSON if wrapped in markdown
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Try to parse as JSON
            try:
                data = json.loads(response_text)
                if isinstance(data, list):
                    logger.info(f"✅ Extracted {len(data)} items")
                    return data
                elif isinstance(data, dict):
                    logger.info("✅ Extracted 1 item (dict converted to list)")
                    return [data]
                else:
                    logger.warning(f"Unexpected data type: {type(data)}")
                    return [{"raw_data": str(data)}]
            except json.JSONDecodeError:
                # Fallback: return raw text
                logger.warning("Could not parse as JSON, returning raw text")
                return [{"raw_text": response_text.strip()}]
                
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return [{"error": str(e)}]

    async def extract_from_page(self, page, schema: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract structured data directly from a Playwright page
        
        Args:
            page: Playwright page object
            schema: Optional list of fields to extract
            
        Returns:
            List of extracted data dictionaries
        """
        try:
            # Get page HTML
            html = await page.content()
            return await self.extract(html, schema)
        except Exception as e:
            logger.error(f"❌ Page extraction failed: {e}")
            return [{"error": str(e)}]
