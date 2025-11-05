# AI Browser Automation

## Overview
This is an AI-powered browser automation web application built with Flask and Playwright. It provides a web interface for automating browser tasks using AI agents.

**Current Status**: ✅ GitHub import successfully configured and running in Replit environment
**Last Updated**: November 5, 2025

## Project Architecture

### Technology Stack
- **Backend**: Python 3.12 with Flask web framework
- **Database**: SQLite (local, stored in instance/ directory)
- **Browser Automation**: Playwright with Chromium browser
- **AI Features**: Supports multiple AI providers (OpenAI, Anthropic, Google, etc.)
- **Node.js Integration**: Playwright MCP server for enhanced automation

### Project Structure
```
.
├── app/                          # Flask application
│   ├── engines/                  # Browser automation engines
│   │   ├── browser_use/         # Browser-use integration
│   │   └── playwright_mcp/      # Playwright MCP integration
│   ├── middleware/              # Security and API middleware
│   ├── routes/                  # API routes
│   ├── services/                # Business logic services
│   ├── static/                  # Frontend assets (CSS, JS)
│   ├── templates/               # HTML templates
│   └── utils/                   # Utility functions
├── auth/                        # OAuth authentication
├── config/                      # Configuration files
├── integrations/                # External integrations
│   └── playwright_mcp_node/    # Node.js MCP server
├── instance/                    # SQLite database storage
├── main.py                      # Application entry point
└── requirements.txt             # Python dependencies
```

### Key Features
1. **Browser Automation**: Automated web browsing with AI-guided actions
2. **Multiple AI Engines**: Support for browser-use and Playwright MCP
3. **Code Generation**: Both engines generate reusable Python Playwright scripts with accurate locators
4. **Web Interface**: User-friendly dashboard for managing automations
5. **Security**: API key authentication, rate limiting, CORS protection
6. **Privacy-First**: No telemetry or cloud sync by default
7. **State Persistence**: Save and restore browser states
8. **Screenshot & PDF Generation**: Capture automation results

## Configuration

### Environment Variables
The application requires OAuth credentials for AI features. Configure these in Replit Secrets:

**Required for AI Features** (optional for basic usage):
- `OAUTH_TOKEN_URL` - OAuth token endpoint
- `OAUTH_CLIENT_ID` - OAuth client ID
- `OAUTH_CLIENT_SECRET` - OAuth client secret
- `OAUTH_GRANT_TYPE` - OAuth grant type (typically "client_credentials")
- `OAUTH_SCOPE` - OAuth scope
- `GW_BASE_URL` - Gateway base URL

**Security Configuration**:
- `SESSION_SECRET` - Flask session secret (auto-generated if not set)
- `API_KEY` - API key for endpoint protection (optional)

**CORS Configuration**:
- `CORS_ALLOWED_ORIGINS` - Allowed origins (default: "*")

**Privacy Settings** (already configured):
- `ANONYMIZED_TELEMETRY=false` - Disables telemetry
- `BROWSER_USE_CLOUD_SYNC=false` - Disables cloud sync

### Application Configuration
Configuration is managed via `config/config.ini`:
- Browser settings (headless mode, browser type)
- AI model configuration
- Logging levels and verbosity
- Performance tuning (wait times, retry settings)
- Advanced features (screenshots, PDFs, cookies, state persistence)

## Running the Application

### Development Mode
The Flask development server runs automatically:
```bash
python main.py
```
- Listens on: `0.0.0.0:5000`
- Debug mode: Enabled
- Auto-reload: Disabled (for stability)

### Production Deployment
Configured to use Gunicorn for production:
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 main:app
```

## Database
- **Type**: SQLite
- **Location**: `instance/automation_history.db`
- **Auto-migration**: Tables created automatically on startup
- **Backup**: Included in Replit snapshots

## Dependencies

### Python Packages
Key dependencies (see requirements.txt for full list):
- Flask 3.1.2 - Web framework
- Playwright 1.55.0 - Browser automation
- SQLAlchemy 2.0.44 - Database ORM
- Gunicorn 23.0.0 - Production WSGI server
- Anthropic, OpenAI, Google GenAI - AI provider SDKs

### System Dependencies
Installed for Playwright browser support:
- Chromium browser dependencies (X11, Mesa, Cairo, Pango, etc.)

### Node.js Packages
Located in `integrations/playwright_mcp_node/`:
- @playwright/mcp - Playwright MCP server
- playwright - Browser automation library

## Code Generation

The **Playwright MCP engine** generates **reusable Python Playwright scripts** from executed automations:

### Playwright MCP Engine Features
- **Three-Agent System**: Planner → Generator → Healer for robust code generation
- **Validated Locators**: Uses strict-mode locator engine with element validation
- **Self-Healing**: Healer agent can automatically fix failing scripts using trace analysis
- **Advanced**: Supports complex workflows with state management
- **Production-Ready**: Complete async scripts with proper error handling and logging

### Browser-Use Engine
The browser-use engine **does not** generate code. It executes automations but does not produce reusable scripts.

**Why?** Browser-use code generation was unreliable due to:
- No validation of generated locators
- No testing of generated code
- High risk of producing non-functional scripts

**Recommendation**: Use the **Playwright MCP engine** when you need reusable code generation.

### Usage
Generated code (from Playwright MCP only) is automatically saved to the database and accessible via:
- Web interface history view
- API response (`playwright_code` field)
- Database `GeneratedScript` table

All generated scripts are standalone, executable, and ready for CI/CD integration.

## User Preferences
- **AI Model**: Configured to use `gpt-4.1-2025-04-14-eastus-dz` for all AI operations
  - Model is read from `config/config.ini` and applied across all engines (browser-use, Playwright MCP, and all three agents: Planner, Generator, Healer)

## Recent Changes
- **Nov 5, 2025**: Updated AI model configuration to use gpt-4.1-2025-04-14-eastus-dz
  - Updated `config/config.ini` to use `model = gpt-4.1-2025-04-14-eastus-dz`
  - Modified all agent files (PlannerAgent, GeneratorAgent, HealerAgent) to accept and use model parameter from config
  - Removed hardcoded "gpt-4o" references in favor of dynamic model configuration
  - Model is now consistently read from config across all components
  - Verified application restart successful with new configuration
- **Nov 5, 2025**: Fixed screenshot capture and display functionality
  - Updated screenshot serving route to correctly map to automation_outputs/screenshots/ directory
  - Screenshots are now properly captured during automation and displayed in real-time in the UI
  - Screenshot panel shows all captured screenshots with step numbers and URLs
  - Screenshots saved to automation_outputs/screenshots/ with timestamped filenames
  - Accessible via both /automation_outputs/ and /screenshots/ routes
- **Nov 5, 2025**: Removed Website Learning System
  - Deleted learning integration from engine_orchestrator.py (no more prompt enhancement or learning from executions)
  - Removed WebsiteKnowledgeBase database model from models.py
  - Deleted website_learning.py and prompt_enhancer.py utility files
  - Removed "PERSISTENT LEARNING" navigation section from UI
  - Removed teaching-mode, recall-mode, and task-library routes and templates
  - Application now runs in pure execution mode without learning features
  - Verified functional: Application starts successfully, all routes working, no errors
- **Nov 5, 2025**: GitHub import successfully configured and verified in Replit environment
  - Python 3.12.11 and Node.js 20.19.3 confirmed installed
  - All Python dependencies verified installed: Flask 3.1.2, Playwright 1.55.0, Anthropic 0.71.0, browser-use 0.9.5, Gunicorn 23.0.0, and 100+ packages
  - Node.js dependencies installed: @playwright/mcp@0.0.43 with playwright@1.57.0-alpha
  - System dependencies installed: X11 libraries (libxcb, libX11, libXcomposite, libXdamage, libXext, libXfixes, libXrandr), Mesa, Cairo, Pango, NSS, ATK, CUPS, DBus, ALSA, libdrm, libgbm, libxkbcommon
  - Playwright Chromium browser installed at /home/runner/workspace/.cache/ms-playwright/chromium-1187
  - Flask workflow configured and running successfully on 0.0.0.0:5000 with webview output
  - Application verified functional: Dashboard loading correctly, database initialized, all routes responding
  - Privacy settings confirmed: ANONYMIZED_TELEMETRY=false, BROWSER_USE_CLOUD_SYNC=false
  - Production deployment configured with Gunicorn autoscale mode (2 workers, port 5000)
  - .gitignore properly configured for Python and Node.js artifacts
- **Nov 4, 2025**: Removed unreliable code generation from browser-use engine
  - Deleted code_generator.py module
  - Updated API to only handle code generation from Playwright MCP engine
  - Browser-use now focuses on execution only; use Playwright MCP for code generation

## Known Issues
- OAuth environment variables are not configured (AI features will not work until set)
- This is expected for fresh setup - configure secrets when ready to use AI features

## Next Steps for Users
1. **Configure OAuth Credentials** (optional):
   - Add required OAuth environment variables in Replit Secrets
   - Restart the application to activate AI features

2. **Customize Configuration** (optional):
   - Edit `config/config.ini` to adjust browser settings, AI models, or performance tuning
   - Modify logging levels for debugging or production use

3. **Start Automating**:
   - Open the web interface (click "Open Website" in Replit)
   - Use the dashboard to create and manage browser automations
   - View automation history and results

## Support
For issues or questions about the application functionality, check the logs in the Replit console for detailed debugging information.
