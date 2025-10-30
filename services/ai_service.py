import os
import json
from openai import OpenAI

class AIService:
    def __init__(self):
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def generate_acceptance_criteria(self, epic_title, epic_description):
        if not self.client:
            return [{
                "story_title": "Sample Story from " + epic_title[:30],
                "criteria": [
                    "Given a user is logged in",
                    "When they perform the main action",
                    "Then the expected outcome occurs"
                ]
            }]
        
        prompt = f"""You are an AI that extracts and writes acceptance criteria from EPICs.

Input:
EPIC: {epic_title}
Description: {epic_description}

Generate structured acceptance criteria in Gherkin format (Given/When/Then).
Break down the EPIC into logical user stories with their acceptance criteria.

Output Format (JSON):
[
  {{
    "story_title": "Story Title",
    "criteria": [
      "Given [context], When [action], Then [outcome]",
      "Given [context], When [action], Then [outcome]"
    ]
  }}
]

Return ONLY the JSON array, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert in writing acceptance criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            if content:
                content = content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                result = json.loads(content)
                return result
            return []
            
        except Exception as e:
            raise Exception(f"AI generation failed: {str(e)}")
    
    def refine_acceptance_criteria(self, current_ac, user_instruction):
        if not self.client:
            return f"{current_ac}\n\n[Note: AI refinement unavailable - OpenAI API key not configured]"
        
        prompt = f"""Current Acceptance Criteria:
{current_ac}

User Instruction: {user_instruction}

Please refine the acceptance criteria based on the user's instruction.
Return ONLY the refined acceptance criteria text, no additional explanation."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert in refining acceptance criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            refined_ac = response.choices[0].message.content
            if refined_ac:
                return refined_ac.strip()
            return current_ac
            
        except Exception as e:
            raise Exception(f"AI refinement failed: {str(e)}")
