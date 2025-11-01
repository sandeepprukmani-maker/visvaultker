from openai import OpenAI
from typing import List, Dict
import json

class ActionPlanner:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
    
    def generate_plan(self, task: str, context: List[Dict]) -> List[Dict]:
        context_str = json.dumps(context, indent=2)
        
        prompt = f"""You are an automation planning assistant. Given a task and available UI elements, create a step-by-step automation plan.

Task: {task}

Available UI Elements:
{context_str}

Generate a sequence of automation actions. Each action should have:
- action_type: one of [navigate, click, input, wait, extract, scroll]
- selector: CSS selector or element description
- value: value for input actions (optional)
- description: what this step does

Return ONLY valid JSON in this format:
{{
  "plan": [
    {{
      "step": 1,
      "action_type": "...",
      "selector": "...",
      "value": "...",
      "description": "..."
    }}
  ]
}}"""
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at creating web automation plans. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return result.get('plan', [])
        return []
