from openai import OpenAI
from typing import Dict
import json

class SemanticLabeler:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
    
    def label_template(self, dom_structure: Dict, url: str = "") -> Dict:
        structure_summary = self._create_structure_summary(dom_structure)
        
        prompt = f"""Analyze this web page structure and provide semantic understanding.

URL: {url}

Page Structure Summary:
{structure_summary}

Identify:
1. Page type (e.g., login page, dashboard, user list, product detail, etc.)
2. Main purpose of this page
3. Key interactive elements and their purposes
4. Common user actions possible on this page

Return ONLY valid JSON in this exact format:
{{
  "page_type": "...",
  "purpose": "...",
  "key_components": [
    {{"name": "...", "purpose": "..."}}
  ],
  "user_actions": [...]
}}"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a UI/UX expert that analyzes web page structures. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return result
        return {"page_type": "unknown", "purpose": "", "key_components": [], "user_actions": []}
    
    def _create_structure_summary(self, dom_structure: Dict, max_depth: int = 3, current_depth: int = 0) -> str:
        if current_depth >= max_depth or not isinstance(dom_structure, dict):
            return ""
        
        lines = []
        indent = "  " * current_depth
        
        tag = dom_structure.get('tag', 'unknown')
        id_val = dom_structure.get('id', '')
        classes = dom_structure.get('classes', '')
        role = dom_structure.get('role', '')
        aria_label = dom_structure.get('ariaLabel', '')
        
        descriptor = f"{tag}"
        if id_val:
            descriptor += f"#{id_val}"
        if classes:
            descriptor += f".{classes.split()[0]}"
        if role:
            descriptor += f"[{role}]"
        if aria_label:
            descriptor += f" '{aria_label}'"
        
        lines.append(f"{indent}{descriptor}")
        
        children = dom_structure.get('children', [])
        for child in children[:10]:
            child_summary = self._create_structure_summary(child, max_depth, current_depth + 1)
            if child_summary:
                lines.append(child_summary)
        
        return "\n".join(lines)
