class MockJiraService:
    """Mock Jira service that provides sample data for testing"""
    
    def __init__(self):
        self.epics = {
            'DEMO-100': {
                'id': 'DEMO-100',
                'title': 'E-commerce Checkout Flow Redesign',
                'description': '''As a product team, we want to redesign the checkout flow to improve conversion rates and user experience.

The current checkout process has multiple pain points:
- Too many steps causing cart abandonment
- Unclear shipping cost calculation
- Limited payment options
- No guest checkout option

Goals:
- Reduce checkout steps from 5 to 3
- Add guest checkout functionality
- Integrate multiple payment providers (Stripe, PayPal, Apple Pay)
- Real-time shipping cost calculation
- Mobile-responsive design
- Save payment methods for returning customers'''
            },
            'DEMO-101': {
                'id': 'DEMO-101',
                'title': 'User Authentication System',
                'description': '''Implement a secure user authentication system with social login options.

Requirements:
- Email/password authentication
- Social login (Google, Facebook, Apple)
- Two-factor authentication
- Password reset functionality
- Session management
- Remember me option
- Account verification via email'''
            },
            'DEMO-102': {
                'id': 'DEMO-102',
                'title': 'Mobile App Dashboard',
                'description': '''Create a mobile dashboard that provides users with real-time analytics and insights.

Features needed:
- Real-time data visualization
- Customizable widgets
- Export data to PDF/CSV
- Dark mode support
- Offline mode with sync
- Push notifications for alerts
- Multi-language support'''
            }
        }
        
        self.stories = {
            'DEMO-100': [
                {
                    'id': 'DEMO-200',
                    'title': 'Implement single-page checkout',
                    'description': 'Create a single-page checkout with all steps visible',
                    'status': 'To Do',
                    'acceptance_criteria': ''
                },
                {
                    'id': 'DEMO-201',
                    'title': 'Add guest checkout option',
                    'description': 'Allow users to checkout without creating an account',
                    'status': 'To Do',
                    'acceptance_criteria': ''
                },
                {
                    'id': 'DEMO-202',
                    'title': 'Integrate Stripe payment gateway',
                    'description': 'Add Stripe as a payment option',
                    'status': 'In Progress',
                    'acceptance_criteria': 'Given a user selects Stripe\nWhen they enter valid card details\nThen payment should be processed successfully'
                }
            ],
            'DEMO-101': [
                {
                    'id': 'DEMO-210',
                    'title': 'Create email/password login',
                    'description': 'Basic authentication with email and password',
                    'status': 'To Do',
                    'acceptance_criteria': ''
                },
                {
                    'id': 'DEMO-211',
                    'title': 'Add Google OAuth integration',
                    'description': 'Allow users to login with Google',
                    'status': 'To Do',
                    'acceptance_criteria': ''
                }
            ],
            'DEMO-102': [
                {
                    'id': 'DEMO-220',
                    'title': 'Create dashboard layout',
                    'description': 'Design and implement the dashboard grid layout',
                    'status': 'To Do',
                    'acceptance_criteria': ''
                }
            ]
        }
    
    def get_epic(self, epic_id):
        """Get epic by ID"""
        epic = self.epics.get(epic_id)
        if not epic:
            return None
        return epic.copy()
    
    def get_epic_stories(self, epic_id):
        """Get all stories for an epic"""
        stories = self.stories.get(epic_id, [])
        return [story.copy() for story in stories]
    
    def update_story_ac(self, story_id, acceptance_criteria):
        """Update acceptance criteria for a story"""
        # Find and update the story in mock data
        for epic_stories in self.stories.values():
            for story in epic_stories:
                if story['id'] == story_id:
                    story['acceptance_criteria'] = acceptance_criteria
                    return True
        return False
    
    def create_story(self, epic_id, title, acceptance_criteria):
        """Create a new story in an epic"""
        if epic_id not in self.stories:
            return None
        
        # Generate new story ID
        story_count = len(self.stories[epic_id])
        new_id = f"{epic_id.split('-')[0]}-{300 + story_count}"
        
        new_story = {
            'id': new_id,
            'title': title,
            'description': f'Auto-generated story from EPIC {epic_id}',
            'status': 'To Do',
            'acceptance_criteria': acceptance_criteria
        }
        
        self.stories[epic_id].append(new_story)
        
        return {
            'id': new_id,
            'title': title
        }
