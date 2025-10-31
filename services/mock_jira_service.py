class MockJiraService:
    """Mock Jira service for demo/testing when credentials are not configured"""
    
    def get_epic(self, epic_id):
        """Return mock EPIC data"""
        mock_epics = {
            'DEMO-100': {
                'id': 'DEMO-100',
                'title': 'User Authentication System',
                'description': 'Implement a complete user authentication system with login, registration, password reset, and session management. The system should support email verification, secure password storage, and remember me functionality.',
                'status': 'In Progress'
            },
            'DEMO-200': {
                'id': 'DEMO-200',
                'title': 'E-commerce Shopping Cart',
                'description': 'Build a shopping cart system that allows users to add products, update quantities, apply discount codes, and proceed to checkout. Include features for saving cart items, calculating totals with taxes, and handling multiple payment methods.',
                'status': 'To Do'
            },
            'DEMO-300': {
                'id': 'DEMO-300',
                'title': 'Real-time Notification System',
                'description': 'Create a real-time notification system that alerts users about important events via email, SMS, and in-app notifications. Support notification preferences, batching, and delivery tracking.',
                'status': 'In Progress'
            }
        }
        
        # Return specific epic or default
        if epic_id in mock_epics:
            return mock_epics[epic_id]
        else:
            # Return a generic epic for any ID
            return {
                'id': epic_id,
                'title': f'Sample EPIC: {epic_id}',
                'description': f'This is a demo EPIC ({epic_id}) with sample data. Configure Jira credentials in Settings to connect to your real Jira instance. This EPIC demonstrates a feature implementation that requires user stories and acceptance criteria.',
                'status': 'To Do'
            }
    
    def get_epic_stories(self, epic_id):
        """Return mock stories for an EPIC"""
        # Return empty stories list for mock data
        # The AI will generate new stories based on the EPIC description
        return []
    
    def update_story_description(self, story_id, new_description):
        """Mock update - always returns success"""
        return True
