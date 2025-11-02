"""
Flask Application Factory
"""
import os
import logging
import sys
import atexit
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root with explicit path
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# PRIVACY: Disable all external data transmission from browser-use library
# Set these BEFORE importing any browser-use components
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'false')
os.environ.setdefault('BROWSER_USE_CLOUD_SYNC', 'false')

from flask import Flask
from flask_cors import CORS
from app.models import db
from app.services.engine_orchestrator import EngineOrchestrator
from app.routes.api import create_api_routes
from app.utils.logging_config import LoggingConfigurator


def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Configured Flask app instance
    """
    # Configure logging from config.ini
    logging_config = LoggingConfigurator()
    logging_config.configure()
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting AI Browser Automation application")
    
    # Log privacy settings confirmation
    telemetry_status = os.environ.get('ANONYMIZED_TELEMETRY', 'not set')
    cloud_sync_status = os.environ.get('BROWSER_USE_CLOUD_SYNC', 'not set')
    logger.info("=" * 80)
    logger.info("🔒 PRIVACY SETTINGS")
    logger.info("=" * 80)
    logger.info(f"Anonymized Telemetry: {telemetry_status} (should be 'false')")
    logger.info(f"Cloud Sync: {cloud_sync_status} (should be 'false')")
    if telemetry_status.lower()[:1] in 'ty1' or cloud_sync_status.lower()[:1] in 'ty1':
        logger.warning("⚠️  WARNING: External data transmission may be ENABLED!")
        logger.warning("⚠️  Set ANONYMIZED_TELEMETRY=false and BROWSER_USE_CLOUD_SYNC=false")
    else:
        logger.info("✅ All external data transmission DISABLED")
        logger.info("✅ No telemetry or cloud sync - data stays on your system")
    logger.info("=" * 80)
    
    app = Flask(__name__)
    
    # Session secret key - MUST be set in production
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        # Generate ephemeral random key for local development only
        import secrets
        session_secret = secrets.token_hex(32)
        logger.warning("⚠️  SESSION_SECRET not set! Using ephemeral random key for local dev.")
        logger.warning("⚠️  Set SESSION_SECRET environment variable for production!")
    
    app.config['SECRET_KEY'] = session_secret
    
    # Use SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///automation_history.db"
    logger.info("📝 Using SQLite database")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        logger.info("✅ Database initialized successfully")
    
    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '*').split(',')
    CORS(app, 
         resources={r"/api/*": {"origins": allowed_origins}},
         methods=["GET", "POST", "OPTIONS", "DELETE"],
         allow_headers=["Content-Type", "X-API-Key"],
         supports_credentials=True)
    
    logger.info(f"🔒 CORS configured with origins: {allowed_origins}")
    logger.info("📦 Initializing Engine Orchestrator")
    orchestrator = EngineOrchestrator()
    
    logger.info("🔗 Registering API routes")
    api_routes = create_api_routes(orchestrator)
    app.register_blueprint(api_routes)
    
    # Add cache control headers to prevent browser caching issues
    @app.after_request
    def add_cache_control_headers(response):
        """Add Cache-Control headers to all responses to prevent caching"""
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    # Handle favicon request to prevent 404 errors
    @app.route('/favicon.ico')
    def favicon():
        """Return 204 No Content for favicon requests"""
        from flask import Response
        return Response(status=204)
    
    # Serve automation outputs (screenshots, PDFs, etc.)
    @app.route('/automation_outputs/<path:filename>')
    def serve_automation_outputs(filename):
        """Serve files from automation_outputs directory (legacy)"""
        from flask import send_from_directory
        import os
        output_dir = os.path.join(project_root, 'automation_outputs')
        return send_from_directory(output_dir, filename)
    
    # Serve screenshots from the new screenshots folder
    @app.route('/screenshots/<path:filename>')
    def serve_screenshots(filename):
        """Serve files from screenshots directory"""
        from flask import send_from_directory
        import os
        screenshots_dir = os.path.join(project_root, 'screenshots')
        # Create directory if it doesn't exist
        os.makedirs(screenshots_dir, exist_ok=True)
        return send_from_directory(screenshots_dir, filename)
    
    # Register cleanup handler for MCP server on app shutdown
    def cleanup_mcp_server():
        """Cleanup handler for persistent MCP server"""
        try:
            from app.engines.playwright_mcp import shutdown_server, get_server_status
            status = get_server_status()
            if status['persistent_running']:
                logger.info("🧹 Shutting down persistent MCP server on app exit...")
                shutdown_server()
                logger.info("✅ MCP server cleanup complete")
        except Exception as e:
            logger.error(f"⚠️  Error during MCP server cleanup: {e}")
    
    atexit.register(cleanup_mcp_server)
    
    logger.info("✅ Application initialization complete")
    
    return app
