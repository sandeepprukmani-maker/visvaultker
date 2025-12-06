# Browser Automation Assistant

## Overview

This is a browser automation tool that allows users to control web browsers through natural language prompts. The application uses Playwright MCP (Model Context Protocol) for browser automation and OpenAI's GPT-4 to translate user requests into executable browser actions. Users describe what they want to automate in plain language (e.g., "Go to google.com and search for weather"), and the system plans and executes the necessary browser interactions.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- React with TypeScript for UI components
- Vite for build tooling and development server
- Wouter for client-side routing
- TanStack Query (React Query) for server state management
- Tailwind CSS with shadcn/ui component library for styling

**Design System:**
- Based on shadcn/ui "new-york" theme with custom design guidelines
- Inspired by Linear, VS Code, and Vercel aesthetics
- Uses Inter for UI text and JetBrains Mono/Fira Code for code/logs
- Supports light/dark mode theming

**Component Structure:**
- Chat interface with message display and prompt input
- History sidebar showing past automation tasks
- Real-time WebSocket connection for task updates
- Empty state with example prompts for new users
- Status badges for connection state and task progress

**State Management:**
- WebSocket connection maintains real-time sync with backend
- React Query handles HTTP requests and caching
- Local state for UI interactions (sidebar toggle, active task selection)

### Backend Architecture

**Technology Stack:**
- Node.js with Express for HTTP server
- WebSocket (ws library) for real-time communication
- TypeScript with ESM module system

**Core Services:**

1. **MCP Client Integration** (`mcp-client.ts`)
   - Connects to Playwright MCP server via stdio transport
   - Manages browser automation session lifecycle
   - Provides tool invocation interface for browser actions
   - Runs Playwright in headless mode by default

2. **Automation Executor** (`automation-executor.ts`)
   - Orchestrates multi-step browser automation workflows
   - Executes planned actions sequentially
   - Broadcasts real-time progress updates via WebSocket
   - Handles action success/failure states

3. **AI Planning Service** (`openai-service.ts`)
   - Uses GPT-4 to convert natural language to structured action plans
   - Defines available browser operations (navigate, click, type, screenshot, etc.)
   - Returns JSON action sequences with tool names and arguments
   - Includes contextual guidelines for common automation patterns

4. **Storage Layer** (`storage.ts`)
   - In-memory storage implementation (MemStorage class)
   - Interface-based design (IStorage) allows for future database implementations
   - Manages automation tasks and their associated actions
   - CRUD operations for tasks and actions

**API Design:**
- RESTful endpoints for task management (`/api/tasks`)
- WebSocket endpoint (`/ws`) for real-time updates
- Task creation returns immediately while execution happens asynchronously
- Connection status tracking for MCP server availability

**Data Flow:**
1. User submits prompt via frontend
2. Backend creates task record with "pending" status
3. OpenAI generates action plan from natural language
4. Actions execute sequentially via MCP
5. Progress updates broadcast to connected WebSocket clients
6. Task completes with success/error status and optional summary

### External Dependencies

**Third-Party Services:**

1. **OpenAI API**
   - Model: GPT-4 (configured as "gpt-4o")
   - Purpose: Natural language to browser action planning
   - Requires: `OPENAI_API_KEY` environment variable
   - Used for: Converting user prompts to structured automation sequences

2. **Playwright MCP Server**
   - Package: `@playwright/mcp@latest`
   - Execution: Spawned as child process via npx
   - Transport: stdio (stdin/stdout communication)
   - Features: Browser control via accessibility tree (not pixel-based)
   - Available tools: navigate, click, type, screenshot, snapshot, select_option, hover, evaluate, press_key, fill_form

**Database:**
- Currently uses in-memory storage (Map-based)
- Drizzle ORM configured for PostgreSQL migration path
- Schema defined in `shared/schema.ts` using Zod
- Database URL expected via `DATABASE_URL` environment variable (for future use)

**UI Component Libraries:**
- Radix UI primitives for accessible components
- shadcn/ui as design system layer
- Lucide React for iconography

**Build and Development Tools:**
- Vite for frontend bundling with HMR
- esbuild for server-side bundling (production)
- TypeScript for type safety across stack
- Tailwind CSS with PostCSS for styling

**Development Environment:**
- Replit-specific plugins for runtime error overlay, cartographer, and dev banner
- Custom build script that bundles client and server separately
- Static file serving in production, Vite middleware in development