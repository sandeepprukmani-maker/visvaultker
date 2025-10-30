from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)

from database import db
db.init_app(app)

from models import User, Epic, Story, GeneratedAC, AuditLog
from services.jira_service import JiraService
from services.mock_jira_service import MockJiraService
from services.ai_service import AIService
from utils import encrypt_password, decrypt_password

# Use mock Jira by default (no real Jira needed)
USE_MOCK_JIRA = True

def get_or_create_default_user():
    """Get or create a default user for the application"""
    user = User.query.first()
    if not user:
        user = User(
            email='default@jira-ac-automation.com',
            name='Default User'
        )
        db.session.add(user)
        db.session.commit()
    return user

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    user = get_or_create_default_user()
    if request.method == 'POST':
        try:
            data = request.json
            user.jira_url = data.get('jira_url')
            user.jira_username = data.get('jira_username')
            
            password = data.get('jira_password')
            if password:
                encrypted = encrypt_password(password)
                if not encrypted:
                    return jsonify({'error': 'Failed to encrypt password'}), 500
                user.jira_password = encrypted
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': f'Failed to save settings: {str(e)}'}), 500
    
    return jsonify({
        'jira_url': user.jira_url or '',
        'jira_username': user.jira_username or '',
        'has_password': bool(user.jira_password)
    })

@app.route('/api/epic/<epic_id>', methods=['GET'])
def fetch_epic(epic_id):
    user = get_or_create_default_user()
    
    try:
        # Use mock Jira service by default
        if USE_MOCK_JIRA:
            jira = MockJiraService()
        else:
            if not user.jira_url or not user.jira_username or not user.jira_password:
                return jsonify({
                    'error': 'Jira credentials not configured. Please configure your Jira settings first.',
                    'needs_settings': True
                }), 400
            jira = JiraService(
                user.jira_url,
                user.jira_username,
                decrypt_password(user.jira_password)
            )
        epic_data = jira.get_epic(epic_id)
        
        if not epic_data:
            return jsonify({'error': 'Invalid EPIC ID'}), 404
        
        if not epic_data.get('description'):
            return jsonify({'error': 'EPIC has no description or is invalid.'}), 400
        
        epic = Epic.query.filter_by(jira_epic_id=epic_id, user_id=user.id).first()
        if not epic:
            epic = Epic(
                user_id=user.id,
                jira_epic_id=epic_id,
                title=epic_data['title'],
                description=epic_data['description']
            )
            db.session.add(epic)
        else:
            epic.title = epic_data['title']
            epic.description = epic_data['description']
        
        db.session.commit()
        
        stories = jira.get_epic_stories(epic_id)
        for story_data in stories:
            story = Story.query.filter_by(jira_story_id=story_data['id'], epic_id=epic.id).first()
            if not story:
                story = Story(
                    epic_id=epic.id,
                    jira_story_id=story_data['id'],
                    title=story_data['title'],
                    description=story_data.get('description', ''),
                    current_ac=story_data.get('acceptance_criteria', '')
                )
                db.session.add(story)
            else:
                story.title = story_data['title']
                story.description = story_data.get('description', '')
                story.current_ac = story_data.get('acceptance_criteria', '')
        
        db.session.commit()
        
        return jsonify({
            'epic': {
                'id': epic.id,
                'jira_id': epic.jira_epic_id,
                'title': epic.title,
                'description': epic.description
            },
            'stories': [{
                'id': s.id,
                'jira_id': s.jira_story_id,
                'title': s.title,
                'description': s.description,
                'current_ac': s.current_ac
            } for s in Story.query.filter_by(epic_id=epic.id).all()]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/<int:epic_id>/generate-ac', methods=['POST'])
def generate_acceptance_criteria(epic_id):
    try:
        epic = Epic.query.get_or_404(epic_id)
        
        ai_service = AIService()
        generated_acs = ai_service.generate_acceptance_criteria(
            epic.title,
            epic.description
        )
        
        for ac_data in generated_acs:
            gen_ac = GeneratedAC(
                epic_id=epic.id,
                story_title=ac_data['story_title'],
                ac_text='\n'.join(ac_data['criteria']),
                format='gherkin'
            )
            db.session.add(gen_ac)
        
        db.session.commit()
        
        return jsonify({
            'generated_acs': [{
                'id': ac.id,
                'story_title': ac.story_title,
                'ac_text': ac.ac_text,
                'format': ac.format
            } for ac in GeneratedAC.query.filter_by(epic_id=epic.id).all()]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/epic/<int:epic_id>/analyze-coverage', methods=['POST'])
def analyze_coverage(epic_id):
    try:
        epic = Epic.query.get_or_404(epic_id)
        stories = Story.query.filter_by(epic_id=epic.id).all()
        
        existing_stories = [{
            'id': s.id,
            'jira_id': s.jira_story_id,
            'title': s.title,
            'description': s.description,
            'current_ac': s.current_ac or ''
        } for s in stories]
        
        ai_service = AIService()
        coverage_analysis = ai_service.analyze_epic_coverage(
            epic.title,
            epic.description,
            existing_stories
        )
        
        GeneratedAC.query.filter_by(epic_id=epic.id).delete()
        
        for update in coverage_analysis.get('updated_stories', []):
            story_id = next((s['id'] for s in existing_stories if s['jira_id'] == update.get('jira_id')), None)
            gen_ac = GeneratedAC(
                epic_id=epic.id,
                story_id=story_id,
                story_title=update['story_title'],
                ac_text=update['suggested_ac'],
                format='gherkin'
            )
            db.session.add(gen_ac)
        
        for new_story in coverage_analysis.get('new_story_suggestions', []):
            gen_ac = GeneratedAC(
                epic_id=epic.id,
                story_title=new_story['story_title'],
                ac_text=new_story['suggested_ac'],
                format='gherkin'
            )
            db.session.add(gen_ac)
        
        db.session.commit()
        
        return jsonify({
            'coverage_analysis': coverage_analysis,
            'generated_acs': [{
                'id': ac.id,
                'story_id': ac.story_id,
                'story_title': ac.story_title,
                'ac_text': ac.ac_text,
                'format': ac.format,
                'is_new': ac.story_id is None
            } for ac in GeneratedAC.query.filter_by(epic_id=epic.id).all()]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/story/<int:story_id>/check-alignment', methods=['POST'])
def check_story_alignment(story_id):
    try:
        story = Story.query.get_or_404(story_id)
        epic = Epic.query.get_or_404(story.epic_id)
        
        ai_service = AIService()
        alignment_result = ai_service.check_story_alignment(
            epic.title,
            epic.description,
            story.title,
            story.current_ac or ''
        )
        
        return jsonify({
            'alignment': alignment_result,
            'story': {
                'id': story.id,
                'title': story.title,
                'current_ac': story.current_ac
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/story/<int:story_id>/update-ac', methods=['POST'])
def update_story_ac(story_id):
    try:
        story = Story.query.get_or_404(story_id)
        data = request.json
        new_ac = data.get('ac_text')
        
        if not new_ac:
            return jsonify({'error': 'No acceptance criteria provided'}), 400
        
        story.current_ac = new_ac
        db.session.commit()
        
        return jsonify({
            'success': True,
            'story': {
                'id': story.id,
                'title': story.title,
                'current_ac': story.current_ac
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ac/<int:ac_id>/edit-manual', methods=['POST'])
def edit_ac_manual(ac_id):
    try:
        gen_ac = GeneratedAC.query.get_or_404(ac_id)
        epic = Epic.query.get(gen_ac.epic_id)
        
        data = request.json
        gen_ac.ac_text = data.get('ac_text', gen_ac.ac_text)
        gen_ac.story_title = data.get('story_title', gen_ac.story_title)
        db.session.commit()
        
        return jsonify({'success': True, 'ac': {
            'id': gen_ac.id,
            'story_title': gen_ac.story_title,
            'ac_text': gen_ac.ac_text
        }})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ac/<int:ac_id>/edit-chat', methods=['POST'])
def edit_ac_chat(ac_id):
    try:
        gen_ac = GeneratedAC.query.get_or_404(ac_id)
        epic = Epic.query.get(gen_ac.epic_id)
        
        data = request.json
        user_message = data.get('message')
        
        ai_service = AIService()
        refined_ac = ai_service.refine_acceptance_criteria(
            gen_ac.ac_text,
            user_message
        )
        
        gen_ac.ac_text = refined_ac
        db.session.commit()
        
        return jsonify({'success': True, 'ac': {
            'id': gen_ac.id,
            'story_title': gen_ac.story_title,
            'ac_text': gen_ac.ac_text
        }})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stories/update', methods=['POST'])
def update_stories():
    user = get_or_create_default_user()
    
    try:
        data = request.json
        story_updates = data.get('updates', [])
        
        # Use mock Jira service by default
        if USE_MOCK_JIRA:
            jira = MockJiraService()
        else:
            if not user.jira_url or not user.jira_username or not user.jira_password:
                return jsonify({'error': 'Jira credentials not configured'}), 400
            jira = JiraService(
                user.jira_url,
                user.jira_username,
                decrypt_password(user.jira_password)
            )
        
        results = []
        for update in story_updates:
            story_id = update['story_id']
            ac_id = update['ac_id']
            
            story = Story.query.get(story_id)
            gen_ac = GeneratedAC.query.get(ac_id)
            
            old_ac = story.current_ac
            new_ac = gen_ac.ac_text
            
            success = jira.update_story_ac(story.jira_story_id, new_ac)
            
            if success:
                story.current_ac = new_ac
                
                audit = AuditLog(
                    user_id=user.id,
                    epic_id=story.epic_id,
                    story_id=story.id,
                    before_text=old_ac,
                    after_text=new_ac,
                    timestamp=datetime.utcnow()
                )
                db.session.add(audit)
                
                results.append({
                    'story_id': story_id,
                    'success': True
                })
            else:
                results.append({
                    'story_id': story_id,
                    'success': False,
                    'error': 'Failed to update Jira'
                })
        
        db.session.commit()
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stories/create', methods=['POST'])
def create_story():
    user = get_or_create_default_user()
    
    try:
        data = request.json
        epic_id = data.get('epic_id')
        ac_id = data.get('ac_id')
        
        epic = Epic.query.get(epic_id)
        gen_ac = GeneratedAC.query.get(ac_id)
        
        # Use mock Jira service by default
        if USE_MOCK_JIRA:
            jira = MockJiraService()
        else:
            if not user.jira_url or not user.jira_username or not user.jira_password:
                return jsonify({'error': 'Jira credentials not configured'}), 400
            jira = JiraService(
                user.jira_url,
                user.jira_username,
                decrypt_password(user.jira_password)
            )
        
        new_story_data = jira.create_story(
            epic.jira_epic_id,
            gen_ac.story_title,
            gen_ac.ac_text
        )
        
        if new_story_data:
            story = Story(
                epic_id=epic.id,
                jira_story_id=new_story_data['id'],
                title=gen_ac.story_title,
                description='',
                current_ac=gen_ac.ac_text
            )
            db.session.add(story)
            
            audit = AuditLog(
                user_id=user.id,
                epic_id=epic.id,
                story_id=story.id,
                before_text='',
                after_text=gen_ac.ac_text,
                timestamp=datetime.utcnow()
            )
            db.session.add(audit)
            db.session.commit()
            
            return jsonify({'success': True, 'story': {
                'id': story.id,
                'jira_id': story.jira_story_id,
                'title': story.title
            }})
        else:
            return jsonify({'error': 'Failed to create story in Jira'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audit-logs', methods=['GET'])
def get_audit_logs():
    user = get_or_create_default_user()
    logs = AuditLog.query.filter_by(user_id=user.id).order_by(AuditLog.timestamp.desc()).limit(50).all()
    
    return jsonify({
        'logs': [{
            'id': log.id,
            'epic_id': log.epic_id,
            'story_id': log.story_id,
            'before_text': log.before_text,
            'after_text': log.after_text,
            'timestamp': log.timestamp.isoformat()
        } for log in logs]
    })

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
