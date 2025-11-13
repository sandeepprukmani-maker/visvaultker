# Stagehand Automation Studio

## Overview

Stagehand Automation Studio is a browser automation code generator that allows users to create web automation scripts using natural language prompts. The application features an intelligent unified interface where users describe their automation task in plain English, including the website URL and desired actions. The system automatically extracts the URL, analyzes the prompt, and selects the appropriate automation mode (act, observe, extract, or agent) based on the task description. It provides live execution logs via WebSocket streaming and generates production-ready TypeScript code. Its primary purpose is to bridge the gap between brittle selector-based automation and unpredictable AI agents, providing a developer-friendly tool that combines AI capabilities with code precision for web automation.

## User Preferences

Preferred communication style: Simple, everyday language.

## Replit Environment Setup (November 13, 2025)

### Configuration for Replit
- **Server Binding**: Updated to bind to `0.0.0.0:5000` for Replit's proxy environment
- **Vite Configuration**: Configured with `allowedHosts: ['all']` to work with Replit's iframe-based preview
- **Workflow**: Configured `dev` workflow running `npm run dev` on port 5000 with webview output
- **Deployment**: Set up as VM deployment (stateful) with build and start scripts
- **Playwright Browsers**: Chromium browser installed for automation (headless mode)
- **Database-Free Architecture**: PostgreSQL completely removed - no database dependency whatsoever

### Custom LLM Client Integration (November 13, 2025)
- **Custom LLM Client Only**: Application exclusively uses custom LLM client for both chat completions and embeddings
- **Dynamic OAuth Token Authentication**: API keys fetched dynamically via `fetch_token.py` script
- **Token Caching**: Tokens cached with automatic expiration and refresh (default 1 hour TTL)
- **Secure TLS**: All API requests use proper TLS certificate validation for security
- **Flexible Configuration**: Supports any OpenAI-compatible API endpoint (Azure OpenAI, Ollama, custom deployments)
- **Type Safety**: Fully compatible with Stagehand's LLMClient interface with proper TypeScript generics
- **Response Parsing**: Intelligent response parsing for structured outputs and element/action normalization
- **Environment Variables**:
  - `CUSTOM_LLM_API_ENDPOINT`: The API endpoint URL for your custom LLM (required)
  - `CUSTOM_LLM_MODEL_NAME`: The specific model name to use (default: `gpt-4o-1-2025-04-14-eastus-dz`)
  - `OPENAI_EMBEDDING_ENDPOINT`: OpenAI embeddings API endpoint (default: `https://api.openai.com/v1/embeddings`)
  - `OPENAI_EMBEDDING_MODEL`: Embedding model to use (default: `text-embedding-3-small`)
- **Token Fetching**: Customize `fetch_token.py` to implement your token fetching logic (OAuth, token service, etc.)

## Recent Changes (November 9, 2025)

### PostgreSQL Completely Removed (November 13, 2025)
- **Database-Free Architecture**: Completely removed all PostgreSQL dependencies and code
- **Removed Files**: server/db.ts, server/api-client.ts, server/semantic-cache.ts, drizzle.config.ts
- **Removed Packages**: @neondatabase/serverless, drizzle-orm, drizzle-kit, drizzle-zod, connect-pg-simple
- **Removed Features**: History tracking, semantic caching, cache viewing
- **Simplified Frontend**: Removed History and Cache pages, streamlined sidebar navigation to Home and Settings only
- **Clean Schema**: shared/schema.ts now contains only Zod validation schemas for automation requests/responses

### Unified Natural Language Automation System
- **Single Prompt Input**: Users now describe automation tasks in plain English without manually selecting modes or entering URLs separately
- **Intelligent URL Extraction**: System automatically detects and extracts URLs from prompts (supports both full URLs and domain names)
- **Smart Mode Selection**: Analyzes prompt keywords to automatically choose the best automation mode:
  - `act` - For single click/type/scroll actions
  - `observe` - For finding/locating elements
  - `extract` - For data extraction and scraping
  - `agent` - For multi-step workflows and complex tasks
- **Live WebSocket Updates**: Real-time execution log streaming during automation runs
- **Reconnection Resilience**: WebSocket automatically resubscribes to sessions after network interruptions, ensuring log continuity

## System Architecture

### Frontend Architecture

The frontend is built with React and TypeScript, bundled by Vite. It uses `wouter` for routing, `shadcn/ui` (built on Radix UI and styled with Tailwind CSS) for UI components, and `TanStack Query` for server state management. The design system incorporates Inter and JetBrains Mono fonts, a custom HSL-based color scheme for light/dark modes, and responsive layouts. Key pages include `Home` (automation input) and `Settings` (model configuration). Navigation is managed through a collapsible sidebar using shadcn's `Sidebar` components. The application uses a custom `useWebSocket` hook for managing real-time WebSocket connections with automatic reconnection and session resubscription.

### Backend Architecture

The backend runs on Node.js with Express.js and TypeScript. It features both legacy (`/api/automate`) and unified (`/api/automate-unified`) REST endpoints for processing automation requests. The unified endpoint uses an intelligent router (`server/intelligent-router.ts`) to parse natural language prompts, extract URLs, and determine optimal automation modes. WebSocket support (`server/websocket.ts`) enables real-time log broadcasting to connected clients. The request flow involves Zod validation, prompt analysis, Stagehand browser automation initialization, step-by-step execution with live log streaming, and TypeScript code generation. The core automation engine is the `@browserbasehq/stagehand` library, supporting 'act', 'observe', 'extract', and 'agent' modes with local browser automation and configurable AI models.

### Data Storage Solutions

The application is database-free and stateless. All automation executions are ephemeral - results are generated and displayed in real-time, with no persistent storage. The `shared/schema.ts` file contains only Zod validation schemas for automation requests and responses.

## External Dependencies

- **Browser Automation**: `@browserbasehq/stagehand` (v2.5.0) for AI-powered browser control.
- **UI Framework**: `Radix UI` for accessible components, `Tailwind CSS` for styling, `shadcn/ui` for pre-built components.
- **Form & Validation**: `React Hook Form` and `Zod` for form management and schema validation.
- **API & State Management**: `TanStack React Query` (v5.60.5) for server state, `Express.js` for the web server.
- **Development Tools**: `Vite` for development, `tsx` for TypeScript execution, `esbuild` for production bundling.
- **Session Management**: `express-session` with `memorystore` for in-memory session storage.
- **Custom LLM Integration**: Custom OAuth-based LLM client for chat completions and embeddings.
- **BrowserBase**: (Optional) `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`.