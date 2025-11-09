# VisionVault - AI-Powered Browser Automation

## Overview

VisionVault (formerly Stagehand Automation Studio) is an AI-powered browser automation platform that transforms natural language instructions into executable browser automations and generates rerunnable Playwright code with XPath locators. The application features an intelligent unified interface where users describe their automation task in plain English, including the website URL and desired actions. The system automatically extracts the URL, analyzes the prompt, and selects the appropriate automation mode (act, observe, extract, or agent) based on the task description. It provides live execution logs via WebSocket streaming and generates production-ready TypeScript code. Its primary purpose is to bridge the gap between brittle selector-based automation and unpredictable AI agents, providing a developer-friendly tool that combines AI capabilities with code precision for web automation.

## User Preferences

Preferred communication style: Simple, everyday language.

## Replit Environment Setup (November 9, 2025)

**Project successfully imported and configured for Replit:**
- ✅ PostgreSQL database provisioned with pgvector extension
- ✅ Database schema pushed using Drizzle ORM
- ✅ Node.js dependencies installed
- ✅ Server configured to bind to 0.0.0.0:5000 (required for Replit proxy)
- ✅ Vite dev server configured with allowedHosts: true for iframe preview
- ✅ Workflow configured for development server on port 5000
- ✅ Deployment settings configured (autoscale with build and run commands)
- ✅ Application tested and running successfully

**Environment Variables Required:**
- `DATABASE_URL` - PostgreSQL connection string (auto-provisioned)
- **For Browser Automation (Required):**
  - `OPENAI_API_KEY` - OpenAI API key for Stagehand automation models
  - OR any other AI model API key supported by Stagehand (Anthropic, etc.)
- **For Semantic Caching (Optional):**
  - `GOOGLE_AI_API_KEY` - Google Gemini API key for text embeddings and semantic cache
  - `DISABLE_EMBEDDINGS=true` - Explicitly disable embedding features if needed
- **For Cloud Browser (Optional):**
  - `BROWSERBASE_API_KEY` - For cloud browser automation
  - `BROWSERBASE_PROJECT_ID` - BrowserBase project ID
- `NODE_ENV` - Set to "development" for dev mode

**Note:** Semantic caching (text embeddings) is now optional. The core automation and code generation features work without `GOOGLE_AI_API_KEY`. When embeddings are disabled, the system will skip cache lookups and continue with normal automation execution.

## Recent Changes (November 9, 2025)

### Embeddings Made Optional ✅ COMPLETE
- **Feature Flag System**: Text embeddings are now optional and automatically disabled when `GOOGLE_AI_API_KEY` is not available
- **Graceful Degradation**: Semantic cache lookups return null when embeddings are disabled, automation continues normally
- **Zero-Impact on Core Features**: Automation and code generation work without embeddings - only semantic caching is affected
- **Clear Logging**: System logs once when embeddings are disabled: "ℹ️ Embeddings disabled - semantic caching unavailable"
- **Implementation**: Updated `server/semantic-cache.ts` to check for API key availability and short-circuit embedding operations
- **Database Compatibility**: History storage works with null embeddings, pgvector column accepts null values

### Rerunnable Code Generation System ✅ COMPLETE
- **Locator-based Code Generator**: Converts Stagehand automation steps into production-ready TypeScript code that can run without LLM inference
- **XPath Preservation**: All selectors maintained as native Playwright XPath using `xpath=` prefix (no broken CSS conversion)
- **Iframe Support**: Full support for nested iframes using `page.deepLocator()` with chained XPath segments
- **String Safety**: Comprehensive escaping for all user inputs (URLs, prompts, selectors, values) preventing code injection
- **Step Capture**: Intelligent step recording during execution, including fallback scenarios where selectors aren't available
- **Database Storage**: Both LLM-generated code and rerunnable locator-based code stored in `automationHistory` table
- **UI Display**: Generated scripts shown in Home page with syntax highlighting and copy functionality
- **Code Generation Engine**: `server/locator-generator.ts` - Transforms captured steps into executable TypeScript using Stagehand's locator API

### History and Cache Management System
- **Screenshot Capture**: Automatically captures full-page screenshots before closing browser sessions using Playwright's `page.screenshot()` method
- **Execution History**: Complete history of all automation runs with timestamps, prompts, models used, execution logs, and screenshots stored in PostgreSQL
- **History Management**: Users can view, reexecute, and delete individual history items or clear all history through dedicated UI
- **Semantic Cache Viewer**: View cached automation results with Gemini embeddings for intelligent prompt matching (0.85 similarity threshold)
- **Sidebar Navigation**: Clean navigation between Home, History, and Cache pages using shadcn sidebar components
- **API Endpoints**: 
  - `GET/DELETE /api/history` - List/clear all execution history
  - `DELETE /api/history/:id` - Delete specific history item
  - `POST /api/history/:id/reexecute` - Reexecute previous automation
  - `GET /api/cache` - View semantic cache entries

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

The frontend is built with React and TypeScript, bundled by Vite. It uses `wouter` for routing, `shadcn/ui` (built on Radix UI and styled with Tailwind CSS) for UI components, and `TanStack Query` for server state management. The design system incorporates Inter and JetBrains Mono fonts, a custom HSL-based color scheme for light/dark modes, and responsive layouts. Key pages include `Home` (automation input), `History` (execution history with screenshots), `Cache` (semantic cache viewer), and `Settings` (model configuration). Navigation is managed through a collapsible sidebar using shadcn's `Sidebar` components. The application uses a custom `useWebSocket` hook for managing real-time WebSocket connections with automatic reconnection and session resubscription.

### Backend Architecture

The backend runs on Node.js with Express.js and TypeScript. It features both legacy (`/api/automate`) and unified (`/api/automate-unified`) REST endpoints for processing automation requests. The unified endpoint uses an intelligent router (`server/intelligent-router.ts`) to parse natural language prompts, extract URLs, and determine optimal automation modes. WebSocket support (`server/websocket.ts`) enables real-time log broadcasting to connected clients. The request flow involves Zod validation, prompt analysis, Stagehand browser automation initialization, step-by-step execution with live log streaming, and TypeScript code generation. The core automation engine is the `@browserbasehq/stagehand` library, supporting 'act', 'observe', 'extract', and 'agent' modes with local browser automation and configurable AI models.

### Data Storage Solutions

The application uses an in-memory storage implementation (MemStorage class) for current operations. It is configured for PostgreSQL using `Drizzle ORM` and `@neondatabase/serverless` for production deployments, with schema definitions in `shared/schema.ts`. Data models include:
- **automationHistory**: Stores execution history with prompt, mode, model, logs (JSONB), generated code, screenshots (base64), and Gemini embeddings (768-dimensional vectors via pgvector extension)
- **User**: Basic user authentication schema
- Screenshot storage uses base64-encoded data URIs stored in text fields for simplicity
- Semantic caching leverages cosine similarity on Gemini embeddings with 0.85 threshold for intelligent prompt matching

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