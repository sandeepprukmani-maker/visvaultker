"""
API Routes
RESTful endpoints for browser automation with security and validation
"""
import os
import json
import logging
import threading
import asyncio
from queue import Queue
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context, current_app
from app.models import db, ExecutionHistory, GeneratedScript, CredentialVault, SiteCrawl, CrawlPage, SiteKnowledge
from app.services.engine_orchestrator import EngineOrchestrator
from app.services.site_crawler import SiteCrawlerService
from app.services.knowledge_retriever import KnowledgeRetriever
from app.middleware.security import (
    require_api_key,
    rate_limit,
    validate_engine_type,
    validate_instruction,
    sanitize_error_message
)
from app.utils.timeout import run_with_timeout, TimeoutError
from app.utils.credentials import replace_credential_placeholders

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
        
        # Save generated Python code if available (Playwright MCP engine only)
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
    
    @api.route('/crawler')
    def crawler():
        """Render site crawler page"""
        return render_template('crawler.html')
    
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
            
            # Enhance instruction with site knowledge if available
            use_knowledge = data.get('use_knowledge', True)  # Default to true
            if use_knowledge:
                try:
                    retriever = KnowledgeRetriever()
                    enhanced_instruction = retriever.enhance_instruction_with_knowledge(processed_instruction)
                    if enhanced_instruction != processed_instruction:
                        logger.info("🧠 Enhanced instruction with site knowledge")
                        processed_instruction = enhanced_instruction
                except Exception as e:
                    logger.warning(f"⚠️  Knowledge enhancement failed: {str(e)}")
                    # Continue with original instruction
            
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
    
    # ============================================
    # SITE CRAWLER ENDPOINTS
    # ============================================
    
    @api.route('/api/crawls', methods=['GET'])
    @require_api_key
    def list_crawls():
        """List all site crawls"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', None)
            
            query = SiteCrawl.query
            if status:
                query = query.filter_by(status=status)
            
            crawls_query = query.order_by(
                SiteCrawl.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            return jsonify({
                'success': True,
                'crawls': [crawl.to_dict() for crawl in crawls_query.items],
                'total': crawls_query.total,
                'page': page,
                'pages': crawls_query.pages,
                'per_page': per_page
            })
            
        except Exception as e:
            logger.error(f"Error listing crawls: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to list crawls',
                'message': str(e)
            }), 500
    
    @api.route('/api/crawls', methods=['POST'])
    @require_api_key
    def create_crawl():
        """
        Create a new site crawl
        
        Request body:
        {
            "name": "My Site Crawl",
            "start_url": "https://example.com",
            "credential_id": 1,  // optional
            "max_pages": 50,
            "max_depth": 3,
            "same_domain_only": true,
            "auto_start": false
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
            start_url = data.get('start_url', '').strip()
            
            if not name:
                return jsonify({
                    'success': False,
                    'error': 'Invalid input',
                    'message': 'Name is required'
                }), 400
            
            if not start_url:
                return jsonify({
                    'success': False,
                    'error': 'Invalid input',
                    'message': 'Start URL is required'
                }), 400
            
            if not start_url.startswith('http://') and not start_url.startswith('https://'):
                return jsonify({
                    'success': False,
                    'error': 'Invalid input',
                    'message': 'Start URL must begin with http:// or https://'
                }), 400
            
            # Create crawl
            crawl = SiteCrawl(
                name=name,
                start_url=start_url,
                credential_id=data.get('credential_id'),
                max_pages=data.get('max_pages', 50),
                max_depth=data.get('max_depth', 3),
                same_domain_only=data.get('same_domain_only', True),
                status='pending'
            )
            
            db.session.add(crawl)
            db.session.commit()
            
            logger.info(f"✅ Created crawl: {crawl.name} (ID: {crawl.id})")
            
            # Auto-start if requested
            if data.get('auto_start', False):
                # Start crawl in background thread with Flask app context
                app = current_app._get_current_object()
                crawl_id = crawl.id
                
                def start_crawl_async():
                    with app.app_context():
                        crawler = SiteCrawlerService()
                        asyncio.run(crawler.start_crawl(crawl_id))
                
                thread = threading.Thread(target=start_crawl_async)
                thread.daemon = True
                thread.start()
                
                logger.info(f"🚀 Started crawl #{crawl.id} in background")
            
            return jsonify({
                'success': True,
                'message': 'Crawl created successfully',
                'crawl': crawl.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating crawl: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to create crawl',
                'message': str(e)
            }), 500
    
    @api.route('/api/crawls/<int:crawl_id>', methods=['GET'])
    @require_api_key
    def get_crawl(crawl_id):
        """Get a specific crawl with optional details"""
        try:
            crawl = SiteCrawl.query.get(crawl_id)
            
            if not crawl:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'Crawl not found'
                }), 404
            
            include_pages = request.args.get('include_pages', 'false').lower() == 'true'
            include_knowledge = request.args.get('include_knowledge', 'false').lower() == 'true'
            
            return jsonify({
                'success': True,
                'crawl': crawl.to_dict(include_pages=include_pages, include_knowledge=include_knowledge)
            })
            
        except Exception as e:
            logger.error(f"Error getting crawl: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to get crawl',
                'message': str(e)
            }), 500
    
    @api.route('/api/crawls/<int:crawl_id>/start', methods=['POST'])
    @require_api_key
    @rate_limit
    def start_crawl(crawl_id):
        """Start a crawl"""
        try:
            crawl = SiteCrawl.query.get(crawl_id)
            
            if not crawl:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'Crawl not found'
                }), 404
            
            if crawl.status == 'running':
                return jsonify({
                    'success': False,
                    'error': 'Already running',
                    'message': 'Crawl is already running'
                }), 400
            
            # Start crawl in background with Flask app context
            app = current_app._get_current_object()
            
            def start_crawl_async():
                with app.app_context():
                    crawler = SiteCrawlerService()
                    asyncio.run(crawler.start_crawl(crawl_id))
            
            thread = threading.Thread(target=start_crawl_async)
            thread.daemon = True
            thread.start()
            
            logger.info(f"🚀 Started crawl #{crawl_id} in background")
            
            return jsonify({
                'success': True,
                'message': 'Crawl started successfully',
                'crawl_id': crawl_id
            })
            
        except Exception as e:
            logger.error(f"Error starting crawl: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to start crawl',
                'message': str(e)
            }), 500
    
    @api.route('/api/crawls/<int:crawl_id>/knowledge', methods=['GET'])
    @require_api_key
    def get_crawl_knowledge(crawl_id):
        """Get knowledge learned from a crawl"""
        try:
            crawl = SiteCrawl.query.get(crawl_id)
            
            if not crawl:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'Crawl not found'
                }), 404
            
            retriever = KnowledgeRetriever()
            knowledge_summary = retriever.get_knowledge_summary(crawl_id)
            
            return jsonify(knowledge_summary)
            
        except Exception as e:
            logger.error(f"Error getting crawl knowledge: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to get knowledge',
                'message': str(e)
            }), 500
    
    @api.route('/api/crawls/<int:crawl_id>', methods=['DELETE'])
    @require_api_key
    def delete_crawl(crawl_id):
        """Delete a crawl and all associated data"""
        try:
            crawl = SiteCrawl.query.get(crawl_id)
            
            if not crawl:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'Crawl not found'
                }), 404
            
            if crawl.status == 'running':
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete running crawl',
                    'message': 'Please stop the crawl before deleting'
                }), 400
            
            crawl_name = crawl.name
            db.session.delete(crawl)
            db.session.commit()
            
            logger.info(f"🗑️ Deleted crawl: {crawl_name}")
            
            return jsonify({
                'success': True,
                'message': 'Crawl deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting crawl: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to delete crawl',
                'message': str(e)
            }), 500
    
    @api.route('/api/knowledge/search', methods=['GET'])
    @require_api_key
    def search_knowledge():
        """Search for site knowledge by URL"""
        try:
            url = request.args.get('url', '').strip()
            
            if not url:
                return jsonify({
                    'success': False,
                    'error': 'Invalid input',
                    'message': 'URL parameter is required'
                }), 400
            
            retriever = KnowledgeRetriever()
            knowledge = retriever.get_knowledge_for_url(url)
            
            return jsonify(knowledge)
            
        except Exception as e:
            logger.error(f"Error searching knowledge: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Failed to search knowledge',
                'message': str(e)
            }), 500
    
    return api
