# AI Browser Automation Platform

## Overview
This project is an AI-powered browser automation web application built with Flask (Python) and Playwright. It enables users to automate web tasks using natural language instructions, providing a comprehensive platform for executing and managing these tasks. The platform offers a significant improvement in automation execution speed, robust script generation and healing capabilities, and a user-friendly interface for managing automation history and configurations. The business vision is to provide a highly efficient and reliable tool for web automation, appealing to users who need to streamline repetitive online tasks with minimal coding effort.

## User Preferences
I prefer clear, concise explanations and a direct communication style. I appreciate iterative development and want to be involved in major architectural decisions. Please ensure that all changes are thoroughly explained, and ask for my approval before implementing significant modifications. I value robust, production-ready code with good error handling and retry mechanisms.

## System Architecture
The application features a Flask (Python) backend with SQLite for database management and a pure JavaScript frontend with a dark theme and responsive design.

**UI/UX Decisions:**
- Dark theme UI
- Responsive design
- Real-time automation dashboard
- Clean interfaces for displaying automation prompts, logs, and screenshots.
- Clear visual indicators for script status (e.g., "Active Version", info banners).

**Technical Implementations:**
- **Backend:** Flask 3.1.2, Flask-SQLAlchemy, SQLAlchemy 2.0.44.
- **Frontend:** Vanilla JavaScript, HTML templates (`app/templates/`), static assets (`app/static/`).
- **Database:** SQLite for development, supporting PostgreSQL for production.
- **Performance Optimization:** Persistent Playwright wrapper with `PersistentPlaywrightClient` for 5-10x performance improvement by eliminating Node.js subprocess overhead and reusing browser instances.
- **Intelligent Dropdown Handling:** Both automation engines support native HTML `<select>`, custom JavaScript dropdowns (Material-UI, Ant Design), searchable dropdowns, long lists with scrolling, and multi-select.
- **Execution History:** Stores screenshots, execution logs, generated Python Playwright scripts, and automatically healed scripts for each execution.
- **Real-Time Live Execution Logs:** Concise, one-liner logs with auto-scrolling for immediate feedback.

**Feature Specifications:**
- **Three-Agent Python Code Generation System:**
    - **StrictModeLocatorEngine:** Generates locators using data-testid, ARIA roles, unique attributes, text content, and CSS selectors.
    - **PlannerAgent:** Explores applications and generates structured YAML automation plans with locator validation.
    - **GeneratorAgent:** Synthesizes production-ready, asynchronous Python Playwright code with error handling and retry logic.
    - **HealerAgent:** Analyzes Playwright trace files, identifies broken locators, and patches code.
- **Smart Script Execution from History:** Allows execution of scripts from history, prioritizing healed versions and offering automatic re-healing upon failure.
- **Verification & Validation Enforcement:** Detects verification keywords in prompts, instructs LLMs to report pass/fail, and flags verification failures.

**System Design Choices:**
- **Core Services:**
    - `Engine Orchestrator` (`app/services/engine_orchestrator.py`)
    - `Browser Use Engine` (`app/engines/browser_use/`)
    - `Playwright MCP` (`app/engines/playwright_mcp/`)
- **Project Structure:** Clear separation of concerns with dedicated directories for engines, routes, services, static assets, templates, utilities, and models.
- **Configuration:** Managed via `config/config.ini` for browser performance, MCP server mode (`always_run`), max steps, and retry mechanisms.
- **Privacy & Security:** Telemetry and cloud sync disabled, secure session management, CORS configuration, and OAuth support.

## External Dependencies
- **Browser Automation Libraries:**
    - Playwright (1.55.0)
    - browser-use library (0.9.1)
- **AI/LLM Providers:**
    - OpenAI GPT-4.1
    - Anthropic Claude
    - Google Gemini
    - Groq
- **Database:**
    - SQLite (for development)
    - PostgreSQL (supported for production)
- **Playwright MCP Server:** A Node.js component located in `integrations/playwright_mcp_node/`.
- **OAuth Integration:** Supports external OAuth providers for AI feature authentication, configurable via environment variables (`OAUTH_TOKEN_URL`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_GRANT_TYPE`, `OAUTH_SCOPE`, `GW_BASE_URL`).