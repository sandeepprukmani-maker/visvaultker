# ZenSmart Executor

## Overview

ZenSmart Executor is a browser automation platform that converts natural language prompts into executable Playwright actions. The application uses Google's Gemini AI to interpret user requests and automatically generate browser automation code that performs tasks like navigating websites, filling forms, and extracting data.

The application follows a minimalist design philosophy inspired by Google's radical simplicity, focusing on a clean, prompt-driven interface where users can describe what they want to automate in plain language. The system handles the complexity of translating these requests into Playwright automation code and executes them in real-time with live progress updates.

**Status**: MVP Complete ✅
- Beautiful minimal UI with Google-inspired design
- Real-time browser automation via headless Playwright
- Gemini AI integration with optimized prompting
- WebSocket live updates (confirmed working)
- Secure whitelist-based code execution
- Action history and pre-built templates
- Token usage metrics dashboard

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework**: React 18 with TypeScript, built using Vite for fast development and optimized production builds.

**UI Component System**: Shadcn/ui with Radix UI primitives for accessible, composable components. The design system uses the "new-york" style variant with Tailwind CSS for styling, featuring a custom color scheme based on HSL values for consistent theming.

**State Management**: TanStack Query (React Query) for server state management with aggressive caching (staleTime: Infinity) to minimize network requests. Local component state managed with React hooks.

**Real-time Communication**: WebSocket integration for live automation progress updates. The frontend connects to a dedicated WebSocket endpoint (`/ws`) that broadcasts automation events including start, progress, and completion messages.

**Routing**: Wouter for lightweight client-side routing, though the current implementation is primarily a single-page application with a home page and 404 fallback.

**Design System**: Typography uses Inter for UI elements and JetBrains Mono for code/technical content. The layout follows a responsive container strategy with different max-widths (640px for hero sections, 896px for results, 1152px for metrics dashboards). Spacing primitives are standardized to Tailwind units (4, 6, 8, 12, 16).

### Backend Architecture

**Server Framework**: Express.js running on Node.js with TypeScript. The server uses ES modules (type: "module") for modern JavaScript module support.

**Execution Engine**: Playwright Test framework for browser automation. The `PlaywrightExecutor` class manages browser instances (Chromium) running in headless mode with security flags for containerized environments (`--no-sandbox`, `--disable-setuid-sandbox`, `--disable-dev-shm-usage`). Uses secure whitelist-based command parsing (`executeSafePlaywrightCode`) instead of eval() to safely execute AI-generated automation code.

**AI Integration**: Google Gemini AI (via `@google/genai` SDK) translates natural language prompts into Playwright code. The system uses prompt engineering to generate safe, executable JavaScript/TypeScript code with proper selectors and error handling. Includes graceful error handling when `GEMINI_API_KEY` is not set.

**Code Execution Safety**: The system uses a whitelist-based command parser (`executeSafePlaywrightCode`) that safely parses AI-generated code and only executes approved Playwright commands (goto, click, fill, getByRole, getByText, waitForLoadState). This prevents arbitrary code execution while maintaining full automation capabilities.

**Real-time Updates**: WebSocket server (ws library) runs on the same HTTP server as Express, providing bidirectional communication for automation progress tracking. Messages follow a typed schema with discriminated unions for different event types (automation_start, automation_progress, automation_complete, automation_error). Frontend connects to correct backend port (5000) in both development and production.

**Development Environment**: Vite middleware integration for hot module replacement in development mode. Custom logging middleware tracks API requests with response times and payload inspection.

### Data Storage

**Current Implementation**: In-memory storage (`MemStorage` class) implementing the `IStorage` interface. This stores automation history, pre-built templates, and token usage metrics in JavaScript Maps.

**Schema Design**: Database schema defined using Drizzle ORM with PostgreSQL dialect. Three main tables:
- `automation_history`: Stores execution records with prompt, generated code, results, status, token usage, and execution time
- `automation_template`: Pre-built automation templates categorized by type (navigation, form, extraction, testing)
- Token metrics derived from aggregating history data

**Migration Strategy**: Drizzle Kit configured for schema migrations with output to `./migrations` directory. The schema is shared between client and server via the `shared/schema.ts` file.

**Database Preparation**: The codebase expects a PostgreSQL database but currently runs with in-memory storage. The `DATABASE_URL` environment variable is checked but not required for operation, allowing development without database setup.

### External Dependencies

**AI Service**: 
- Google Gemini API (Developer API, not Vertex AI) accessed via the `@google/genai` package
- Requires `GEMINI_API_KEY` environment variable
- Used for natural language to Playwright code conversion with optimized prompting for token efficiency
- Supports both gemini-2.5-flash and gemini-2.5-pro model series

**Browser Automation**:
- Playwright Test framework (`@playwright/test`) for Chromium browser control
- Runs in headless mode suitable for server environments and containers
- Default viewport: 1280x720

**Database** (Planned):
- PostgreSQL via Neon serverless driver (`@neondatabase/serverless`)
- Drizzle ORM for type-safe database operations
- Connection pooling and serverless optimization
- Schema management through Drizzle Kit

**UI Component Libraries**:
- Radix UI primitives for accessible components (accordion, dialog, dropdown, popover, select, tabs, toast, tooltip, etc.)
- class-variance-authority for component variant management
- cmdk for command palette functionality
- date-fns for date formatting
- Lucide React for icons

**Development Tools**:
- Replit-specific plugins for runtime error overlay, cartographer, and dev banner
- ESBuild for server bundling in production
- TypeScript with strict mode and path aliases for clean imports
- PostCSS with Tailwind CSS and Autoprefixer

**WebSocket Communication**:
- ws library for WebSocket server implementation
- Custom typed message schema using Zod for runtime validation
- Separate endpoint from Vite's HMR WebSocket to avoid conflicts