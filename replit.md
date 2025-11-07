# AI Browser Automation

## Overview
This project is an AI-powered web automation application built with Flask, designed to provide a web interface for automating browser tasks using AI agents. Its purpose is to enable users to easily create and manage complex web automations. The application supports **two automation engines**: Browser Use (default) and Playwright MCP (advanced). It emphasizes security, privacy, and state persistence, making it suitable for various automation needs.

## Recent Changes (November 2025)
- **Playwright MCP Engine Added**: New automation engine using Playwright MCP server with AI agents
  - Supports both Claude and GPT-4o models
  - Automatic MCP server management via npx
  - Seamless engine switching through configuration UI
  - Uses Model Context Protocol for advanced browser automation

## User Preferences
- **AI Model**: Configured to use `gpt-4.1-2025-04-14-eastus-dz` for all AI operations
  - Model is read from `config/config.ini` and applied to both automation engines
- **Automation Engine**: Browser Use (default) or Playwright MCP
  - Configurable in `config/config.ini` under `[engine]` section
  - Switchable via Configuration page in the web interface

## System Architecture
The application uses Python 3.12 with the Flask web framework, SQLite for local data storage, and supports two automation engines for browser automation.

### Automation Engines

#### Browser Use Engine (Default)
- Uses the `browser-use` library for AI-powered automation
- Best for most tasks, simpler setup
- Direct Playwright integration
- Faster execution for simple tasks

#### Playwright MCP Engine (Advanced)
- Uses Playwright MCP (Model Context Protocol) server
- AI agents (Claude/GPT-4o) control browser via MCP tools
- More structured approach with tool-based automation
- Requires Node.js 20+ for MCP server
- Automatic server management via npx

### Key Features
- **Dual Engine Support**: Choose between Browser Use and Playwright MCP engines
- **Browser Automation**: AI-guided web browsing actions using advanced AI models
- **Web Interface**: User-friendly dashboard for managing automations
- **Security**: API key authentication, rate limiting, and CORS protection
- **Privacy-First**: No telemetry or cloud sync by default
- **State Persistence**: Ability to save and restore browser states
- **Screenshot & PDF Generation**: Capture and display of automation results

### Project Structure
The codebase is organized into logical directories:
- `app/`: Contains the Flask application, including engines, middleware, routes, services, static assets, templates, and utilities.
  - `app/engines/browser_use/`: Browser Use engine implementation
  - `app/engines/playwright_mcp/`: Playwright MCP engine implementation
    - `engine_mcp.py`: Main MCP engine
    - `mcp_client.py`: MCP server client
    - `ai_agents.py`: AI agents for automation
  - `app/services/engine_orchestrator.py`: Manages both engines
- `auth/`: Handles OAuth authentication.
- `config/`: Stores configuration files.
- `instance/`: Used for SQLite database storage.
- `main.py`: The application's entry point.
- `requirements.txt`: Lists Python dependencies.
- `package.json`: Node.js configuration for Playwright MCP server.

### Configuration
- **Environment Variables**: OAuth credentials for AI features (e.g., `OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`) and security settings (`SESSION_SECRET`, `API_KEY`) are managed via Replit Secrets.
  - For Playwright MCP: `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` (at least one required)
- **Application Configuration**: Detailed settings for browser, AI models, logging, performance, and advanced features are controlled through `config/config.ini`.
  - `[engine]` section: Select automation engine (`browser_use` or `playwright_mcp`)
  - Engine selection is also available via the Configuration page in the web interface

### Database
- **Type**: SQLite, located at `instance/automation_history.db`.
- **Management**: Tables are automatically created on startup, and data is included in Replit snapshots.

## External Dependencies
- **Python Packages**:
    - `Flask`: Web framework
    - `browser-use`: AI-powered browser automation engine (Browser Use engine)
    - `SQLAlchemy`: Database ORM
    - `Gunicorn`: Production WSGI server
    - `Anthropic`, `OpenAI`, `Google GenAI`: SDKs for various AI providers
    - `mcp`: Model Context Protocol library (for Playwright MCP engine)
    - `playwright`: Browser automation library (used by both engines)
- **Node.js Dependencies** (for Playwright MCP engine):
    - `@playwright/mcp`: Playwright MCP server (auto-installed via npx on first use)
    - Node.js 20+ is required for Playwright MCP engine
- **System Dependencies**:
    - Chromium browser dependencies (e.g., X11, Mesa, Cairo, Pango) are installed to support browser automation

## Setup Notes
- **Playwright MCP Engine**: The `@playwright/mcp` package is automatically installed on first use via npx. No manual npm install required.
- **Engine Switching**: Users can switch between Browser Use and Playwright MCP engines in the Configuration page without restarting the application.