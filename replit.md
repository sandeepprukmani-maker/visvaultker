# Stagehand Automation Studio

## Overview

Stagehand Automation Studio is a browser automation code generator that allows users to create web automation scripts using natural language prompts. The application features an intelligent unified interface where users describe their automation task in plain English, including the website URL and desired actions. The system automatically extracts the URL, analyzes the prompt, and selects the appropriate automation mode (act, observe, extract, or agent) based on the task description. It provides live execution logs via WebSocket streaming and generates production-ready TypeScript code. Its primary purpose is to bridge the gap between brittle selector-based automation and unpredictable AI agents, providing a developer-friendly tool that combines AI capabilities with code precision for web automation.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (November 9, 2025)

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

The frontend is built with React and TypeScript, bundled by Vite. It uses `wouter` for routing, `shadcn/ui` (built on Radix UI and styled with Tailwind CSS) for UI components, and `TanStack Query` for server state management. The design system incorporates Inter and JetBrains Mono fonts, a custom HSL-based color scheme for light/dark modes, and responsive layouts. Key components include `UnifiedAutomationInput`, `ExecutionLog`, `CodeOutput`, and `Header`. The application uses a custom `useWebSocket` hook for managing real-time WebSocket connections with automatic reconnection and session resubscription.

### Backend Architecture

The backend runs on Node.js with Express.js and TypeScript. It features both legacy (`/api/automate`) and unified (`/api/automate-unified`) REST endpoints for processing automation requests. The unified endpoint uses an intelligent router (`server/intelligent-router.ts`) to parse natural language prompts, extract URLs, and determine optimal automation modes. WebSocket support (`server/websocket.ts`) enables real-time log broadcasting to connected clients. The request flow involves Zod validation, prompt analysis, Stagehand browser automation initialization, step-by-step execution with live log streaming, and TypeScript code generation. The core automation engine is the `@browserbasehq/stagehand` library, supporting 'act', 'observe', 'extract', and 'agent' modes with local browser automation and configurable AI models.

### Data Storage Solutions

The application uses an in-memory storage implementation (MemStorage class) for current operations. It is configured for PostgreSQL using `Drizzle ORM` and `@neondatabase/serverless` for future production deployments, with schema definitions in `shared/schema.ts`. Data models include User, automation request/response schemas, and log entries.

## External Dependencies

- **Browser Automation**: `@browserbasehq/stagehand` (v2.5.0) for AI-powered browser control.
- **Database & ORM**: `Drizzle ORM` (v0.39.1) for type-safe SQL, `Neon Database Serverless` for PostgreSQL connectivity.
- **UI Framework**: `Radix UI` for accessible components, `Tailwind CSS` for styling, `shadcn/ui` for pre-built components.
- **Form & Validation**: `React Hook Form` and `Zod` (with `drizzle-zod`) for form management and schema validation.
- **API & State Management**: `TanStack React Query` (v5.60.5) for server state, `Express.js` for the web server.
- **Development Tools**: `Vite` for development, `tsx` for TypeScript execution, `esbuild` for production bundling.
- **Session Management**: `connect-pg-simple` for PostgreSQL session storage.
- **AI Model Providers**: Google Gemini, OpenAI, Anthropic (via API keys).
- **BrowserBase**: (Optional) `BROWSERBASE_API_KEY`, `BROWSERBASE_PROJECT_ID`.