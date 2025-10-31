from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')

CORS(app)

from services.ai_service import AIService
from services.jira_service import JiraService

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    """Handle Jira configuration settings"""
    if request.method == 'POST':
        try:
            data = request.json
            session['jira_url'] = data.get('jira_url')
            session['jira_username'] = data.get('jira_username')
            session['jira_password'] = data.get('jira_password')
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': f'Failed to save settings: {str(e)}'}), 500
    
    return jsonify({
        'jira_url': session.get('jira_url', ''),
        'jira_username': session.get('jira_username', ''),
        'has_password': bool(session.get('jira_password'))
    })

@app.route('/api/epic/<epic_id>', methods=['GET'])
def fetch_epic(epic_id):
    """Fetch EPIC from Jira and generate acceptance criteria using OpenAI"""
    try:
        jira_url = session.get('jira_url')
        jira_username = session.get('jira_username')
        jira_password = session.get('jira_password')
        
        # Use mock Jira if credentials are not configured
        if not all([jira_url, jira_username, jira_password]):
            from services.mock_jira_service import MockJiraService
            jira = MockJiraService()
        else:
            jira = JiraService(jira_url, jira_username, jira_password)
        epic_data = jira.get_epic(epic_id)
        
        if not epic_data:
            return jsonify({'error': 'Invalid EPIC ID or failed to fetch from Jira'}), 404
        
        if not epic_data.get('description'):
            return jsonify({'error': 'EPIC has no description.'}), 400
        
        ai_service = AIService()
        
        if not ai_service.client:
            return jsonify({
                'error': 'OpenAI client not configured. Please check your OAuth settings or API key in the .env file.',
                'needs_settings': True
            }), 400
        
        acceptance_criteria = ai_service.generate_acceptance_criteria(
            epic_data['title'],
            epic_data['description']
        )
        
        existing_stories = jira.get_epic_stories(epic_id)
        
        return jsonify({
            'epic': epic_data,
            'existing_stories': existing_stories,
            'generated_stories': acceptance_criteria,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to process EPIC: {str(e)}'}), 500

@app.route('/api/test-oauth', methods=['GET'])
def test_oauth():
    """Test endpoint to verify OAuth configuration"""
    try:
        ai_service = AIService()
        
        use_oauth = os.environ.get('USE_OAUTH_FOR_OPENAI', 'false').lower() == 'true'
        
        status = {
            'oauth_enabled': use_oauth,
            'client_initialized': ai_service.client is not None,
            'authentication_mode': 'OAuth' if use_oauth else 'Direct API Key'
        }
        
        if use_oauth:
            required_vars = [
                'OAUTH_TOKEN_URL',
                'OAUTH_CLIENT_ID',
                'OAUTH_CLIENT_SECRET',
                'OAUTH_GRANT_TYPE',
                'OAUTH_SCOPE'
            ]
            status['oauth_config'] = {
                var: 'Set' if os.environ.get(var) else 'Missing'
                for var in required_vars
            }
            if os.environ.get('GPT_BASE_URL'):
                status['custom_base_url'] = 'Configured'
        else:
            status['openai_api_key'] = 'Set' if os.environ.get('OPENAI_API_KEY') else 'Missing'
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refine-ac', methods=['POST'])
def refine_acceptance_criteria():
    """Refine acceptance criteria based on user instruction"""
    try:
        data = request.json
        current_ac = data.get('current_ac')
        instruction = data.get('instruction')
        
        if not current_ac or not instruction:
            return jsonify({'error': 'Missing current_ac or instruction'}), 400
        
        ai_service = AIService()
        
        if not ai_service.client:
            return jsonify({'error': 'OpenAI client not configured'}), 400
        
        refined_ac = ai_service.refine_acceptance_criteria(current_ac, instruction)
        
        return jsonify({
            'refined_ac': refined_ac,
            'refined_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to refine AC: {str(e)}'}), 500

@app.route('/api/update-jira-story', methods=['POST'])
def update_jira_story():
    """Update a Jira story with new acceptance criteria"""
    try:
        data = request.json
        story_id = data.get('story_id')
        new_ac = data.get('acceptance_criteria')
        
        if not story_id or not new_ac:
            return jsonify({'error': 'Missing story_id or acceptance_criteria'}), 400
        
        jira_url = session.get('jira_url')
        jira_username = session.get('jira_username')
        jira_password = session.get('jira_password')
        
        if not all([jira_url, jira_username, jira_password]):
            return jsonify({'error': 'Jira credentials not configured'}), 400
        
        jira = JiraService(jira_url, jira_username, jira_password)
        success = jira.update_story_description(story_id, new_ac)
        
        if success:
            return jsonify({'success': True, 'message': f'Story {story_id} updated successfully'})
        else:
            return jsonify({'error': 'Failed to update Jira story'}), 500
        
    except Exception as e:
        return jsonify({'error': f'Failed to update story: {str(e)}'}), 500

with app.app_context():
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
