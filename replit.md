# AutomateAI - Enterprise AI Browser Automation Platform

## Overview
An enterprise-grade AI browser automation platform built with Python and TypeScript, featuring centralized LLM management, multi-modal intelligence, task teaching system, and intelligent workflow orchestration.

## Architecture

### Backend (Python FastAPI)
- **Port**: 8000
- **Location**: `python_backend/`
- **Features**:
  - Centralized LLM manager supporting GPT-4, Claude 3.5 Sonnet, and Gemini
  - Playwright-based browser automation with anti-detection and stealth mode
  - Intelligent website profiling with DOM mapping and visual AI analysis
  - Task teaching system with natural language learning
  - Workflow orchestration engine with conditional logic and data passing

### Frontend (React + Vite + Express)
- **Port**: 5000
- **Location**: `client/src/`
- **Features**:
  - Dashboard with analytics and stats
  - Task library for managing learned automations
  - Workflow builder for chaining tasks
  - Real-time execution monitoring
  - Settings for LLM configuration

### Database
- **Type**: PostgreSQL (Neon)
- **Schema**: Defined in `shared/schema.ts`
- **Tables**:
  - `tasks` - Taught automation tasks
  - `workflows` - Chains of tasks
  - `website_profiles` - Learned website structures
  - `executions` - Execution history
  - `llm_usage` - LLM API usage and cost tracking
  - `workflow_tasks` - Join table for workflow-task relationships

## Setup Instructions

### 1. API Keys (Required for AI Features)

The platform requires API keys for at least one LLM provider. Set these environment variables:

```bash
# OpenAI (GPT-4, GPT-4 Vision)
OPENAI_API_KEY=sk-...

# Anthropic (Claude 3.5 Sonnet)
ANTHROPIC_API_KEY=sk-ant-...

# Google AI (Gemini)
GOOGLE_AI_API_KEY=...
```

**Note**: If no API keys are configured, AI-dependent features (task teaching, website profiling) will return placeholder messages instead of crashing.

### 2. Database Setup

The database is already provisioned and configured. Schema is automatically synced on startup.

### 3. Running the Application

Both servers start automatically via the workflow:

```bash
bash run-all.sh
```

This starts:
- Python FastAPI backend on `http://localhost:8000`
- Express + Vite frontend on `http://localhost:5000`

Access the application at: `http://localhost:5000`

## Features

### 1. Centralized LLM Management
- Single unified interface for all AI model interactions
- Automatic provider routing based on task complexity
- Smart model selection (vision → GPT-4V/Claude Vision, reasoning → Claude, speed → Gemini)
- Automatic fallback if primary model fails
- Cost tracking and usage analytics

### 2. Browser Automation
- Playwright-based with anti-detection
- Stealth mode to avoid bot detection
- Session persistence and cookie management
- Safe interaction engine (avoids destructive actions)

### 3. Intelligent Website Profiling
- Deep interactive exploration (hovers, clicks, scrolls)
- Visual AI analysis using vision models
- Self-learning DOM mapper
- Semantic understanding and element categorization
- Profile versioning to track UI changes

### 4. Task Teaching System
- Demonstrate tasks once, AI learns forever
- Natural language task names and descriptions
- Parametric tasks with variables
- Task library with categorization and tagging
- Version control for learned automations

### 5. Workflow Orchestration
- Chain multiple tasks into sequential workflows
- Conditional branching and loops
- Smart data passing between tasks
- Parallel execution support
- Error handling and retry logic

### 6. Monitoring & Analytics
- Real-time execution dashboard
- Success rate tracking
- Performance metrics
- AI confidence scores
- LLM cost tracking per model

## Configuration

LLM settings and browser automation parameters are configured in `python_backend/config.yaml`:

- **LLM Providers**: Model names, capabilities, costs, priorities
- **Task Routing**: Which models to use for different task types
- **Browser Settings**: Headless mode, viewport size, timeouts
- **Exploration Settings**: Maximum depth, safe actions, avoid patterns

## API Endpoints

### Python Backend (Port 8000)

- `GET /` - API information
- `GET /api/tasks` - List all tasks
- `POST /api/tasks/teach` - Teach a new task
- `POST /api/tasks/{id}/execute` - Execute a task
- `GET /api/workflows` - List all workflows
- `POST /api/workflows` - Create a workflow
- `POST /api/workflows/{id}/execute` - Execute a workflow
- `POST /api/website-profiles` - Profile a website
- `GET /api/analytics/overview` - Get analytics overview
- `GET /api/analytics/llm-usage` - Get LLM usage stats

### Frontend Proxy (Port 5000)

All Python API endpoints are proxied through `/api/python/*` to avoid CORS issues.

## Development Guidelines

### Adding New Features

1. **Backend**: Add services to `python_backend/services/`
2. **API**: Add endpoints to `python_backend/main.py`
3. **Frontend**: Create components in `client/src/components/`
4. **Pages**: Add pages to `client/src/pages/`

### Database Changes

1. Update schema in `shared/schema.ts`
2. Run `npm run db:push` to sync to database
3. Use `--force` flag if data loss warning appears

### Testing

- Backend tests: `pytest` (coming soon)
- Frontend: Browser testing via Replit webview
- Integration: Test via frontend UI or API calls

## Project Structure

```
.
├── python_backend/           # Python FastAPI backend
│   ├── config.yaml          # LLM and automation config
│   ├── main.py              # FastAPI app and routes
│   └── services/            # Core services
│       ├── llm_manager.py   # Centralized LLM interface
│       ├── browser_automation.py
│       ├── website_profiler.py
│       ├── task_manager.py
│       └── workflow_engine.py
├── client/                  # React frontend
│   └── src/
│       ├── pages/           # Page components
│       ├── components/      # Reusable components
│       └── lib/             # Utilities
├── server/                  # Express backend
│   ├── index.ts             # Server entry
│   ├── routes.ts            # API proxy routes
│   └── storage.ts           # Storage interface
├── shared/                  # Shared types
│   └── schema.ts            # Database schema
└── run-all.sh               # Startup script

```

## Next Steps

1. **Add API Keys**: Configure at least one LLM provider in environment secrets
2. **Learn a Website**: Use "Learn a Website" to profile a site
3. **Create a Task**: Teach the AI to automate a specific action
4. **Build Workflows**: Chain tasks together for complex automations
5. **Monitor Usage**: Track LLM costs and execution analytics

## Recent Changes

- **2024-11-04**: Initial implementation of comprehensive automation platform
  - Database schema with all required tables
  - Python backend with FastAPI and all services
  - Frontend integration with Python API
  - Dual-server architecture working successfully
  - Graceful degradation when API keys not configured

## User Preferences

None specified yet. The platform is ready for customization based on user needs.
