# AI Browser Automation

## Overview
This project is an AI-powered web automation application built with Flask, designed to provide a web interface for automating browser tasks using AI agents. Its purpose is to enable users to easily create and manage complex web automations. The application uses the browser-use engine for AI-powered automation with Chromium. It emphasizes security, privacy, and state persistence, making it suitable for various automation needs.

## User Preferences
- **AI Model**: Configured to use `gpt-4.1-2025-04-14-eastus-dz` for all AI operations
  - Model is read from `config/config.ini` and applied to the browser-use engine

## System Architecture
The application uses Python 3.12 with the Flask web framework, SQLite for local data storage, and the browser-use engine (which leverages Chromium) for browser automation.

### Key Features
- **Browser Automation**: AI-guided web browsing actions using the browser-use engine.
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
    - `browser-use`: AI-powered browser automation engine (includes Playwright internally).
    - `SQLAlchemy`: Database ORM.
    - `Gunicorn`: Production WSGI server.
    - `Anthropic`, `OpenAI`, `Google GenAI`: SDKs for various AI providers.
- **System Dependencies**:
    - Chromium browser dependencies (e.g., X11, Mesa, Cairo, Pango) are installed to support browser automation.