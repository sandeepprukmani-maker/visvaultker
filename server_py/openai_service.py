import os
import json
from typing import Optional
from openai import AsyncOpenAI

async def create_openai_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("GW_BASE_URL", "https://api.openai.com/v1")
    return AsyncOpenAI(api_key=api_key, base_url=base_url)

class OpenAIService:
    async def generate_embedding(self, text: str) -> list[float]:
        try:
            openai = await create_openai_client()
            response = await openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as error:
            print(f"Error generating embedding: {error}")
            raise error

    async def analyze_page(self, page_data: dict) -> dict:
        try:
            elements_description = "\n".join(
                f"<{el['tag']}>{el.get('text', '')}</{el['tag']}>"
                for el in page_data["elements"][:50]
            )

            prompt = f"""Analyze this web page and provide semantic understanding:

URL: {page_data['url']}
Title: {page_data['title']}

Key Elements:
{elements_description}

Provide a JSON response with:
1. pageType: A concise label (e.g., "Login Page", "Dashboard", "User Profile")
2. description: Brief description of the page's purpose
3. possibleActions: Array of common actions users might perform here
4. keyElements: Array of the most important UI elements on the page

Respond only with valid JSON, no markdown formatting."""

            openai = await create_openai_client()
            response = await openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a web page analyzer. Analyze web pages and identify their purpose, type, and key interactive elements. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content or "{}")
            return {
                "pageType": analysis.get("pageType", "Unknown Page"),
                "description": analysis.get("description", ""),
                "possibleActions": analysis.get("possibleActions", []),
                "keyElements": analysis.get("keyElements", [])
            }
        except Exception as error:
            print(f"Error analyzing page: {error}")
            return {
                "pageType": "Unknown Page",
                "description": "Unable to analyze page",
                "possibleActions": [],
                "keyElements": []
            }

    async def generate_automation_plan(self, command: str, pages: list[dict]) -> dict:
        try:
            pages_context = "\n\n".join(
                f"Page: {p['url']}\nTitle: {p['title']}\nElements: {json.dumps(p['elements'][:20])}"
                for p in pages[:5]
            )

            prompt = f"""Given this command: "{command}"

Available pages and elements:
{pages_context}

Create an automation plan with step-by-step instructions.

Provide JSON with:
1. steps: Array of {{action, selector, value, description}} objects
2. estimatedDuration: milliseconds
3. confidence: 0-100 score

Actions: navigate, click, type, select, wait, waitForElement, scroll, hover, pressKey, extract, extractTable, verify, screenshot

Respond with valid JSON only."""

            openai = await create_openai_client()
            response = await openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an automation expert. Create detailed, reliable automation plans from natural language commands. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            plan = json.loads(response.choices[0].message.content or "{}")
            return {
                "steps": plan.get("steps", []),
                "estimatedDuration": plan.get("estimatedDuration", 5000),
                "confidence": plan.get("confidence", 50)
            }
        except Exception as error:
            print(f"Error generating automation plan: {error}")
            return {
                "steps": [],
                "estimatedDuration": 0,
                "confidence": 0
            }

    async def analyze_screenshot(self, screenshot_base64: str, query: Optional[str] = None) -> dict:
        try:
            prompt = query if query else "Analyze this screenshot and identify all interactive UI elements.\n\nProvide JSON with:\n1. elements: Array of objects with {description, location: {x, y, width, height}, type, text}\n2. layout: Overall layout description\n3. suggestions: Array of accessibility/usability suggestions"

            openai = await create_openai_client()
            response = await openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert UI/UX analyzer. Analyze screenshots to identify elements, layout patterns, and provide actionable insights. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": screenshot_base64,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
                max_tokens=4096
            )

            analysis = json.loads(response.choices[0].message.content or "{}")
            return {
                "elements": analysis.get("elements", []),
                "layout": analysis.get("layout", "Unable to analyze layout"),
                "suggestions": analysis.get("suggestions", [])
            }
        except Exception as error:
            print(f"Error analyzing screenshot: {error}")
            return {
                "elements": [],
                "layout": "Unable to analyze",
                "suggestions": []
            }

    async def compare_screenshots(self, screenshot1: str, screenshot2: str) -> dict:
        try:
            prompt = "Compare these two screenshots and identify what changed.\n\nProvide JSON with:\n1. changeDetected: boolean\n2. changedRegions: Array of {x, y, width, height, description} for changed areas\n3. similarityScore: 0-100 percentage\n4. summary: Brief description of changes"

            openai = await create_openai_client()
            response = await openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a visual comparison expert. Compare screenshots to detect changes, new elements, removed elements, and layout shifts. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": screenshot1, "detail": "high"}},
                            {"type": "image_url", "image_url": {"url": screenshot2, "detail": "high"}}
                        ]
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            comparison = json.loads(response.choices[0].message.content or "{}")
            return {
                "changeDetected": comparison.get("changeDetected", False),
                "changedRegions": comparison.get("changedRegions", []),
                "similarityScore": comparison.get("similarityScore", 0),
                "summary": comparison.get("summary", "")
            }
        except Exception as error:
            print(f"Error comparing screenshots: {error}")
            return {
                "changeDetected": False,
                "changedRegions": [],
                "similarityScore": 0,
                "summary": "Unable to compare"
            }

    async def find_element_by_visual(self, screenshot: str, description: str) -> dict:
        try:
            prompt = f"Find the element matching this description: {description}\n\nProvide JSON with approximate location: {{x, y, width, height}}"

            openai = await create_openai_client()
            response = await openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an element locator. Find UI elements in screenshots based on descriptions. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": screenshot, "detail": "high"}}
                        ]
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            location = json.loads(response.choices[0].message.content or "{}")
            return location
        except Exception as error:
            print(f"Error finding element: {error}")
            return {}

    async def generate_smart_selectors(self, element_description: str, page_context: dict) -> dict:
        try:
            elements_info = json.dumps(page_context.get("elements", [])[:30])
            prompt = f"Generate smart selectors for: {element_description}\n\nPage elements: {elements_info}\n\nProvide JSON with: cssSelector, xpath, textSelector, ariaSelector, confidence (0-100)"

            openai = await create_openai_client()
            response = await openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a selector generator. Create robust selectors for web automation. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content or "{}")
            return {
                "cssSelector": result.get("cssSelector"),
                "xpath": result.get("xpath"),
                "textSelector": result.get("textSelector"),
                "ariaSelector": result.get("ariaSelector"),
                "confidence": result.get("confidence", 50)
            }
        except Exception as error:
            print(f"Error generating smart selectors: {error}")
            return {"confidence": 0}

openai_service = OpenAIService()
