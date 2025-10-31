import os
import json
import logging
from openai import OpenAI
from services.oauth_config import OauthConfig, OauthTokenFetcher

logging.basicConfig(level=logging.INFO)


class AIService:
    def __init__(self):
        use_oauth = os.environ.get('USE_OAUTH_FOR_OPENAI', 'false').lower() == 'true'
        
        if use_oauth:
            required_env_vars = [
                "OAUTH_TOKEN_URL",
                "OAUTH_CLIENT_ID", 
                "OAUTH_CLIENT_SECRET",
                "OAUTH_GRANT_TYPE",
                "OAUTH_SCOPE"
            ]
            
            missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
            if missing_vars:
                logging.error(f"Missing required OAuth environment variables: {', '.join(missing_vars)}")
                self.client = None
                self.token_fetcher = None
                return
            
            try:
                oauth_config = OauthConfig(
                    token_url=os.environ["OAUTH_TOKEN_URL"],
                    client_id=os.environ["OAUTH_CLIENT_ID"],
                    client_secret=os.environ["OAUTH_CLIENT_SECRET"],
                    grant_type=os.environ["OAUTH_GRANT_TYPE"],
                    scope=os.environ["OAUTH_SCOPE"]
                )
                
                self.token_fetcher = OauthTokenFetcher(oauth_config)
                self.base_url = os.environ.get("GPT_BASE_URL")
                self.client = self._get_oauth_client()
                logging.info("OAuth authentication configured successfully")
            except Exception as e:
                logging.error(f"Failed to configure OAuth: {e}")
                self.client = None
                self.token_fetcher = None
        else:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.token_fetcher = None
            else:
                self.client = None
                self.token_fetcher = None
    
    def _get_oauth_client(self):
        """Get OpenAI client with fresh OAuth token."""
        if self.token_fetcher:
            if self.base_url:
                return OpenAI(
                    api_key=self.token_fetcher.get_token(),
                    base_url=self.base_url
                )
            else:
                return OpenAI(api_key=self.token_fetcher.get_token())
        return None
    
    def _ensure_client(self):
        """Ensure client has a fresh OAuth token before making requests."""
        if self.token_fetcher:
            self.client = self._get_oauth_client()
    
    def generate_acceptance_criteria(self, epic_title, epic_description):
        self._ensure_client()
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
        self._ensure_client()
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
    
    def refine_ac_with_context(self, story_title, current_ac, epic_title, epic_description, 
                                all_stories, conversation_history, user_message):
        """
        Enhanced AC refinement with full context awareness.
        
        Args:
            story_title: Title of the current story being edited
            current_ac: Current acceptance criteria
            epic_title: Parent EPIC title
            epic_description: Parent EPIC description
            all_stories: List of all stories in the EPIC for context
            conversation_history: Previous chat messages
            user_message: Current user instruction
        """
        self._ensure_client()
        if not self.client:
            return {
                "refined_ac": f"{current_ac}\n\n[Note: AI refinement unavailable]",
                "response_message": "AI service unavailable"
            }
        
        # Build context about other stories
        other_stories_context = ""
        if all_stories:
            other_stories_list = [
                f"- {s['title']}: {s.get('current_ac', 'No AC')[:100]}..." 
                for s in all_stories if s['title'] != story_title
            ]
            if other_stories_list:
                other_stories_context = "\n\nOther Stories in this EPIC:\n" + "\n".join(other_stories_list[:5])
        
        system_prompt = f"""You are an expert business analyst AI assistant helping to refine acceptance criteria for user stories.

CONTEXT:
- EPIC: {epic_title}
- EPIC Description: {epic_description}
- Current Story: {story_title}
- Current AC: {current_ac}{other_stories_context}

YOUR CAPABILITIES:
1. Understand the story's relationship to the EPIC
2. Know what other stories cover to avoid duplication
3. Detect conflicts or overlaps with existing stories
4. Provide intelligent suggestions based on the EPIC's goals
5. Remember our conversation and build upon previous refinements

INSTRUCTIONS:
- Analyze the user's request in context of the EPIC and other stories
- If the request conflicts with the EPIC or duplicates other stories, explain why
- Provide thoughtful, context-aware responses
- When refining AC, maintain Gherkin format (Given/When/Then) unless asked otherwise
- Be conversational and helpful, not robotic"""

        # Build conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Try to extract refined AC if the response contains it
            # The AI should format with markers or we take the whole response as AC
            refined_ac = current_ac  # Default to current if we can't extract
            response_message = ai_response
            
            # Check if AI provided structured response with AC
            if "REFINED AC:" in ai_response or "Updated AC:" in ai_response:
                parts = ai_response.split("REFINED AC:" if "REFINED AC:" in ai_response else "Updated AC:")
                if len(parts) > 1:
                    refined_ac = parts[1].strip()
                    response_message = parts[0].strip()
            elif any(keyword in ai_response.lower() for keyword in ["given", "when", "then"]):
                # If response contains Gherkin keywords, treat it as the AC
                refined_ac = ai_response
                response_message = "I've updated the acceptance criteria based on your request."
            
            return {
                "refined_ac": refined_ac,
                "response_message": response_message,
                "full_response": ai_response
            }
            
        except Exception as e:
            raise Exception(f"Context-aware refinement failed: {str(e)}")
    
    def analyze_epic_coverage(self, epic_title, epic_description, existing_stories):
        self._ensure_client()
        
        # If there are no existing stories, return 0% coverage immediately
        if not existing_stories or len(existing_stories) == 0:
            if not self.client:
                return {
                    "coverage_status": "none",
                    "updated_stories": [],
                    "new_story_suggestions": [],
                    "redundant_stories": [],
                    "coverage_percentage": 0,
                    "summary": "No user stories exist yet for this EPIC."
                }
            
            # Let AI suggest new stories for empty EPIC
            return self._analyze_empty_epic(epic_title, epic_description)
        
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
    
    def _analyze_empty_epic(self, epic_title, epic_description):
        """Analyze an EPIC with no existing stories and suggest new stories."""
        prompt = f"""Analyze this EPIC and suggest user stories to implement it.

EPIC Title: {epic_title}
EPIC Description: {epic_description}

Since there are no existing user stories, suggest new stories needed to fully implement this EPIC.

Output Format (JSON):
{{
  "coverage_status": "none",
  "coverage_percentage": 0,
  "updated_stories": [],
  "new_story_suggestions": [
    {{
      "story_title": "story title",
      "reason": "what this story covers from the EPIC",
      "suggested_ac": "acceptance criteria in Gherkin format"
    }}
  ],
  "redundant_stories": [],
  "summary": "brief summary explaining there are no existing stories and what's needed"
}}

Return ONLY the JSON object, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a business analyst expert in breaking down EPICs into user stories."},
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
                # Ensure coverage is 0 for empty EPICs
                result['coverage_percentage'] = 0
                result['coverage_status'] = 'none'
                return result
            return {
                "coverage_status": "none",
                "coverage_percentage": 0,
                "updated_stories": [],
                "new_story_suggestions": [],
                "redundant_stories": [],
                "summary": "No existing stories for this EPIC."
            }
            
        except Exception as e:
            raise Exception(f"Empty EPIC analysis failed: {str(e)}")
    
    def check_story_alignment(self, epic_title, epic_description, story_title, story_ac):
        self._ensure_client()
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
