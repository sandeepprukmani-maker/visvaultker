"""
Main entry point for the AI Browser Automation web application
"""
import os
import sys
from dotenv import load_dotenv
from app import create_app
from app.utils.model_provider import ModelProviderFactory

# Force unbuffered output for better logging
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore
os.environ['PYTHONUNBUFFERED'] = '1'

# Load .env file and override any existing environment variables
load_dotenv(override=True)

app = create_app()

if __name__ == '__main__':
    print("="*80)
    print("🚀 AI BROWSER AUTOMATION - STARTING UP")
    print("="*80)
    
    # Validate AI provider configuration
    try:
        provider_config = ModelProviderFactory.get_provider_config()
        provider = provider_config['provider']
        model = provider_config['model']
        
        print(f"\n🤖 AI Provider: {provider.upper()}")
        print(f"🧠 Model: {model}")
        
        is_valid, missing_vars = ModelProviderFactory.validate_provider_config(provider)
        
        if is_valid:
            print(f"✅ {provider.upper()} credentials configured correctly")
            
            if provider == 'oauth_gateway':
                print(f"✅ Gateway URL: {os.environ.get('GW_BASE_URL')}")
            elif provider == 'openai':
                print("✅ OpenAI API key found")
            elif provider == 'anthropic':
                print("✅ Anthropic API key found")
            elif provider == 'gemini':
                print("✅ Google API key found")
        else:
            print(f"\n⚠️  WARNING: Missing {provider.upper()} environment variables: {', '.join(missing_vars)}")
            print("   The application will start but AI features will not work.")
            print(f"   Please set the required variables for {provider.upper()} provider.\n")
            print("   Provider-specific requirements:")
            print("   - openai: OPENAI_API_KEY")
            print("   - anthropic: ANTHROPIC_API_KEY")
            print("   - gemini: GOOGLE_API_KEY")
            print("   - oauth_gateway: OAUTH_TOKEN_URL, OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET, OAUTH_GRANT_TYPE, OAUTH_SCOPE, GW_BASE_URL\n")
    except Exception as e:
        print(f"\n⚠️  WARNING: Error validating provider configuration: {str(e)}")
        print("   The application will start but AI features may not work.\n")
    
    sys.stdout.flush()

    print("\n🌐 Starting Flask web server on port 5000...")
    print("="*80)
    print("\n💡 TIP: Keep this console window open to see automation logs\n")
    sys.stdout.flush()

    # Start the web app with debug mode for better console output
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
