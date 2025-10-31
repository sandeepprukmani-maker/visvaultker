import requests
from requests.auth import HTTPBasicAuth
import logging

logging.basicConfig(level=logging.INFO)

class JiraService:
    def __init__(self, jira_url, username, password):
        """Initialize Jira service with credentials"""
        self.jira_url = jira_url.rstrip('/')
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_epic(self, epic_id):
        """Fetch EPIC details from Jira"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{epic_id}"
            response = requests.get(url, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            
            issue = response.json()
            
            return {
                'id': epic_id,
                'title': issue['fields'].get('summary', ''),
                'description': issue['fields'].get('description', ''),
                'status': issue['fields']['status']['name']
            }
        except Exception as e:
            logging.error(f"Failed to fetch EPIC {epic_id}: {e}")
            return None
    
    def get_epic_stories(self, epic_id):
        """Fetch all stories linked to an EPIC"""
        try:
            jql = f'parent={epic_id}'
            url = f"{self.jira_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'fields': 'summary,description,status,assignee'
            }
            
            response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
            response.raise_for_status()
            
            data = response.json()
            stories = []
            
            for issue in data.get('issues', []):
                stories.append({
                    'id': issue['key'],
                    'title': issue['fields'].get('summary', ''),
                    'description': issue['fields'].get('description', ''),
                    'status': issue['fields']['status']['name'],
                    'current_ac': self._extract_acceptance_criteria(issue['fields'].get('description', ''))
                })
            
            return stories
        except Exception as e:
            logging.error(f"Failed to fetch stories for EPIC {epic_id}: {e}")
            return []
    
    def _extract_acceptance_criteria(self, description):
        """Extract acceptance criteria from Jira description if present"""
        if not description:
            return None
        
        if isinstance(description, dict):
            return str(description)
        
        ac_markers = ['acceptance criteria', 'ac:', 'given/when/then']
        description_lower = description.lower()
        
        for marker in ac_markers:
            if marker in description_lower:
                return description
        
        return None
    
    def update_story_description(self, story_id, new_description):
        """Update a Jira story's description with new acceptance criteria"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{story_id}"
            payload = {
                'fields': {
                    'description': new_description
                }
            }
            
            response = requests.put(url, json=payload, headers=self.headers, auth=self.auth)
            response.raise_for_status()
            
            logging.info(f"Successfully updated story {story_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to update story {story_id}: {e}")
            return False
