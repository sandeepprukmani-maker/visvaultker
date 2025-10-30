import requests
from requests.auth import HTTPBasicAuth
import json

class JiraService:
    def __init__(self, jira_url, username, password):
        if not jira_url or not username or not password:
            raise ValueError("Jira URL, username, and password are required")
        self.jira_url = jira_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_epic(self, epic_id):
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{epic_id}"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            return {
                'id': data['key'],
                'title': data['fields'].get('summary', ''),
                'description': data['fields'].get('description', '')
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Unable to connect to Jira. Please try again. Error: {str(e)}")
    
    def get_epic_stories(self, epic_id):
        try:
            jql = f"'Epic Link' = {epic_id}"
            url = f"{self.jira_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'fields': 'summary,description,status,customfield_10200'
            }
            
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            stories = []
            for issue in data.get('issues', []):
                ac_field = issue['fields'].get('customfield_10200', '')
                
                stories.append({
                    'id': issue['key'],
                    'title': issue['fields'].get('summary', ''),
                    'description': issue['fields'].get('description', ''),
                    'status': issue['fields'].get('status', {}).get('name', ''),
                    'acceptance_criteria': ac_field if ac_field else ''
                })
            
            return stories
        except requests.exceptions.RequestException as e:
            raise Exception(f"Unable to fetch stories. Error: {str(e)}")
    
    def update_story_ac(self, story_id, acceptance_criteria):
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{story_id}"
            data = {
                'fields': {
                    'customfield_10200': acceptance_criteria
                }
            }
            
            response = requests.put(url, auth=self.auth, headers=self.headers, json=data)
            
            if response.status_code in [200, 204]:
                return True
            
            return False
        except requests.exceptions.RequestException:
            return False
    
    def create_story(self, epic_id, title, acceptance_criteria):
        try:
            url = f"{self.jira_url}/rest/api/3/issue"
            
            epic_response = requests.get(
                f"{self.jira_url}/rest/api/3/issue/{epic_id}",
                auth=self.auth,
                headers=self.headers
            )
            epic_data = epic_response.json()
            project_key = epic_data['fields']['project']['key']
            
            data = {
                'fields': {
                    'project': {'key': project_key},
                    'summary': title,
                    'description': f"Auto-generated story from EPIC {epic_id}",
                    'issuetype': {'name': 'Story'},
                    'customfield_10200': acceptance_criteria
                }
            }
            
            response = requests.post(url, auth=self.auth, headers=self.headers, json=data)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'id': result['key'],
                    'title': title
                }
            
            return None
        except requests.exceptions.RequestException:
            return None
