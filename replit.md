# AI Browser Automation Platform

## Overview
This project is an AI-powered web application for automating browser tasks using natural language instructions. It provides a comprehensive platform for executing and managing browser automation, with a focus on ease of use, security, and robust execution. The application supports various automation engines and includes features like secure credential management, detailed execution history with script healing, and a user-friendly interface.

## User Preferences
The user prefers iterative development and expects the agent to ask before making major changes.

## System Architecture

### UI/UX Decisions
The application features a dark theme UI with a responsive design, providing a real-time automation dashboard. It uses pure JavaScript for the frontend, located in `app/templates/` and `app/static/`. Key pages include Dashboard, History, Configuration, Teaching Mode, Task Library, and Recall Mode.

### Technical Implementations
The backend is built with Flask 3.1.2 and Flask-SQLAlchemy, using SQLite for the database (PostgreSQL support for production). Browser automation is handled by the `browser-use` library (0.9.1) and Playwright (1.55.0) with a Node.js-based Playwright MCP (Model Context Protocol) integration.

**Core Features:**
- **Secure Credential Vault System**: Credentials are encrypted using AES-256 (Fernet) and stored in the database. Users can reference credentials in prompts using placeholders like `{{credential_name}}`. A CRUD UI for credential management is available at `/credentials`.
- **Intelligent Website Learning System**: The system automatically learns from every automation execution, storing website-specific patterns in the WebsiteKnowledgeBase. This includes:
    - **Automatic Pattern Recognition**: Learns login flows, search methods, form structures, and common UI elements
    - **Context Enhancement**: Automatically injects learned knowledge into prompts for faster, more accurate automations
    - **Success Tracking**: Monitors success rates per website and adapts strategies accordingly
    - **Sequential Reasoning**: Enhanced prompts guide engines through complex multi-step workflows intelligently
    - **Zero Manual Setup**: Works transparently with both engines - no configuration needed
- **Enhanced History Feature**: Each execution stores screenshots, detailed logs, generated Python Playwright scripts, and automatically "healed" scripts. Users can re-execute scripts from history, with healed scripts taking precedence.
- **Three-Agent Python Code Generation System (Playwright MCP Engine)**:
    - **StrictModeLocatorEngine**: Generates locators using a multi-strategy approach (data-testid, ARIA roles, unique attributes, CSS selectors).
    - **PlannerAgent**: Explores the app and generates structured YAML plans with validated locators.
    - **GeneratorAgent**: Synthesizes production-ready, asynchronous Python Playwright code with error handling and retry logic.
    - **HealerAgent**: Analyzes Playwright trace files to patch broken locators and actions.
- **Intelligent Dropdown Handling**: Both automation engines support native HTML `<select>`, custom JavaScript dropdowns (e.g., Material-UI), searchable dropdowns, long lists with scrolling, and multi-select options.
- **Verification & Validation**: The system detects verification keywords in prompts and enforces explicit reporting of verification pass/fail, automatically failing executions where verifications are not met.
- **Real-Time Live Execution Logs**: Both engines stream concise, step-by-step logs with auto-scrolling for immediate feedback.

### Feature Specifications
- **Automation Execution**: `POST /api/execute` endpoint to run instructions with specified engine and headless mode.
- **History Management**: API endpoints for retrieving, re-executing, and deleting history items.
- **Engine Management**: Endpoints for cleaning up engine resources and checking status.
- **Configuration**: Managed via `config/config.ini`, including browser performance, MCP server mode (persistent), max steps, and retry mechanisms.
- **Privacy & Security**: Telemetry and cloud sync are disabled. Secure session management and CORS configuration are in place. OAuth support is available for AI features.

### System Design Choices
The application is structured into `app/`, `integrations/`, `config/`, and `docs/` directories. Key components include `Engine Orchestrator` for managing automation engines, `Browser Use Engine`, and `Playwright MCP` for automation execution. Logging is detailed and configurable, with real-time output in the UI.

## External Dependencies

- **Database**: SQLite (development), PostgreSQL (production)
- **Browser Automation Libraries**: `browser-use` (0.9.1), `Playwright` (1.55.0)
- **AI/LLM Providers**: OpenAI (GPT-4.1), Anthropic (Claude), Google (Gemini), Groq
- **OAuth Provider**: Configurable via environment variables for AI feature authentication.
- **Playwright MCP Server**: A Node.js component for Playwright integration.