# AI Browser Automation Platform

A powerful web-based platform for automating browser tasks using natural language instructions. Built with Flask and Playwright.

## 🚀 Quick Start

The application is **already running** on Replit! Just open the preview to access the web interface.

### What's Working
✅ Flask web server running on port 5000  
✅ Database initialized (SQLite)  
✅ Playwright browsers installed  
✅ All dependencies configured  
✅ Privacy settings enabled (no telemetry)  

### Current Status
The app is running in **demo mode** without AI features. You can:
- View the web interface
- Explore the dashboard and UI
- See all available features

To enable AI automation features, you'll need to add OAuth credentials (see below).

## 📋 Features

- **Natural Language Automation** - Describe tasks in plain English
- **Multiple Engines** - Browser-use and Playwright MCP integration
- **Execution History** - Track all automation runs
- **Teaching Mode** - Interactive automation teaching
- **Task Library** - Save and reuse automation scripts
- **Performance Optimized** - Balanced for speed and reliability

## 🔧 Configuration (Optional)

### Enable AI Features

To use the AI automation capabilities, add these OAuth credentials via Replit Secrets:

- `OAUTH_TOKEN_URL` - Your OAuth provider endpoint
- `OAUTH_CLIENT_ID` - OAuth client ID
- `OAUTH_CLIENT_SECRET` - OAuth client secret  
- `OAUTH_GRANT_TYPE` - Grant type (usually `client_credentials`)
- `OAUTH_SCOPE` - Required OAuth scope
- `GW_BASE_URL` - Gateway API endpoint


## 📁 Project Structure

```
├── app/                 # Main application
│   ├── agents/         # AI agents (planner, generator, healer)
│   ├── engines/        # Automation engines
│   ├── routes/         # API endpoints
│   ├── templates/      # HTML templates
│   └── static/         # CSS, JavaScript
├── config/             # Configuration files
├── integrations/       # External integrations
├── docs/              # Documentation
└── main.py            # Application entry point
```

## 📖 Documentation

See [replit.md](replit.md) for complete documentation including:
- Architecture details
- API endpoints
- Configuration options
- Performance tuning
- Troubleshooting

## 🔒 Privacy & Security

- ✅ Telemetry disabled by default
- ✅ No cloud sync - all data stays local
- ✅ Session secrets auto-generated for dev
- ✅ CORS configured

## 🛠️ Tech Stack

- **Backend:** Python 3.11, Flask 3.1.2
- **Frontend:** Vanilla JavaScript, Dark theme UI
- **Database:** SQLAlchemy with SQLite
- **Automation:** Playwright 1.55.0, browser-use 0.9.1
- **AI:** Support for OpenAI, Anthropic, Google GenAI, Groq

## 📝 Notes

The LSP errors you might see in the editor are false positives - the application is running correctly. The language server cache will update automatically.

## 🚀 Deployment

The app is configured for deployment on Replit using:
- **Type:** Autoscale (stateless web app)
- **Server:** Gunicorn with 2 workers
- **Port:** 5000

---

**Need help?** Check the detailed documentation in [replit.md](replit.md) or the docs folder.
