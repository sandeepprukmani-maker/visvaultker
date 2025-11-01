"""
🎭 Planner Agent - Explores the app and produces Markdown test plans

Inspired by Playwright's test agent architecture, this agent:
1. Crawls and analyzes web applications
2. Generates human-readable, structured test plans in Markdown
3. Creates comprehensive scenario coverage with steps and expected results
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from pathlib import Path


class PlannerAgent:
    """Generates structured test plans from web application exploration"""
    
    def __init__(self, crawler, embedder, semantic_labeler, openai_client):
        self.crawler = crawler
        self.embedder = embedder
        self.semantic_labeler = semantic_labeler
        self.openai_client = openai_client
        self.specs_dir = Path("data/specs")
        self.specs_dir.mkdir(parents=True, exist_ok=True)
    
    async def explore_and_plan(
        self, 
        url: str, 
        scenarios: List[str],
        seed_context: Optional[Dict[str, Any]] = None,
        prd: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Explore the application and generate a comprehensive test plan
        
        Args:
            url: Starting URL to explore
            scenarios: List of scenarios/flows to plan for (e.g., ["guest checkout", "user login"])
            seed_context: Optional seed test context for initialization
            prd: Optional Product Requirements Document for additional context
        
        Returns:
            Dictionary with plan metadata and file path
        """
        # Step 1: Crawl the application
        crawl_result = await self.crawler.crawl(url, depth=2)
        
        # Step 2: Extract and analyze UI elements
        elements = await self._extract_interactive_elements(crawl_result)
        
        # Step 3: Generate semantic labels
        labeled_elements = await self._label_elements(elements)
        
        # Step 4: Build context for GPT
        context = self._build_planning_context(
            url, 
            labeled_elements, 
            crawl_result,
            seed_context,
            prd
        )
        
        # Step 5: Generate plan for each scenario
        plans = []
        for scenario in scenarios:
            plan = await self._generate_scenario_plan(scenario, context)
            plans.append(plan)
        
        # Step 6: Combine into comprehensive Markdown document
        markdown_plan = self._create_markdown_spec(url, plans, context)
        
        # Step 7: Save the plan
        spec_path = self._save_spec(url, scenarios, markdown_plan)
        
        return {
            "spec_path": str(spec_path),
            "scenarios_count": len(scenarios),
            "elements_analyzed": len(labeled_elements),
            "plan_preview": markdown_plan[:500] + "..." if len(markdown_plan) > 500 else markdown_plan,
            "created_at": datetime.now().isoformat()
        }
    
    async def _extract_interactive_elements(self, crawl_result: Dict) -> List[Dict]:
        """Extract interactive elements from crawl results"""
        elements = []
        
        for page_data in crawl_result.get("pages", []):
            dom_elements = page_data.get("dom_elements", [])
            
            # Filter for interactive elements
            interactive_types = {"button", "input", "select", "textarea", "a", "checkbox", "radio"}
            
            for elem in dom_elements:
                if elem.get("tag") in interactive_types or elem.get("role") in interactive_types:
                    elements.append({
                        "url": page_data.get("url"),
                        "tag": elem.get("tag"),
                        "role": elem.get("role"),
                        "text": elem.get("text", ""),
                        "attributes": elem.get("attributes", {}),
                        "selector": elem.get("selector", "")
                    })
        
        return elements
    
    async def _label_elements(self, elements: List[Dict]) -> List[Dict]:
        """Add semantic labels to elements"""
        labeled = []
        
        for elem in elements:
            # Create description for semantic labeling
            description = f"{elem['tag']} - {elem.get('text', '')} {elem.get('attributes', {}).get('placeholder', '')}"
            
            # Get semantic label
            label = await self.semantic_labeler.label_element(description)
            
            elem["semantic_label"] = label
            labeled.append(elem)
        
        return labeled
    
    def _build_planning_context(
        self, 
        url: str, 
        elements: List[Dict], 
        crawl_result: Dict,
        seed_context: Optional[Dict] = None,
        prd: Optional[str] = None
    ) -> Dict:
        """Build comprehensive context for plan generation"""
        # Organize elements by page
        elements_by_page = {}
        for elem in elements:
            page_url = elem.get("url", url)
            if page_url not in elements_by_page:
                elements_by_page[page_url] = []
            elements_by_page[page_url].append(elem)
        
        # Group by semantic category
        elements_by_category = {}
        for elem in elements:
            category = elem.get("semantic_label", "other")
            if category not in elements_by_category:
                elements_by_category[category] = []
            elements_by_category[category].append(elem)
        
        context = {
            "url": url,
            "total_elements": len(elements),
            "elements_by_page": elements_by_page,
            "elements_by_category": elements_by_category,
            "pages_crawled": len(crawl_result.get("pages", [])),
            "templates_detected": crawl_result.get("templates", [])
        }
        
        if seed_context:
            context["seed_context"] = seed_context
        
        if prd:
            context["prd"] = prd
        
        return context
    
    async def _generate_scenario_plan(self, scenario: str, context: Dict) -> Dict:
        """Generate a detailed plan for a specific scenario using GPT"""
        
        # Build the prompt
        prompt = self._build_scenario_prompt(scenario, context)
        
        # Call OpenAI
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a test planning expert. Generate detailed, structured test plans 
                        that include:
                        1. Clear scenario description
                        2. Step-by-step user actions
                        3. Expected results for each step
                        4. Edge cases and error conditions
                        5. Data requirements
                        
                        Be precise and thorough. Each step should be actionable and verifiable."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3
            )
        )
        
        plan_text = response.choices[0].message.content
        
        return {
            "scenario": scenario,
            "plan": plan_text,
            "elements_referenced": self._extract_element_references(plan_text, context)
        }
    
    def _build_scenario_prompt(self, scenario: str, context: Dict) -> str:
        """Build a detailed prompt for scenario planning"""
        
        # Summarize available elements
        element_summary = []
        for category, elements in context.get("elements_by_category", {}).items():
            element_summary.append(f"\n{category.upper()} ({len(elements)} elements):")
            for elem in elements[:5]:  # Show first 5 of each category
                text = elem.get("text", "")[:50]
                element_summary.append(f"  - {elem['tag']}: {text}")
        
        prompt = f"""Generate a comprehensive test plan for the following scenario:

SCENARIO: {scenario}

APPLICATION CONTEXT:
- URL: {context['url']}
- Pages Crawled: {context['pages_crawled']}
- Total Interactive Elements: {context['total_elements']}

AVAILABLE UI ELEMENTS:
{''.join(element_summary)}

"""
        
        if "prd" in context:
            prompt += f"\nPRODUCT REQUIREMENTS:\n{context['prd']}\n"
        
        if "seed_context" in context:
            prompt += f"\nSEED TEST CONTEXT:\n{json.dumps(context['seed_context'], indent=2)}\n"
        
        prompt += """
Please generate a test plan with:
1. Scenario overview
2. Prerequisites/setup
3. Detailed step-by-step actions
4. Expected results after each step
5. Edge cases to test
6. Cleanup/teardown steps

Format as structured Markdown with clear headers and numbered lists.
"""
        
        return prompt
    
    def _extract_element_references(self, plan_text: str, context: Dict) -> List[str]:
        """Extract which UI elements are referenced in the plan"""
        references = []
        
        for elem in context.get("elements_by_category", {}).get("button", [])[:10]:
            if elem.get("text", "").lower() in plan_text.lower():
                references.append(elem.get("text", ""))
        
        return references
    
    def _create_markdown_spec(self, url: str, plans: List[Dict], context: Dict) -> str:
        """Create a comprehensive Markdown specification document"""
        
        markdown = f"""# Test Plan for {url}

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Pages Analyzed**: {context['pages_crawled']}  
**Interactive Elements**: {context['total_elements']}

---

## Application Overview

This application was automatically explored and analyzed to produce comprehensive test scenarios.

### Discovered Elements by Category

"""
        
        # Add element categories
        for category, elements in context.get("elements_by_category", {}).items():
            markdown += f"- **{category.title()}**: {len(elements)} elements\n"
        
        markdown += "\n---\n\n## Test Scenarios\n\n"
        
        # Add each scenario plan
        for idx, plan_data in enumerate(plans, 1):
            markdown += f"### {idx}. {plan_data['scenario']}\n\n"
            markdown += plan_data['plan']
            markdown += "\n\n---\n\n"
        
        return markdown
    
    def _save_spec(self, url: str, scenarios: List[str], markdown: str) -> Path:
        """Save the specification to a file"""
        
        # Create a filename from URL and scenarios
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.replace(".", "_")
        scenario_slug = "_".join(s.replace(" ", "-").lower()[:20] for s in scenarios[:2])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{scenario_slug}_{timestamp}.md"
        
        spec_path = self.specs_dir / filename
        
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        # Also save metadata
        metadata = {
            "url": url,
            "scenarios": scenarios,
            "spec_file": filename,
            "created_at": datetime.now().isoformat()
        }
        
        metadata_path = self.specs_dir / f"{filename}.meta.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        return spec_path
    
    def list_specs(self) -> List[Dict]:
        """List all generated specs"""
        specs = []
        
        for meta_file in self.specs_dir.glob("*.meta.json"):
            with open(meta_file) as f:
                metadata = json.load(f)
                specs.append(metadata)
        
        return sorted(specs, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def get_spec(self, filename: str) -> Optional[str]:
        """Retrieve a specific spec by filename"""
        spec_path = self.specs_dir / filename
        
        if spec_path.exists():
            with open(spec_path, "r", encoding="utf-8") as f:
                return f.read()
        
        return None
