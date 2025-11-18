# ZenSmart Executor

## Overview

ZenSmart Executor is a browser automation application that enables users to control web browsers using natural language commands. The application leverages AI-powered automation through Stagehand, allowing users to execute web tasks by simply describing what they want to accomplish. It provides a Google-like interface with a clean, minimalist design that progressively reveals advanced features as needed.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework**: React 18 with TypeScript, using Vite as the build tool and development server.

**UI Component Library**: Shadcn UI (New York style variant) built on Radix UI primitives, providing a comprehensive set of accessible, customizable components. The design system follows Material Design 3 principles with Google Search influences, emphasizing "zen simplicity" with generous whitespace and centered layouts.

**State Management**: TanStack Query (React Query) for server state management, with custom query client configuration that handles API requests, error states, and data caching. Queries are configured with infinite stale time and disabled automatic refetching for predictable behavior.

**Styling**: Tailwind CSS with custom design tokens defined in CSS variables. The theming system supports light and dark modes through a ThemeProvider context that manages theme state in localStorage and applies classes to the document root.

**Real-time Communication**: WebSocket connection for live execution updates. Custom `useWebSocket` hook manages connection state, automatic reconnection, and message parsing with structured error handling.

**Routing**: Wouter for lightweight client-side routing, currently implementing a simple home page route with a 404 fallback.

### Backend Architecture

**Server Framework**: Express.js running as a Node.js application with TypeScript support via tsx.

**HTTP/WebSocket Hybrid**: Single HTTP server instance handles both REST API endpoints and WebSocket connections. The WebSocket server runs on the `/ws` path for real-time automation execution updates.

**API Structure**: RESTful endpoints for managing automations, cache patterns, and user settings. The routes module registers all endpoints and initializes the WebSocket server on the same HTTP server instance.

**Automation Engine**: Stagehand integration for AI-powered browser automation. The `AutomationExecutor` class wraps Stagehand functionality and manages execution lifecycle, logging, and WebSocket communication. Supports multiple AI models (OpenAI, Anthropic, Gemini) selectable by the user.

**Development/Production Modes**: Vite middleware integration in development for HMR and React Fast Refresh. Production builds serve static assets from the `dist/public` directory. The server auto-detects environment and configures accordingly.

### Data Storage

**ORM**: Drizzle ORM configured for PostgreSQL with schema defined in `shared/schema.ts`.

**Database Provider**: Neon Serverless PostgreSQL adapter specified in configuration, though the application currently implements an in-memory storage fallback (`MemStorage` class) for development or when database is unavailable.

**Schema Design**:
- **Automations table**: Stores execution records with prompt, status, selected model, results, logs, errors, and duration
- **Cache table**: Stores reusable automation patterns with usage tracking
- **Settings table**: Single-row configuration table for user preferences (selected model, screenshot mode, theme)

**Storage Interface**: Abstract `IStorage` interface allows swapping between in-memory and database implementations without changing business logic.

### Authentication & Authorization

No authentication system is currently implemented. The application appears designed for single-user or development use.

## External Dependencies

### AI & Automation Services

**Stagehand (@browserbasehq/stagehand v3.0.3)**: Primary browser automation framework that combines Playwright with AI capabilities for natural language web automation. Provides four core primitives: act (execute actions), extract (pull structured data), observe (discover page actions), and agent (autonomous workflows).

**AI Model SDKs**:
- **OpenAI**: Via `@google/genai` package (v1.30.0)
- **Anthropic**: Via `@anthropic-ai/sdk` (v0.37.0)
- **Google Gemini**: Via `@google/genai` package

Users can switch between these models through the settings panel to control automation behavior.

### Database

**Neon Serverless PostgreSQL** (`@neondatabase/serverless` v0.10.4): Serverless PostgreSQL client optimized for edge runtimes and serverless functions. Configured through `DATABASE_URL` environment variable.

**Drizzle Kit**: Schema migration tool for managing database schema changes and generating migration files in the `/migrations` directory.

### UI & Component Libraries

**Radix UI**: Complete suite of accessible, unstyled UI primitives including dialogs, popovers, dropdowns, accordions, tabs, tooltips, and form controls. All components support keyboard navigation and screen readers.

**Tailwind CSS**: Utility-first CSS framework with custom configuration extending the default theme with project-specific colors, spacing, and design tokens.

**Lucide React**: Icon library providing consistent, customizable SVG icons throughout the interface.

### Form Handling & Validation

**React Hook Form**: Form state management and validation library used with Zod resolvers for type-safe form validation.

**Zod**: TypeScript-first schema validation library used for runtime validation of API requests, form inputs, and database operations.

### Development Tools

**Replit Plugins**: Development-specific Vite plugins for runtime error overlays, cartographer (code navigation), and dev banner functionality, conditionally loaded only in Replit development environment.

**TypeScript**: Strict type checking enabled with path aliases for `@/` (client), `@shared/` (shared), and `@assets/` (attached_assets) directories.

### Build & Deployment

**Vite**: Build tool and dev server with React plugin, custom alias resolution, and production optimization. Builds output to `dist/public` for static assets.

**ESBuild**: Used for bundling the server code during production builds, targeting Node.js with ESM module format.