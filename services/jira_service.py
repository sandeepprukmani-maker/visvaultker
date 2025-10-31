from jira import JIRA
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)

class JiraService:
    def __init__(self, jira_url, username, password):
        """Initialize Jira service with credentials"""
        self.jira_url = jira_url
        self.jira_username = username
        self.jira_password = password
        self.jira = None
        
        # Check credentials are configured
        self._check_configured()
        
        # Connect to Jira
        self._connect()
        
        # Test connection
        self._test_connection()
    
    def _check_configured(self):
        """Check if Jira credentials are configured"""
        if not self.jira_url or not self.jira_username or not self.jira_password:
            raise Exception("Jira credentials not configured. Please set JIRA_URL, JIRA_USERNAME, and JIRA_PASSWORD environment variables.")
    
    def _connect(self):
        """Establish connection to Jira"""
        try:
            options = {'server': self.jira_url, 'verify': True}
            self.jira = JIRA(options=options, basic_auth=(self.jira_username, self.jira_password))
        except Exception as e:
            logging.error(f"Failed to connect to Jira: {e}")
            raise Exception(f"Failed to connect to Jira: {e}")
    
    def _test_connection(self):
        """Test Jira connection"""
        try:
            myself = self.jira.myself()
            logging.info(f"Successfully authenticated to Jira as {myself.get('displayName', 'unknown')}")
        except Exception as e:
            logging.error(f"Jira authentication failed: {e}")
            raise Exception(f"Jira authentication failed: {e}")
    
    def get_epic(self, epic_key):
        """Get EPIC details from Jira"""
        try:
            issue = self.jira.issue(epic_key)
            fields = issue.fields
            
            # Extract description - handle both string and ADF (Atlassian Document Format)
            description_text = self._extract_text_from_description(fields.description)
            
            # Get comments if available
            comments = getattr(fields, 'comment', None)
            comments_text = ''
            if comments and hasattr(comments, 'comments'):
                comments_text = '\n'.join([
                    f"{getattr(c, 'author', 'Unknown')}: {getattr(c, 'body', '')}"
                    for c in comments.comments
                ])
            
            epic_info = {
                'id': issue.key,
                'title': getattr(fields, 'summary', ''),
                'description': description_text,
                'status': fields.status.name if hasattr(fields, 'status') else 'Unknown',
                'comments': comments_text
            }
            
            return epic_info
        except Exception as e:
            logging.error(f"Failed to fetch EPIC {epic_key}: {e}")
            return None
    
    def get_epic_stories(self, epic_key):
        """Fetch all stories linked to an EPIC"""
        try:
            # Use JQL to find stories with this epic as parent
            jql = f'parent={epic_key}'
            issues = self.jira.search_issues(jql, maxResults=100)
            
            stories = []
            for issue in issues:
                fields = issue.fields
                description_text = self._extract_text_from_description(fields.description)
                
                stories.append({
                    'id': issue.key,
                    'title': getattr(fields, 'summary', ''),
                    'description': description_text,
                    'status': fields.status.name if hasattr(fields, 'status') else 'Unknown',
                    'current_ac': self._extract_acceptance_criteria(description_text)
                })
            
            return stories
        except Exception as e:
            logging.error(f"Failed to fetch stories for EPIC {epic_key}: {e}")
            return []
    
    def _extract_text_from_description(self, description):
        """Extract plain text from description (handles ADF format)"""
        if not description:
            return ''
        
        # If description is already a string, return it
        if isinstance(description, str):
            return description
        
        # If description is ADF (Atlassian Document Format), extract text
        if isinstance(description, dict):
            return self._extract_text_from_adf(description)
        
        return str(description)
    
    def _extract_text_from_adf(self, adf_content):
        """Recursively extract text from ADF (Atlassian Document Format)"""
        if not isinstance(adf_content, dict):
            return str(adf_content)
        
        text_parts = []
        
        # Handle text nodes
        if adf_content.get('type') == 'text':
            return adf_content.get('text', '')
        
        # Handle paragraph and other content nodes
        if 'content' in adf_content:
            for item in adf_content['content']:
                text_parts.append(self._extract_text_from_adf(item))
        
        return ' '.join(text_parts)
    
    def _extract_acceptance_criteria(self, description):
        """Extract acceptance criteria from Jira description if present"""
        if not description:
            return None
        
        description_lower = description.lower()
        ac_markers = ['acceptance criteria', 'ac:', 'given/when/then', 'given:', 'when:', 'then:']
        
        for marker in ac_markers:
            if marker in description_lower:
                return description
        
        return None
    
    def update_story_description(self, story_id, new_description):
        """Update a Jira story's description with new acceptance criteria"""
        try:
            issue = self.jira.issue(story_id)
            issue.update(fields={'description': new_description})
            logging.info(f"Successfully updated story {story_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to update story {story_id}: {e}")
            return False
    
    def update_story_ac(self, story_id, acceptance_criteria):
        """Update a Jira story's acceptance criteria"""
        return self.update_story_description(story_id, acceptance_criteria)
    
    def create_story(self, epic_key, title, description):
        """Create a new story under an EPIC"""
        try:
            # Get the epic to extract project info
            epic = self.jira.issue(epic_key)
            project_key = epic.fields.project.key
            
            # Create the new story
            new_issue = self.jira.create_issue(
                project=project_key,
                summary=title,
                description=description,
                issuetype={'name': 'Story'},
                parent={'key': epic_key}
            )
            
            logging.info(f"Successfully created story {new_issue.key} under epic {epic_key}")
            return {
                'id': new_issue.key,
                'title': title
            }
        except Exception as e:
            logging.error(f"Failed to create story under epic {epic_key}: {e}")
            return None
