# Mortgage News Video Generator

## Overview

This application is a mortgage news video generator that fetches RSS feed content from mortgage news sources, uses AI to rephrase the content into marketing scripts, and generates videos using the HeyGen API. It's built as a full-stack TypeScript application with a React frontend and Express backend.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: React 18 with TypeScript
- **Routing**: Wouter for lightweight client-side routing
- **State Management**: TanStack React Query for server state management and caching
- **UI Components**: shadcn/ui component library built on Radix UI primitives
- **Styling**: Tailwind CSS with custom CSS variables for theming (light/dark mode support)
- **Build Tool**: Vite for development and production builds

### Backend Architecture
- **Framework**: Express.js with TypeScript
- **API Design**: RESTful endpoints defined in `shared/routes.ts` with Zod schema validation
- **Database ORM**: Drizzle ORM with PostgreSQL dialect
- **AI Integration**: OpenAI API (via Replit AI Integrations) for content rephrasing
- **External APIs**: 
  - HeyGen API for video generation
  - Mortgage News Daily RSS feed for content sourcing

### Data Storage
- **Database**: PostgreSQL with Drizzle ORM
- **Schema Location**: `shared/schema.ts` defines all database tables
- **Tables**:
  - `users`: Basic user authentication (username/password)
  - `videos`: Stores generated video metadata (videoId, status, URLs, scripts)
  - `conversations` and `messages`: Chat functionality for AI integrations

### Project Structure
```
├── client/           # React frontend
│   └── src/
│       ├── components/ui/  # shadcn/ui components
│       ├── pages/          # Page components
│       ├── hooks/          # Custom React hooks
│       └── lib/            # Utilities and query client
├── server/           # Express backend
│   ├── routes.ts     # API route handlers
│   ├── storage.ts    # Database operations
│   └── db.ts         # Database connection
├── shared/           # Shared types and schemas
│   ├── schema.ts     # Drizzle database schema
│   └── routes.ts     # API contract definitions
└── migrations/       # Database migrations
```

### Build System
- Development: `npm run dev` runs tsx to start the Express server with Vite middleware
- Production: `npm run build` bundles both client (Vite) and server (esbuild)
- Database: `npm run db:push` pushes schema changes to PostgreSQL

## External Dependencies

### Required Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (required for database operations)
- `AI_INTEGRATIONS_OPENAI_API_KEY`: OpenAI API key for content rephrasing
- `AI_INTEGRATIONS_OPENAI_BASE_URL`: OpenAI base URL (for Replit AI Integrations)
- `HEYGEN_API_KEY`: HeyGen API key for video generation

### Third-Party Services
- **PostgreSQL**: Primary database (provision via Replit Database or external provider)
- **OpenAI API**: Used for rephrasing RSS content into marketing scripts
- **HeyGen API**: Avatar-based video generation service
- **Mortgage News Daily RSS**: External RSS feed source for mortgage news content

### Key NPM Dependencies
- `drizzle-orm` / `drizzle-kit`: Database ORM and migrations
- `@tanstack/react-query`: Server state management
- `openai`: OpenAI API client
- `xml2js`: RSS feed XML parsing
- `zod`: Runtime type validation
- `express`: Web server framework