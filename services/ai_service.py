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
                model="gpt-4o-mini",
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
                model="gpt-4o-mini",
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
    
    def analyze_epic_coverage(self, epic_title, epic_description, existing_stories):
        if not self.client:
            return {
                "coverage_status": "limited",
                "updated_stories": [],
                "new_story_suggestions": [],
                "redundant_stories": [],
                "coverage_percentage": 50
            }
        
        stories_summary = "\n".join([
            f"- Jira ID: {s.get('jira_id', 'N/A')}, Story: {s['title']}\n  Current AC: {s.get('current_ac', 'None')}"
            for s in existing_stories
        ])
        
        prompt = f"""Analyze the coverage of an EPIC by its user stories.

EPIC Title: {epic_title}
EPIC Description: {epic_description}

Existing User Stories:
{stories_summary}

Perform the following analysis:
1. Identify which parts of the EPIC are covered by existing stories
2. Identify missing functionalities that need new stories
3. Identify stories that need updated ACs to better match the EPIC
4. Identify potentially redundant or duplicate stories
5. Calculate coverage percentage

Output Format (JSON):
{{
  "coverage_status": "full|partial|limited",
  "coverage_percentage": 0-100,
  "updated_stories": [
    {{
      "jira_id": "existing story Jira ID (e.g., DEMO-200)",
      "story_title": "title",
      "reason": "why update is needed",
      "suggested_ac": "updated acceptance criteria in Gherkin format"
    }}
  ],
  "new_story_suggestions": [
    {{
      "story_title": "new story title",
      "reason": "what gap this fills",
      "suggested_ac": "acceptance criteria in Gherkin format"
    }}
  ],
  "redundant_stories": [
    {{
      "jira_id": "Jira ID of redundant story",
      "reason": "why it might be redundant"
    }}
  ],
  "summary": "brief analysis summary"
}}

Return ONLY the JSON object, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert in coverage analysis and acceptance criteria."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            if content:
                content = content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                result = json.loads(content)
                return result
            return {}
            
        except Exception as e:
            raise Exception(f"Coverage analysis failed: {str(e)}")
    
    def check_story_alignment(self, epic_title, epic_description, story_title, story_ac):
        if not self.client:
            return {
                "aligned": True,
                "alignment_score": 75,
                "suggested_ac": story_ac,
                "reasoning": "Alignment check unavailable - OpenAI API key not configured"
            }
        
        prompt = f"""Check if a user story's acceptance criteria aligns with its parent EPIC.

EPIC Title: {epic_title}
EPIC Description: {epic_description}

Story Title: {story_title}
Current AC: {story_ac}

Analyze:
1. Does the story AC align with the EPIC's goals?
2. Is anything missing or outdated?
3. Should the AC be updated?

Output Format (JSON):
{{
  "aligned": true|false,
  "alignment_score": 0-100,
  "reasoning": "explanation of alignment status",
  "suggested_ac": "updated AC if needed, or original if aligned",
  "changes_needed": ["list of specific changes if alignment is poor"]
}}

Return ONLY the JSON object, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert in story alignment and acceptance criteria."},
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
            return {}
            
        except Exception as e:
            raise Exception(f"Alignment check failed: {str(e)}")
