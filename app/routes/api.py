"""
API Routes
RESTful endpoints for browser automation with security and validation
"""
import os
import json
import logging
import threading
from queue import Queue
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context, current_app
from app.models import db, ExecutionHistory, GeneratedScript, CredentialVault
from app.services.engine_orchestrator import EngineOrchestrator
from app.middleware.security import (
    require_api_key,
    rate_limit,
    validate_engine_type,
    validate_instruction,
    sanitize_error_message
)
from app.utils.timeout import run_with_timeout, TimeoutError
from app.utils.credentials import replace_credential_placeholders
from app.utils.db_maintenance import prune_old_executions, get_database_stats

logger = logging.getLogger(__name__)

def save_execution_to_history(instruction, engine_type, headless, result):
    """
    Save execution result to history database
    
    Args:
        instruction: The automation instruction
        engine_type: The engine used (browser_use)
        headless: Whether execution was headless
        result: The execution result dictionary
    """
    try:
        # Handle screenshot paths - convert array to JSON or handle single path
        screenshot_paths = result.get('screenshot_paths', [])
        screenshot_path_json = None
        
        if screenshot_paths and isinstance(screenshot_paths, list):
            screenshot_path_json = json.dumps(screenshot_paths)
        elif result.get('screenshot_path'):
            # Handle legacy single screenshot path
            screenshot_path_json = json.dumps([result.get('screenshot_path')])
        
        # Map 'steps' to 'history' for display - BrowserAgent returns steps, not history
        execution_history = result.get('history') or result.get('steps', [])
        
        history_entry = ExecutionHistory(
            prompt=instruction,
            engine=engine_type,
            headless=headless,
            success=result.get('success', False),
            error_message=result.get('error') or result.get('message') if not result.get('success') else None,
            screenshot_path=screenshot_path_json,
            execution_logs=json.dumps(execution_history) if execution_history else None,
            iterations=result.get('iterations'),
            execution_time=result.get('execution_time')
        )
        
        db.session.add(history_entry)
        db.session.flush()  # Flush to get the history_entry.id
        
        # Save generated Python code if available
        python_code = result.get('playwright_code')
        if python_code:
            import hashlib
            script_hash = hashlib.sha256(python_code.encode()).hexdigest()
            
            generated_script = GeneratedScript(
                execution_id=history_entry.id,
                python_code=python_code,
                script_hash=script_hash,
                is_healed=False,
                healing_iterations=0
            )
            db.session.add(generated_script)
            logger.info(f"💾 Saved generated Python script (hash: {script_hash[:8]}...)")
        
        # Save healed code if available
        if result.get('healed_code'):
            import hashlib
            healed_code = result.get('healed_code')
            script_hash = hashlib.sha256(healed_code.encode()).hexdigest()
            
            healed_script = GeneratedScript(
                execution_id=history_entry.id,
                python_code=healed_code,
                script_hash=script_hash,
                is_healed=True,
                healing_iterations=result.get('healing_iterations', 1)
            )
            db.session.add(healed_script)
            logger.info(f"💾 Saved healed Python script (hash: {script_hash[:8]}...)")
        
        db.session.commit()
        
        logger.info(f"💾 Saved execution to history (ID: {history_entry.id})")
        return history_entry.id
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to save execution to history: {str(e)}", exc_info=True)
        return None


def create_api_routes(orchestrator: EngineOrchestrator) -> Blueprint:
    """
    Create API routes blueprint
    
    Args:
        orchestrator: Engine orchestrator instance
        
    Returns:
        Flask Blueprint with all routes
    """
    api = Blueprint('api', __name__)
    
    @api.route('/')
    def index():
        """Render dashboard page"""
        return render_template('dashboard.html')
    
    @api.route('/history')
    def history():
        """Render history page"""
        return render_template('history.html')
    
    @api.route('/configuration')
    def configuration():
        """Render configuration page"""
        return render_template('configuration.html')
    
    @api.route('/credentials')
    def credentials():
        """Render credentials manager page"""
        return render_template('credentials.html')
    
    @api.route('/api/execute', methods=['POST'])
    @require_api_key
    @rate_limit
    def execute_instruction():
        """Execute a browser automation instruction"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request',
                    'message': 'Request body must be valid JSON'
                }), 400
            
            instruction = data.get('instruction', '').strip()
            engine_type = data.get('engine', 'browser_use')
            headless = data.get('headless', False)
            
            is_valid, error_msg = validate_instruction(instruction)
            if not is_valid:
                logger.warning(f"⚠️  Invalid instruction: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid instruction',
                    'message': error_msg
                }), 400
            
            is_valid, error_msg = validate_engine_type(engine_type)
            if not is_valid:
                logger.warning(f"⚠️  Invalid engine type: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid engine type',
                    'message': error_msg
                }), 400
            
            if not isinstance(headless, bool):
                return jsonify({
                    'success': False,
                    'error': 'Invalid parameter',
                    'message': 'headless must be a boolean'
                }), 400
            
            # Store original instruction for database (with placeholders)
            original_instruction = instruction
            
            # Replace credential placeholders with actual values
            try:
                processed_instruction, credentials_used = replace_credential_placeholders(instruction)
                if credentials_used:
                    logger.info(f"🔐 Using {len(credentials_used)} credential(s): {', '.join(credentials_used)}")
            except ValueError as e:
                logger.warning(f"⚠️  Credential replacement failed: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Missing credentials',
                    'message': str(e)
                }), 400
            
            logger.info("="*80)
            logger.info("📨 NEW AUTOMATION REQUEST")
            logger.info(f"📝 Instruction: {original_instruction}")
            logger.info(f"🔧 Engine: {engine_type}")
            logger.info(f"👁️  Headless: {headless}")
            logger.info(f"🌐 Client: {request.remote_addr}")
            logger.info("="*80)
            
            logger.info("🚀 Starting automation execution...")
            
            try:
                result = run_with_timeout(
                    orchestrator.execute_instruction,
                    300,
                    processed_instruction,
                    engine_type,
                    headless,
                    None  # progress_callback
                )
            except TimeoutError as e:
                logger.error(f"⏱️  Automation timed out: {str(e)}")
                orchestrator.cleanup_after_timeout(engine_type, headless)
                return jsonify({
                    'success': False,
                    'error': 'Timeout',
                    'message': 'Operation timed out. The task took longer than 5 minutes to complete.',
                    'timeout': True
                }), 408
            
            if result.get('success'):
                logger.info(f"✅ Automation completed successfully in {result.get('iterations', 0)} steps")
            else:
                logger.error(f"❌ Automation failed: {result.get('error', 'Unknown error')}")
            
            save_execution_to_history(original_instruction, engine_type, headless, result)
            
            logger.info("="*80)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"💥 Exception in execute_instruction: {str(e)}", exc_info=True)
            
            user_message = sanitize_error_message(e)
            
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': user_message
            }), 500
    
    @api.route('/api/execute/stream', methods=['POST'])
    @require_api_key
    @rate_limit
    def execute_instruction_stream():
        """Execute a browser automation instruction with Server-Sent Events streaming"""
        def generate_progress():
            """Generator function for SSE streaming"""
            try:
                data = request.get_json()
                
                if not data:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid request', 'message': 'Request body must be valid JSON'})}\n\n"
                    return
                
                instruction = data.get('instruction', '').strip()
                engine_type = data.get('engine', 'browser_use')
                headless = data.get('headless', False)
                
                # Validation
                is_valid, error_msg = validate_instruction(instruction)
                if not is_valid:
                    logger.warning(f"⚠️  Invalid instruction: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid instruction', 'message': error_msg})}\n\n"
                    return
                
                is_valid, error_msg = validate_engine_type(engine_type)
                if not is_valid:
                    logger.warning(f"⚠️  Invalid engine type: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid engine type', 'message': error_msg})}\n\n"
                    return
                
                if not isinstance(headless, bool):
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid parameter', 'message': 'headless must be a boolean'})}\n\n"
                    return
                
                # Store original instruction for database (with placeholders)
                original_instruction = instruction
                
                # Replace credential placeholders with actual values
                try:
                    processed_instruction, credentials_used = replace_credential_placeholders(instruction)
                    if credentials_used:
                        logger.info(f"🔐 Using {len(credentials_used)} credential(s): {', '.join(credentials_used)}")
                except ValueError as e:
                    logger.warning(f"⚠️  Credential replacement failed: {str(e)}")
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Missing credentials', 'message': str(e)})}\n\n"
                    return
                
                logger.info("="*80)
                logger.info("📨 NEW AUTOMATION REQUEST (STREAMING)")
                logger.info(f"📝 Instruction: {original_instruction}")
                logger.info(f"🔧 Engine: {engine_type}")
                logger.info(f"👁️  Headless: {headless}")
                logger.info(f"🌐 Client: {request.remote_addr}")
                logger.info("="*80)
                
                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Starting automation...'})}\n\n"
                
                # Create a queue for progress updates
                progress_queue = Queue()
                result_holder = {}
                
                # Capture the Flask app object for use in the thread
                app = current_app._get_current_object()
                
                def progress_callback(event_type, data):
                    """Callback function to send progress updates"""
                    progress_queue.put({'type': event_type, 'data': data})
                
                def execute_in_thread():
                    """Execute automation in a separate thread"""
                    try:
                        result = orchestrator.execute_instruction_with_progress(
                            processed_instruction,
                            engine_type,
                            headless,
                            progress_callback
                        )
                        result_holder['result'] = result
                        # Use app context for database operations in thread
                        with app.app_context():
                            save_execution_to_history(original_instruction, engine_type, headless, result)
                        progress_queue.put({'type': 'done', 'result': result})
                    except Exception as e:
                        logger.error(f"💥 Exception in threaded execution: {str(e)}", exc_info=True)
                        result_holder['error'] = str(e)
                        error_result = {
                            'success': False,
                            'error': str(e),
                            'message': sanitize_error_message(e)
                        }
                        # Use app context for database operations in thread
                        with app.app_context():
                            save_execution_to_history(original_instruction, engine_type, headless, error_result)
                        progress_queue.put({'type': 'error', 'error': str(e), 'message': sanitize_error_message(e)})
                
                # Start execution in thread
                execution_thread = threading.Thread(target=execute_in_thread)
                execution_thread.daemon = True
                execution_thread.start()
                
                # Stream progress updates
                while True:
                    event = progress_queue.get()
                    
                    if event['type'] == 'done':
                        # Send final result
                        yield f"data: {json.dumps(event)}\n\n"
                        logger.info("✅ Streaming completed successfully")
                        break
                    elif event['type'] == 'error':
                        # Send error and stop
                        yield f"data: {json.dumps(event)}\n\n"
                        logger.error(f"❌ Streaming failed: {event.get('error')}")
                        break
                    else:
                        # Send progress update
                        yield f"data: {json.dumps(event)}\n\n"
                
                logger.info("="*80)
                
            except Exception as e:
                logger.error(f"💥 Exception in SSE streaming: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': 'Internal error', 'message': sanitize_error_message(e)})}\n\n"
        
        return Response(
            stream_with_context(generate_progress()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    @api.route('/api/tools', methods=['GET'])
    def get_tools():
        """Get available browser tools"""
        try:
            engine_type = request.args.get('engine', 'browser_use')
            
            is_valid, error_msg = validate_engine_type(engine_type)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid engine type',
                    'message': error_msg
                }), 400
            
            tools = orchestrator.get_tools(engine_type)
            
            return jsonify({
                'success': True,
                'tools': tools,
                'engine': engine_type
            })
            
        except Exception as e:
            logger.error(f"Error getting tools: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/reset', methods=['POST'])
    @require_api_key
    def reset_agent():
        """Reset the browser agent"""
        try:
            data = request.get_json() or {}
            engine_type = data.get('engine', 'browser_use')
            
            is_valid, error_msg = validate_engine_type(engine_type)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid engine type',
                    'message': error_msg
                }), 400
            
            orchestrator.reset_agent(engine_type)
            
            return jsonify({
                'success': True,
                'message': 'Agent reset successfully',
                'engine': engine_type
            })
            
        except Exception as e:
            logger.error(f"Error resetting agent: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            return jsonify({
                'status': 'healthy',
                'engines': {
                    'browser_use': 'available'
                },
                'message': 'AI browser automation ready',
                'security': {
                    'authentication': 'enabled' if os.environ.get('API_KEY') else 'disabled',
                    'rate_limiting': 'enabled'
                }
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'unhealthy',
                'error': 'Service unavailable'
            }), 503
    
    @api.route('/api/history', methods=['GET'])
    def get_history():
        """Get all execution history"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            history_query = ExecutionHistory.query.order_by(
                ExecutionHistory.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            return jsonify({
                'success': True,
                'history': [item.to_dict() for item in history_query.items],
                'total': history_query.total,
                'page': page,
                'pages': history_query.pages,
                'per_page': per_page
            })
            
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/history/<int:history_id>', methods=['GET'])
    def get_history_item(history_id):
        """Get a specific execution history item"""
        try:
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            return jsonify({
                'success': True,
                'history': item.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error getting history item: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/history', methods=['DELETE'])
    @require_api_key
    def delete_all_history():
        """Delete all execution history"""
        try:
            count = ExecutionHistory.query.delete()
            db.session.commit()
            
            logger.info(f"🗑️  Deleted {count} history items")
            
            return jsonify({
                'success': True,
                'message': f'Deleted {count} history items',
                'count': count
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting history: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/history/<int:history_id>', methods=['DELETE'])
    @require_api_key
    def delete_history_item(history_id):
        """Delete a specific execution history item"""
        try:
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            db.session.delete(item)
            db.session.commit()
            
            logger.info(f"🗑️  Deleted history item {history_id}")
            
            return jsonify({
                'success': True,
                'message': 'History item deleted'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting history item: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/credentials', methods=['GET'])
    def list_credentials():
        """
        List all stored credentials (without values)
        """
        try:
            credentials = CredentialVault.query.order_by(CredentialVault.created_at.desc()).all()
            return jsonify({
                'success': True,
                'credentials': [cred.to_dict(include_value=False) for cred in credentials]
            })
        except Exception as e:
            logger.error(f"Error listing credentials: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to list credentials',
                'message': str(e)
            }), 500
    
    @api.route('/api/credentials', methods=['POST'])
    def create_credential():
        """
        Create a new credential
        
        Request body:
            {
                "name": "gmail_password",
                "service": "Gmail",
                "username": "user@example.com",
                "value": "secretPassword123",
                "description": "My Gmail password"
            }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request',
                    'message': 'Request body must be valid JSON'
                }), 400
            
            name = data.get('name', '').strip()
            value = data.get('value', '').strip()
            
            if not name:
                return jsonify({
                    'success': False,
                    'error': 'Invalid input',
                    'message': 'Credential name is required'
                }), 400
            
            if not value:
                return jsonify({
                    'success': False,
                    'error': 'Invalid input',
                    'message': 'Credential value is required'
                }), 400
            
            # Check if credential with this name already exists
            existing = CredentialVault.query.filter_by(name=name).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Credential exists',
                    'message': f'A credential with name "{name}" already exists'
                }), 409
            
            # Create new credential
            credential = CredentialVault(
                name=name,
                service=data.get('service', '').strip() or None,
                url=data.get('url', '').strip() or None,
                username=data.get('username', '').strip() or None,
                description=data.get('description', '').strip() or None
            )
            credential.set_credential(value)
            
            db.session.add(credential)
            db.session.commit()
            
            logger.info(f"✅ Created new credential: {name}")
            
            return jsonify({
                'success': True,
                'message': 'Credential created successfully',
                'credential': credential.to_dict(include_value=False)
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating credential: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to create credential',
                'message': str(e)
            }), 500
    
    @api.route('/api/credentials/<int:credential_id>', methods=['GET'])
    def get_credential(credential_id):
        """
        Get a specific credential (without value)
        """
        try:
            credential = CredentialVault.query.get(credential_id)
            
            if not credential:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'Credential not found'
                }), 404
            
            return jsonify({
                'success': True,
                'credential': credential.to_dict(include_value=False)
            })
            
        except Exception as e:
            logger.error(f"Error getting credential: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to get credential',
                'message': str(e)
            }), 500
    
    @api.route('/api/credentials/<int:credential_id>', methods=['PUT'])
    def update_credential(credential_id):
        """
        Update an existing credential
        """
        try:
            credential = CredentialVault.query.get(credential_id)
            
            if not credential:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'Credential not found'
                }), 404
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request',
                    'message': 'Request body must be valid JSON'
                }), 400
            
            # Update fields if provided
            if 'name' in data and data['name'].strip():
                new_name = data['name'].strip()
                # Check if another credential has this name
                existing = CredentialVault.query.filter_by(name=new_name).first()
                if existing and existing.id != credential_id:
                    return jsonify({
                        'success': False,
                        'error': 'Credential exists',
                        'message': f'A credential with name "{new_name}" already exists'
                    }), 409
                credential.name = new_name
            
            if 'service' in data:
                credential.service = data['service'].strip() or None
            
            if 'url' in data:
                credential.url = data['url'].strip() or None
            
            if 'username' in data:
                credential.username = data['username'].strip() or None
            
            if 'description' in data:
                credential.description = data['description'].strip() or None
            
            if 'value' in data and data['value'].strip():
                credential.set_credential(data['value'].strip())
            
            db.session.commit()
            
            logger.info(f"✅ Updated credential: {credential.name}")
            
            return jsonify({
                'success': True,
                'message': 'Credential updated successfully',
                'credential': credential.to_dict(include_value=False)
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating credential: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to update credential',
                'message': str(e)
            }), 500
    
    @api.route('/api/credentials/<int:credential_id>', methods=['DELETE'])
    def delete_credential(credential_id):
        """
        Delete a credential
        """
        try:
            credential = CredentialVault.query.get(credential_id)
            
            if not credential:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'Credential not found'
                }), 404
            
            credential_name = credential.name
            db.session.delete(credential)
            db.session.commit()
            
            logger.info(f"🗑️  Deleted credential: {credential_name}")
            
            return jsonify({
                'success': True,
                'message': 'Credential deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting credential: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to delete credential',
                'message': str(e)
            }), 500
    
    @api.route('/api/maintenance/database/stats', methods=['GET'])
    @require_api_key
    def get_db_stats():
        """Get database statistics (requires API key)"""
        try:
            stats = get_database_stats()
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to get database stats',
                'message': str(e)
            }), 500
    
    @api.route('/api/maintenance/database/prune', methods=['POST'])
    @require_api_key
    def prune_database():
        """Prune old execution history records"""
        try:
            data = request.get_json() or {}
            days_to_keep = data.get('days_to_keep', 30)
            dry_run = data.get('dry_run', True)  # Default to dry run for safety
            
            if not isinstance(days_to_keep, int) or days_to_keep < 1:
                return jsonify({
                    'success': False,
                    'error': 'Invalid parameter',
                    'message': 'days_to_keep must be a positive integer'
                }), 400
            
            result = prune_old_executions(days_to_keep=days_to_keep, dry_run=dry_run)
            
            return jsonify({
                'success': True,
                'result': result,
                'message': f"{'[DRY RUN] Would delete' if dry_run else 'Deleted'} {result['deleted_executions']} executions"
            })
            
        except Exception as e:
            logger.error(f"Error pruning database: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to prune database',
                'message': str(e)
            }), 500
    
    return api
