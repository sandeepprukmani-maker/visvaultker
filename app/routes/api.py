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
from app.models import db, ExecutionHistory, GeneratedScript, SiteCredential
from app.services.engine_orchestrator import EngineOrchestrator
from app.middleware.security import (
    require_api_key,
    rate_limit,
    validate_engine_type,
    validate_instruction,
    sanitize_error_message
)
from app.utils.timeout import run_with_timeout, TimeoutError

logger = logging.getLogger(__name__)

def save_execution_to_history(instruction, engine_type, headless, result):
    """
    Save execution result to history database
    
    Args:
        instruction: The automation instruction
        engine_type: The engine used (browser_use or playwright_mcp)
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
        
        # Save generated Python code if available (Playwright MCP engine)
        if result.get('playwright_code'):
            import hashlib
            python_code = result.get('playwright_code')
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
    
    @api.route('/teaching-mode')
    def teaching_mode():
        """Render teaching mode page"""
        return render_template('teaching-mode.html')
    
    @api.route('/task-library')
    def task_library():
        """Render task library page"""
        return render_template('task-library.html')
    
    @api.route('/recall-mode')
    def recall_mode():
        """Render recall mode page"""
        return render_template('recall-mode.html')
    
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
            
            logger.info("="*80)
            logger.info("📨 NEW AUTOMATION REQUEST")
            logger.info(f"📝 Instruction: {instruction}")
            logger.info(f"🔧 Engine: {engine_type}")
            logger.info(f"👁️  Headless: {headless}")
            logger.info(f"🌐 Client: {request.remote_addr}")
            logger.info("="*80)
            
            logger.info("🚀 Starting automation execution...")
            
            try:
                result = run_with_timeout(
                    orchestrator.execute_instruction,
                    300,
                    instruction,
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
            
            save_execution_to_history(instruction, engine_type, headless, result)
            
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
                
                logger.info("="*80)
                logger.info("📨 NEW AUTOMATION REQUEST (STREAMING)")
                logger.info(f"📝 Instruction: {instruction}")
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
                            instruction,
                            engine_type,
                            headless,
                            progress_callback
                        )
                        result_holder['result'] = result
                        # Use app context for database operations in thread
                        with app.app_context():
                            save_execution_to_history(instruction, engine_type, headless, result)
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
                            save_execution_to_history(instruction, engine_type, headless, error_result)
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
    
    @api.route('/api/mcp/status', methods=['GET'])
    def mcp_server_status():
        """Get Playwright MCP server status"""
        try:
            from app.engines.playwright_mcp import get_server_status
            status = get_server_status()
            
            return jsonify({
                'success': True,
                'server_mode': status['mode'],
                'persistent_running': status['persistent_running'],
                'message': f"MCP server in '{status['mode']}' mode"
            })
            
        except Exception as e:
            logger.error(f"Error getting MCP server status: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/mcp/restart', methods=['POST'])
    @require_api_key
    def restart_mcp_server():
        """Restart persistent MCP server (only works in 'always_run' mode)"""
        try:
            from app.engines.playwright_mcp import shutdown_server, get_server_status
            
            status = get_server_status()
            if status['mode'] != 'always_run':
                return jsonify({
                    'success': False,
                    'error': 'Server not in always_run mode',
                    'message': 'Server restart only available in always_run mode'
                }), 400
            
            shutdown_server()
            logger.info("🔄 MCP server restarted")
            
            return jsonify({
                'success': True,
                'message': 'MCP server shutdown. It will restart on next request.'
            })
            
        except Exception as e:
            logger.error(f"Error restarting MCP server: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            from app.engines.playwright_mcp import get_server_status
            mcp_status = get_server_status()
            
            return jsonify({
                'status': 'healthy',
                'engines': {
                    'browser_use': 'available',
                    'playwright_mcp': 'available'
                },
                'mcp_server': {
                    'mode': mcp_status['mode'],
                    'running': mcp_status['persistent_running']
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
    
    @api.route('/api/history/<int:history_id>/execute', methods=['POST'])
    @require_api_key
    @rate_limit
    def execute_from_history(history_id):
        """
        Execute a script from history with auto-healing
        
        Logic:
        1. Execute the generated script (or healed script if both exist, healed takes precedence)
        2. If it fails, trigger healer agent to fix it
        3. Save healed script to database
        4. If healed script fails, move it to generated_script and create new healed version
        """
        import subprocess
        import tempfile
        from app.engines.playwright_mcp.agents.healer_agent import HealerAgent
        from app.models import GeneratedScript
        
        try:
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            # Get the script to execute
            # If both exist, healed script takes precedence
            healed_scripts = [s for s in item.generated_scripts if s.is_healed]
            generated_scripts = [s for s in item.generated_scripts if not s.is_healed]
            
            script_to_execute = None
            is_executing_healed = False
            existing_healed_script = None
            existing_generated_script = None
            
            if healed_scripts:
                # Sort by created_at descending to get the most recent
                healed_scripts.sort(key=lambda x: x.created_at, reverse=True)
                script_to_execute = healed_scripts[0].python_code
                is_executing_healed = True
                existing_healed_script = healed_scripts[0]
                logger.info(f"🔄 Executing healed script from history #{history_id}")
            elif generated_scripts:
                generated_scripts.sort(key=lambda x: x.created_at, reverse=True)
                script_to_execute = generated_scripts[0].python_code
                existing_generated_script = generated_scripts[0]
                logger.info(f"🔄 Executing generated script from history #{history_id}")
            else:
                return jsonify({
                    'success': False,
                    'error': 'No script',
                    'message': 'No generated script found for this history item'
                }), 400
            
            # Execute the script
            logger.info("▶️  Executing script...")
            execution_result, error_message = _execute_python_script(script_to_execute)
            
            if execution_result['success']:
                # Script passed without errors
                logger.info("✅ Script executed successfully without errors")
                return jsonify({
                    'success': True,
                    'message': 'Script executed successfully',
                    'healing_needed': False
                })
            
            # Script failed, trigger healing
            logger.warning(f"❌ Script failed: {error_message}")
            logger.info("🔧 Triggering healer agent...")
            
            # Initialize healer agent
            from auth.oauth_handler import OAuthHandler
            oauth_handler = OAuthHandler()
            llm_client = oauth_handler.get_llm_client()
            healer_agent = HealerAgent(llm_client)
            
            # Heal the script
            heal_result = healer_agent.heal_script(
                python_code=script_to_execute,
                error_message=error_message,
                max_iterations=3
            )
            
            if not heal_result.get('success'):
                logger.error("❌ Healing failed")
                return jsonify({
                    'success': False,
                    'error': 'Healing failed',
                    'message': 'Could not automatically fix the script errors'
                }), 500
            
            healed_code = heal_result['healed_code']
            healing_iterations = heal_result['healing_iterations']
            
            # If we were executing a healed script that failed:
            # Move it to generated_script and create new healed version
            if is_executing_healed and existing_healed_script:
                logger.info("🔄 Healed script failed, moving to generated and creating new healed version...")
                
                # Mark the old healed script as non-healed (move to generated)
                existing_healed_script.is_healed = False
                existing_healed_script.healing_iterations = 0
                
                # Create new healed script
                new_healed_script = GeneratedScript(
                    execution_id=history_id,
                    python_code=healed_code,
                    script_hash=heal_result['script_hash'],
                    is_healed=True,
                    healing_iterations=healing_iterations
                )
                db.session.add(new_healed_script)
            else:
                # Create new healed script from generated script
                logger.info("🔧 Creating new healed script...")
                new_healed_script = GeneratedScript(
                    execution_id=history_id,
                    python_code=healed_code,
                    script_hash=heal_result['script_hash'],
                    is_healed=True,
                    healing_iterations=healing_iterations
                )
                db.session.add(new_healed_script)
            
            db.session.commit()
            logger.info(f"✅ Healed script saved to database")
            
            return jsonify({
                'success': True,
                'message': 'Script healed successfully',
                'healing_needed': True,
                'healed_script': healed_code,
                'healing_attempts': healing_iterations,
                'healing_steps': len(json.loads(heal_result.get('fixes_applied', '[]')))
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error executing from history: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    def _execute_python_script(python_code: str) -> tuple:
        """
        Execute a Python script and return success status and error message
        
        Returns:
            Tuple of (result_dict, error_message)
        """
        try:
            # Create a temporary file with the script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(python_code)
                script_path = f.name
            
            # Execute the script with timeout
            result = subprocess.run(
                ['python', script_path],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            # Clean up temp file
            import os
            os.unlink(script_path)
            
            if result.returncode == 0:
                return ({'success': True}, None)
            else:
                error_msg = result.stderr or result.stdout or 'Unknown error'
                return ({'success': False}, error_msg)
                
        except subprocess.TimeoutExpired:
            return ({'success': False}, 'Script execution timed out after 60 seconds')
        except Exception as e:
            return ({'success': False}, str(e))
    
    # ========================================================================
    # CREDENTIAL MANAGEMENT ENDPOINTS
    # ========================================================================
    
    @api.route('/credentials', methods=['GET'])
    def get_credentials_page():
        """Render credentials management page"""
        return render_template('credentials.html')
    
    @api.route('/api/credentials', methods=['GET'])
    @require_api_key
    def list_credentials():
        """List all stored credentials (without passwords)"""
        try:
            credentials = SiteCredential.query.all()
            return jsonify([cred.to_dict(include_password=False) for cred in credentials])
        except Exception as e:
            logger.error(f"Error listing credentials: {str(e)}")
            return jsonify({'error': 'Failed to load credentials'}), 500
    
    @api.route('/api/credentials', methods=['POST'])
    @require_api_key
    def create_credential():
        """Create a new site credential"""
        try:
            data = request.get_json()
            
            if not data or not all(k in data for k in ['site_name', 'url', 'username', 'password']):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Check if site already exists
            existing = SiteCredential.query.filter_by(site_name=data['site_name'].lower().strip()).first()
            if existing:
                return jsonify({'error': 'Site already exists'}), 409
            
            # Create new credential
            credential = SiteCredential(
                site_name=data['site_name'].lower().strip(),
                url=data['url'].strip(),
                username=data['username'].strip(),
                keywords=data.get('keywords', '').strip()
            )
            credential.set_password(data['password'])
            
            db.session.add(credential)
            db.session.commit()
            
            logger.info(f"✅ Created credential for {credential.site_name}")
            
            return jsonify(credential.to_dict(include_password=False)), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating credential: {str(e)}")
            return jsonify({'error': 'Failed to create credential'}), 500
    
    @api.route('/api/credentials/<int:cred_id>', methods=['PUT'])
    @require_api_key
    def update_credential(cred_id):
        """Update an existing credential"""
        try:
            credential = SiteCredential.query.get_or_404(cred_id)
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Update fields
            if 'site_name' in data:
                # Check if new name conflicts with another site
                new_name = data['site_name'].lower().strip()
                if new_name != credential.site_name:
                    existing = SiteCredential.query.filter_by(site_name=new_name).first()
                    if existing:
                        return jsonify({'error': 'Site name already exists'}), 409
                credential.site_name = new_name
            
            if 'url' in data:
                credential.url = data['url'].strip()
            if 'username' in data:
                credential.username = data['username'].strip()
            if 'keywords' in data:
                credential.keywords = data.get('keywords', '').strip()
            if 'password' in data and data['password']:
                credential.set_password(data['password'])
            
            credential.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Updated credential for {credential.site_name}")
            
            return jsonify(credential.to_dict(include_password=False))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating credential: {str(e)}")
            return jsonify({'error': 'Failed to update credential'}), 500
    
    @api.route('/api/credentials/<int:cred_id>', methods=['DELETE'])
    @require_api_key
    def delete_credential(cred_id):
        """Delete a credential"""
        try:
            credential = SiteCredential.query.get_or_404(cred_id)
            site_name = credential.site_name
            
            db.session.delete(credential)
            db.session.commit()
            
            logger.info(f"🗑️  Deleted credential for {site_name}")
            
            return jsonify({'success': True, 'message': 'Credential deleted'})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting credential: {str(e)}")
            return jsonify({'error': 'Failed to delete credential'}), 500
    
    return api
