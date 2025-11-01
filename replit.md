# AI-Powered Web Automation Platform

## Overview

This is an AI-powered web automation platform that learns web application structures and executes tasks from natural language commands. The system crawls websites to build a knowledge base of UI elements, uses OpenAI for semantic understanding, and enables users to automate web interactions through conversational commands like "Login as admin" or "Add a new user".

**Core Capabilities:**
- Intelligent web crawling with Playwright to discover and catalog pages and elements
- AI-powered semantic understanding of UI components using OpenAI embeddings
- Natural language command interface for automation execution
- Self-healing automation that adapts to UI changes using vector similarity search
- Template detection to identify and group similar page structures

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework:** React with TypeScript using Vite as the build tool

**Routing:** wouter for client-side navigation

**UI Component System:** 
- shadcn/ui component library with Radix UI primitives
- Tailwind CSS for styling with a custom "Modern Developer Tools" aesthetic (Linear + Vercel + Playwright DevTools inspired)
- Design system emphasizes technical precision, information density, and real-time feedback
- Typography uses Inter for UI elements and JetBrains Mono for technical/code content

**State Management:**
- TanStack Query (React Query) for server state and API interactions
- Local component state with React hooks

**Key UI Patterns:**
- Dashboard with sidebar navigation (SidebarProvider pattern)
- Theme switching (light/dark mode) via ThemeProvider context
- Command-driven interface with natural language input
- Real-time status indicators and execution logs
- Metric cards displaying crawl statistics and automation performance

### Backend Architecture

**Runtime:** Node.js with Express.js server

**Development Server:** Vite middleware mode for HMR during development

**API Design:** RESTful endpoints under `/api` prefix
- `/api/crawl` - Initiate and manage website crawling sessions
- `/api/automations` - Execute and track automation commands
- Storage operations for sessions, pages, elements, and logs

**Background Processing:**
- Asynchronous crawling operations using async IIFE pattern
- Non-blocking automation execution with status updates

**Services Layer:**
- `CrawlerService`: Playwright-based web crawling and element extraction
- `OpenAIService`: AI analysis of pages and natural language processing
- `AutomationService`: Execution engine for automation plans

### Data Storage

**Primary Database:** PostgreSQL via Neon serverless driver

**ORM:** Drizzle ORM for type-safe database operations

**Schema Design:**
- `crawl_sessions` - Tracks crawling operations with status and metrics
- `pages` - Stores discovered pages with metadata and screenshots
- `elements` - Individual UI elements with selectors, attributes, and embeddings
- `automations` - Automation commands with execution plans and results
- `automation_logs` - Step-by-step execution logs for debugging

**Data Storage Pattern:**
- Currently uses in-memory storage (MemStorage class) for development
- IStorage interface abstraction allows swapping to database implementation
- Designed for future migration to full PostgreSQL persistence

**Vector Storage Strategy:**
- Element embeddings stored as text in PostgreSQL
- Semantic search capability through OpenAI embedding similarity
- Template detection via hash-based grouping

### External Dependencies

**AI Services:**
- **OpenAI API**: Required for semantic understanding and intent recognition
  - `text-embedding-3-small` model for generating element embeddings
  - GPT models for page analysis and automation plan generation
  - Natural language command parsing

**Web Automation:**
- **Playwright**: Browser automation framework
  - Headless Chromium for crawling and automation execution
  - Screenshot capture and element inspection
  - Cross-browser support (configured for Chromium)

**Database:**
- **Neon Database**: Serverless PostgreSQL database
  - Requires `DATABASE_URL` environment variable
  - Accessed via `@neondatabase/serverless` driver
  - Connection pooling for scalability

**Session Management:**
- **connect-pg-simple**: PostgreSQL session store for Express
  - User session persistence
  - Cookie-based authentication support

**Development Tools:**
- **Replit Integrations**: 
  - Vite plugin for runtime error overlay
  - Cartographer plugin for code navigation
  - Dev banner plugin (development only)

**Configuration Requirements:**
- `OPENAI_API_KEY` environment variable (mandatory for AI features)
- `DATABASE_URL` environment variable (mandatory for persistence)
- `NODE_ENV` for environment-specific behavior