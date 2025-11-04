# AI Browser Automation

## Overview
This is an AI-powered browser automation web application built with Flask and Playwright. It provides a web interface for automating browser tasks using AI agents.

**Current Status**: Fully configured and running in Replit environment
**Last Updated**: November 4, 2025

## Project Architecture

### Technology Stack
- **Backend**: Python 3.11 with Flask web framework
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

Both automation engines now generate **reusable Python Playwright scripts** from executed automations:

### Browser-Use Engine
- **LLM-Powered Generation**: Analyzes natural language execution steps using AI
- **Intelligent Locators**: Generates strict, maintainable locators following best practices:
  1. `get_by_role()` with name (highest priority)
  2. `get_by_placeholder()` for inputs
  3. `get_by_label()` for form fields
  4. `get_by_text()` for text elements
  5. CSS/data-testid selectors (last resort)
- **Production-Ready**: Complete async scripts with error handling, retries (3x), logging, timeouts
- **Automatic**: Code generated automatically after successful execution
- **Fallback**: Template-based generation if LLM unavailable

### Playwright MCP Engine
- **Three-Agent System**: Planner → Generator → Healer
- **Validated Locators**: Uses strict-mode locator engine with element validation
- **Self-Healing**: Healer agent can automatically fix failing scripts using trace analysis
- **Advanced**: Supports complex workflows with state management

### Usage
Generated code is automatically saved to the database and accessible via:
- Web interface history view
- API response (`generated_code` field)
- Database `GeneratedScript` table

All generated scripts are standalone, executable, and ready for CI/CD integration.

## User Preferences
None recorded yet.

## Recent Changes
- **Nov 4, 2025**: Added code generation to browser-use engine
  - Created BrowserUseCodeGenerator module with LLM-powered code generation
  - Integrated automatic code generation after successful executions
  - Updated API to save generated code from both engines to database
  - Browser-use now produces reusable Python Playwright scripts with strict locators
- **Nov 4, 2025**: Initial Replit setup
  - Installed Python 3.11 and Node.js 20
  - Installed all Python dependencies from requirements.txt
  - Installed Node.js dependencies for Playwright MCP
  - Installed Chromium browser for Playwright
  - Installed system dependencies for browser support
  - Created .gitignore for Python and Node.js
  - Configured Flask workflow on port 5000
  - Configured deployment with Gunicorn
  - Application running successfully

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
