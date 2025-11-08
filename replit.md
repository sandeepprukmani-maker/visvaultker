# Stagehand Automation Studio

## Overview

Stagehand Automation Studio is a browser automation code generator that enables users to create web automation scripts using natural language prompts. The application provides an interactive interface where users can input a URL and describe their automation task, and the system generates TypeScript code using the Stagehand library. It supports multiple automation modes (act, observe, extract, agent) and provides real-time execution logs and generated code output.

The application bridges the gap between traditional brittle selector-based automation and unpredictable AI agents by offering a developer-friendly tool that combines AI capabilities with code precision.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework:** React with TypeScript, bundled using Vite

**Routing:** wouter for client-side routing

**UI Components:** shadcn/ui component library built on Radix UI primitives, styled with Tailwind CSS using a custom design system inspired by Linear, Vercel, and Stripe aesthetics

**State Management:** 
- TanStack Query (React Query) for server state management and API interactions
- Local component state using React hooks

**Design System:**
- Typography: Inter for UI elements, JetBrains Mono for code/monospace content
- Spacing: Tailwind's spacing scale (2, 4, 6, 8, 12, 16, 24, 32 units)
- Color scheme: Custom HSL-based color system supporting light/dark modes
- Layout: Max-width containers (max-w-7xl), split-screen layouts for input/output views

**Key Components:**
- AutomationInput: Collects URL, natural language prompt, automation mode, and model selection
- BrowserPreview: Displays browser session state with loading indicators
- ExecutionLog: Real-time log viewer showing automation steps with status indicators
- CodeOutput: Tabbed view for generated TypeScript, cached, and agent code with copy/download functionality
- Header: Application header with session management and status display

### Backend Architecture

**Runtime:** Node.js with Express framework

**Language:** TypeScript with ES modules

**API Design:** RESTful API with a single main endpoint `/api/automate` accepting POST requests

**Request Processing Flow:**
1. Request validation using Zod schemas
2. Stagehand browser automation initialization
3. Step-by-step execution with log generation
4. Code generation for different formats (TypeScript, cached, agent)
5. Structured response with logs and generated code

**Automation Engine:** Stagehand library (@browserbasehq/stagehand) provides four automation modes:
- **Act:** Execute actions using natural language instructions
- **Observe:** Discover available actions on web pages
- **Extract:** Pull structured data with schema validation
- **Agent:** Autonomous multi-step workflow execution

**Environment Support:** Local browser automation (LOCAL mode) with configurable AI models (default: google/gemini-2.5-flash)

**Development Server:** Vite development server integrated with Express for HMR and asset serving in development mode

### Data Storage Solutions

**Primary Storage:** In-memory storage implementation (MemStorage class)

**Schema Definition:** Drizzle ORM schema definitions in shared/schema.ts, configured for PostgreSQL via drizzle.config.ts

**Database Configuration:** 
- Prepared for PostgreSQL through Neon Database serverless driver (@neondatabase/serverless)
- Migration output directory: ./migrations
- Currently using in-memory storage, with database infrastructure ready for production deployment

**Data Models:**
- User model with id, username fields
- Automation request/response schemas with Zod validation
- Log entry tracking with timestamp, action, status, selector fields

### External Dependencies

**Browser Automation:**
- Stagehand (@browserbasehq/stagehand v2.5.0): Core automation library providing AI-powered browser control
- Supports multiple AI model providers through configurable modelName parameter

**Database & ORM:**
- Drizzle ORM (v0.39.1): Type-safe SQL ORM with Zod integration
- Neon Database Serverless: PostgreSQL database connection for production

**UI Framework:**
- Radix UI: Comprehensive collection of accessible component primitives
- Tailwind CSS: Utility-first CSS framework with custom configuration
- shadcn/ui: Pre-built component library with the "new-york" style variant

**Form & Validation:**
- React Hook Form with Hookform Resolvers for form state management
- Zod (with drizzle-zod) for runtime type validation and schema definition

**API & State:**
- TanStack React Query (v5.60.5): Server state management, caching, and synchronization
- Express.js: Web server framework with middleware support

**Development Tools:**
- Vite: Build tool and development server with HMR
- tsx: TypeScript execution for development
- esbuild: Production bundling for server code

**Session Management:**
- connect-pg-simple: PostgreSQL session store for Express sessions (ready for production)

**Utilities:**
- date-fns: Date manipulation and formatting
- clsx & class-variance-authority: Conditional className utilities
- nanoid: Unique ID generation for sessions and logs