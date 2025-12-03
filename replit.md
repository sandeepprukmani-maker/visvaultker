# Eko Web Automation Application

## Overview

Eko is an AI-powered web automation platform that transforms natural language prompts into executable multi-step workflows. Users describe automation tasks in plain English, and the system generates, visualizes, and executes workflows using AI models (Anthropic Claude or OpenAI GPT-4o-mini). The application provides real-time execution monitoring, workflow history, model selection, and a modern, gradient-accented UI built with React and shadcn/ui components.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework & Routing**
- React 18 with TypeScript for type safety
- Wouter for lightweight client-side routing
- Vite as the build tool and development server
- Single-page application (SPA) with a simple two-route structure: Home and NotFound

**State Management**
- TanStack Query (React Query) for server state management and caching
- Local React state (useState) for UI state and application flow
- Polling mechanism for real-time execution updates using setInterval

**UI Component System**
- shadcn/ui component library (Radix UI primitives) for accessible, customizable components
- Tailwind CSS for utility-first styling with custom design tokens
- Custom theme system supporting light/dark modes with localStorage persistence
- Material Design principles with modern gradient accents (purple-to-blue)
- Design guidelines emphasize clarity, progressive disclosure, and real-time feedback

**Key Design Decisions**
- Chose shadcn/ui over pre-built component libraries to maintain full design control while ensuring accessibility
- Polling for execution updates instead of WebSockets to reduce infrastructure complexity (simpler deployment, no persistent connections)
- Inline workflow visualization to provide immediate user feedback without requiring navigation

### Backend Architecture

**Server Framework**
- Express.js for HTTP server and API routing
- TypeScript with ES modules for modern JavaScript features
- Development server uses Vite middleware for hot module replacement (HMR)

**API Structure**
- RESTful endpoints under `/api` prefix:
  - `POST /api/workflow/generate` - Generate workflow from prompt
  - `POST /api/workflow/execute` - Execute a workflow
  - `POST /api/workflow/control` - Control execution (pause/resume/cancel)
  - `GET /api/executions` - Retrieve execution history
  - `DELETE /api/executions/:id` - Delete execution record

**Workflow Engine**
- Sequential step execution with dependency tracking
- Support for multiple tool types: browser, file, search, database, code
- Execution state machine: planning → ready → running → (paused) → completed/failed/cancelled
- In-memory execution control map for managing pause/cancel operations

**Storage Layer**
- In-memory storage implementation (MemStorage) for development
- Interface-based design (IStorage) allows easy swap to database-backed storage
- Drizzle ORM configured for PostgreSQL (via Neon serverless driver)
- Schema defined in shared directory for type safety across client/server

**Browser Automation**
- Playwright with Chromium for real browser automation
- Per-execution browser contexts (isolated, no shared state between concurrent workflows)
- Headless browser mode for server-side execution
- Smart step parsing to determine browser actions from step names/descriptions:
  - Navigation: detects "navigate", "open", "go to", "visit" and extracts URLs
  - Text input: detects "search", "type", "enter", "input" and finds search fields
  - Click/Submit: detects "submit", "click", "press" and triggers appropriate actions
  - Data extraction: detects "extract", "get", "read", "scrape" and captures page text
  - Screenshots: captures page state when requested
- Browser lifecycle management with proper cleanup on success, failure, or cancellation

**Key Design Decisions**
- In-memory storage initially to reduce deployment complexity; production should use PostgreSQL
- Per-execution Playwright browser instances ensure workflow isolation and prevent race conditions
- Shared schema directory ensures type consistency between frontend and backend
- Server-side build bundles common dependencies to reduce cold start times

### Data Models

**Workflow Schema**
```typescript
{
  name: string
  description?: string
  steps: WorkflowStep[]
}
```

**WorkflowStep Schema**
```typescript
{
  id: string
  name: string
  description?: string
  status: "pending" | "running" | "completed" | "failed" | "paused"
  tool?: "browser" | "file" | "search" | "database" | "code"
  dependencies?: string[]
  result?: string
  error?: string
}
```

**Execution Schema**
```typescript
{
  id: string
  prompt: string
  workflow: Workflow (JSONB)
  status: ExecutionStatus
  logs: LogEntry[] (JSONB)
  createdAt?: Date
  updatedAt?: Date
}
```

**Database Schema** (Drizzle ORM)
- Users table: Basic authentication structure (not actively used)
- Executions table: Stores workflow executions with JSONB for workflow/logs
- PostgreSQL dialect configured for production deployment

## External Dependencies

### AI Services
- **Anthropic Claude API** (`@anthropic-ai/sdk`)
  - Model: `claude-sonnet-4-20250514`
  - Used for: Generating workflow plans from natural language prompts
  - Requires: `ANTHROPIC_API_KEY` environment variable
  - Integration: Direct SDK calls with structured JSON output parsing

- **OpenAI API** (`openai`)
  - Model: `gpt-4o-mini`
  - Used for: Alternative workflow generation with JSON response format
  - Requires: `OPENAI_API_KEY` environment variable
  - Integration: Chat completions with json_object response format

- **Model Selection**
  - Users can choose between Anthropic Claude and OpenAI GPT-4o-mini in the UI
  - Model selector dropdown in prompt input area
  - Falls back to mock workflows if no API key is configured for selected model

### Database
- **Neon Serverless PostgreSQL** (`@neondatabase/serverless`)
  - Connection pooling for serverless environments
  - Configured via `DATABASE_URL` environment variable
  - Used with Drizzle ORM for type-safe database operations
  - Session storage: `connect-pg-simple` for Express sessions

### UI Component Libraries
- **Radix UI** - Accessible component primitives
  - Accordion, Dialog, Dropdown, Popover, Sheet, Tabs, Toast, Tooltip
  - Provides keyboard navigation and ARIA attributes
- **shadcn/ui** - Pre-styled Radix components with Tailwind CSS
- **Lucide React** - Icon library for consistent iconography

### Development Tools
- **Vite** - Build tool with HMR for development
- **ESBuild** - Fast JavaScript bundler for production builds
- **TypeScript** - Type safety across full stack
- **Drizzle Kit** - Database migration tool

### Styling
- **Tailwind CSS** - Utility-first CSS framework
- **PostCSS** with Autoprefixer for CSS processing
- Custom design tokens defined in `tailwind.config.ts`
- CSS variables for theme customization (light/dark modes)

### Build Configuration
- Custom build script bundles allowlisted dependencies (reduces syscalls, improves cold start)
- Separate client and server builds
- Development uses Vite dev server with Express middleware mode
- Production serves static assets from Express