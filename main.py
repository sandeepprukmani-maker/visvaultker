"""
Main entry point for the AI Browser Automation web application
"""
import os
import sys
from dotenv import load_dotenv
from app import create_app

# Force unbuffered output for better logging
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore
os.environ['PYTHONUNBUFFERED'] = '1'

# Skip Playwright browser downloads permanently
os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'

# Load .env file and override any existing environment variables
load_dotenv(override=True)

app = create_app()

if __name__ == '__main__':
    print("="*80)
    print("🚀 AI BROWSER AUTOMATION - STARTING UP")
    print("="*80)
    
    # Validate OAuth configuration
    required_oauth_vars = [
        "OAUTH_TOKEN_URL",
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "OAUTH_GRANT_TYPE",
        "OAUTH_SCOPE",
        "GW_BASE_URL"
    ]
    
    missing_vars = [var for var in required_oauth_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"\n⚠️  WARNING: Missing OAuth environment variables: {', '.join(missing_vars)}")
        print("   The application will start but AI features will not work.")
        print("   Please set the required OAuth variables in your environment.\n")
    else:
        print("✅ OAuth configuration found")
        print(f"✅ Gateway URL: {os.environ.get('GW_BASE_URL')}")
    
    sys.stdout.flush()

    print("\n🌐 Starting Flask web server on port 5000...")
    print("="*80)
    print("\n💡 TIP: Keep this console window open to see automation logs\n")
    sys.stdout.flush()

    # Start the web app with debug mode for better console output
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
