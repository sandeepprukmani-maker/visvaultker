# Stagehand UI

## Overview

Stagehand UI is a web automation platform that allows users to describe tasks in plain English, which are then executed by a headless browser using the Stagehand library. The application provides a dashboard interface for creating, monitoring, and reviewing browser automation tasks with real-time logging and screenshot capture capabilities.

The system uses a custom OpenAI-compatible provider (RBC internal endpoint) with Claude Sonnet 4.5 model and OAuth token authentication.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Routing**: Wouter (lightweight React router)
- **State Management**: TanStack React Query for server state
- **Styling**: Tailwind CSS with shadcn/ui component library
- **Animations**: Framer Motion for page transitions and UI animations
- **Build Tool**: Vite with custom Replit plugins

The frontend follows a page-based structure with shared components. Key pages include:
- Home dashboard for creating automations and viewing history
- Automation detail page with real-time log streaming and results display

### Backend Architecture
- **Runtime**: Node.js with Express
- **Language**: TypeScript (ESM modules)
- **API Pattern**: RESTful endpoints defined in `shared/routes.ts` with Zod validation
- **Browser Automation**: Stagehand library with custom LLM client

The backend uses a clean separation between route handlers (`server/routes.ts`), business logic (`server/stagehand.ts`), and data access (`server/storage.ts`).

### Data Storage
- **Database**: PostgreSQL via Drizzle ORM
- **Schema Location**: `shared/schema.ts`
- **Tables**:
  - `automations`: Stores automation tasks with prompt, status, result, screenshot, and error fields
  - `automation_logs`: Real-time log entries linked to automations

### API Structure
Routes are defined declaratively in `shared/routes.ts` with Zod schemas for type safety:
- `GET /api/automations` - List all automations
- `POST /api/automations` - Create and start new automation
- `GET /api/automations/:id` - Get automation with logs
- `GET /api/automations/:id/logs` - Get logs only

### Authentication Flow
OAuth token retrieval is handled via a Python script (`fetch_token.py`) that outputs JSON with an access token. This is invoked from Node.js using child process spawn.

## External Dependencies

### Third-Party Services
- **Custom LLM Provider**: RBC internal endpoint (`https://perf-apigw-int.saifg.rbc.com/JLCO/llm-control-stack/v1`)
- **Model**: Claude Sonnet 4.5

### Required Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `CHROME_PATH`: Path to Chromium/Chrome executable

### Key npm Dependencies
- `@browserbasehq/stagehand`: Browser automation framework
- `ai-sdk` & `@ai-sdk/openai`: AI SDK for custom model integration
- `drizzle-orm` + `drizzle-kit`: Database ORM and migrations
- `@tanstack/react-query`: Server state management
- `framer-motion`: Animation library

### Database Migrations
Run `npm run db:push` to sync schema changes to the database using Drizzle Kit.
