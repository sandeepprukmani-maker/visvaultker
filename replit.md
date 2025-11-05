# AI Browser Automation

## Overview
This project is an AI-powered web automation application built with Flask and Playwright, designed to provide a web interface for automating browser tasks using AI agents. Its purpose is to enable users to easily create and manage complex web automations. The application supports multiple AI engines for flexible automation and can generate reusable Python Playwright scripts. It emphasizes security, privacy, and state persistence, making it suitable for various automation needs.

## User Preferences
- **AI Model**: Configured to use `gpt-4.1-2025-04-14-eastus-dz` for all AI operations
  - Model is read from `config/config.ini` and applied across all engines (browser-use, Playwright MCP, and all three agents: Planner, Generator, Healer)

## System Architecture
The application uses Python 3.12 with the Flask web framework, SQLite for local data storage, and Playwright with Chromium for browser automation. It integrates with a Node.js-based Playwright MCP server for enhanced automation capabilities.

### Key Features
- **Browser Automation**: AI-guided web browsing actions.
- **Multiple AI Engines**: Supports `browser-use` and `Playwright MCP`.
- **Code Generation**: Both engines can generate reusable Python Playwright scripts with accurate locators. The Playwright MCP engine uses a three-agent system (Planner → Generator → Healer) for robust code generation with validated, self-healing locators.
- **Web Interface**: User-friendly dashboard for managing automations.
- **Security**: API key authentication, rate limiting, and CORS protection.
- **Privacy-First**: No telemetry or cloud sync by default.
- **State Persistence**: Ability to save and restore browser states.
- **Screenshot & PDF Generation**: Capture and display of automation results.

### Project Structure
The codebase is organized into logical directories:
- `app/`: Contains the Flask application, including engines, middleware, routes, services, static assets, templates, and utilities.
- `auth/`: Handles OAuth authentication.
- `config/`: Stores configuration files.
- `integrations/`: Manages external integrations, specifically the Playwright MCP Node.js server.
- `instance/`: Used for SQLite database storage.
- `main.py`: The application's entry point.
- `requirements.txt`: Lists Python dependencies.

### Configuration
- **Environment Variables**: OAuth credentials for AI features (e.g., `OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`) and security settings (`SESSION_SECRET`, `API_KEY`) are managed via Replit Secrets.
- **Application Configuration**: Detailed settings for browser, AI models, logging, performance, and advanced features are controlled through `config/config.ini`.

### Database
- **Type**: SQLite, located at `instance/automation_history.db`.
- **Management**: Tables are automatically created on startup, and data is included in Replit snapshots.

## External Dependencies
- **Python Packages**:
    - `Flask`: Web framework.
    - `Playwright`: Browser automation library.
    - `SQLAlchemy`: Database ORM.
    - `Gunicorn`: Production WSGI server.
    - `Anthropic`, `OpenAI`, `Google GenAI`: SDKs for various AI providers.
- **Node.js Packages**:
    - `@playwright/mcp`: Playwright MCP server.
    - `playwright`: Browser automation library (Node.js version).
- **System Dependencies**:
    - Chromium browser dependencies (e.g., X11, Mesa, Cairo, Pango) are installed to support Playwright.