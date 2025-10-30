from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
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

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from models import User, Epic, Story, GeneratedAC, AuditLog
from services.jira_service import JiraService
from services.ai_service import AIService
from utils import encrypt_password, decrypt_password

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/auth/callback')
def auth_callback():
    import jwt
    import requests as req
    
    token = request.headers.get('X-Replit-User-Id')
    if not token:
        return redirect(url_for('login'))
    
    user_data = jwt.decode(token, options={"verify_signature": False})
    email = user_data.get('email', f"{user_data.get('id')}@replit.user")
    
    user = User.query.filter_by(replit_user_id=user_data.get('id')).first()
    if not user:
        user = User(
            email=email,
            name=user_data.get('name', 'User'),
            replit_user_id=user_data.get('id')
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        try:
            data = request.json
            current_user.jira_url = data.get('jira_url')
            current_user.jira_username = data.get('jira_username')
            
            password = data.get('jira_password')
            if password:
                encrypted = encrypt_password(password)
                if not encrypted:
                    return jsonify({'error': 'Failed to encrypt password'}), 500
                current_user.jira_password = encrypted
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': f'Failed to save settings: {str(e)}'}), 500
    
    return jsonify({
        'jira_url': current_user.jira_url or '',
        'jira_username': current_user.jira_username or '',
        'has_password': bool(current_user.jira_password)
    })

@app.route('/api/epic/<epic_id>', methods=['GET'])
@login_required
def fetch_epic(epic_id):
    if not current_user.jira_url or not current_user.jira_username or not current_user.jira_password:
        return jsonify({
            'error': 'Jira credentials not configured. Please configure your Jira settings first.',
            'needs_settings': True
        }), 400
    
    try:
        jira = JiraService(
            current_user.jira_url,
            current_user.jira_username,
            decrypt_password(current_user.jira_password)
        )
        epic_data = jira.get_epic(epic_id)
        
        if not epic_data:
            return jsonify({'error': 'Invalid EPIC ID'}), 404
        
        if not epic_data.get('description'):
            return jsonify({'error': 'EPIC has no description or is invalid.'}), 400
        
        epic = Epic.query.filter_by(jira_epic_id=epic_id, user_id=current_user.id).first()
        if not epic:
            epic = Epic(
                user_id=current_user.id,
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
@login_required
def generate_acceptance_criteria(epic_id):
    try:
        epic = Epic.query.get_or_404(epic_id)
        if epic.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
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

@app.route('/api/ac/<int:ac_id>/edit-manual', methods=['POST'])
@login_required
def edit_ac_manual(ac_id):
    try:
        gen_ac = GeneratedAC.query.get_or_404(ac_id)
        epic = Epic.query.get(gen_ac.epic_id)
        
        if epic.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
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
@login_required
def edit_ac_chat(ac_id):
    try:
        gen_ac = GeneratedAC.query.get_or_404(ac_id)
        epic = Epic.query.get(gen_ac.epic_id)
        
        if epic.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
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
@login_required
def update_stories():
    if not current_user.jira_url or not current_user.jira_username or not current_user.jira_password:
        return jsonify({'error': 'Jira credentials not configured'}), 400
    
    try:
        data = request.json
        story_updates = data.get('updates', [])
        
        jira = JiraService(
            current_user.jira_url,
            current_user.jira_username,
            decrypt_password(current_user.jira_password)
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
                    user_id=current_user.id,
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
@login_required
def create_story():
    if not current_user.jira_url or not current_user.jira_username or not current_user.jira_password:
        return jsonify({'error': 'Jira credentials not configured'}), 400
    
    try:
        data = request.json
        epic_id = data.get('epic_id')
        ac_id = data.get('ac_id')
        
        epic = Epic.query.get(epic_id)
        gen_ac = GeneratedAC.query.get(ac_id)
        
        if epic.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        jira = JiraService(
            current_user.jira_url,
            current_user.jira_username,
            decrypt_password(current_user.jira_password)
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
                user_id=current_user.id,
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
@login_required
def get_audit_logs():
    logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(AuditLog.timestamp.desc()).limit(50).all()
    
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
