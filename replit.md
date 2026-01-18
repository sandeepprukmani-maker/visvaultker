# Visvaultker - Mortgage Pulse Application

## Overview

This is a full-stack mortgage market intelligence application called "Mortgage Pulse." It fetches real-time mortgage rate news from RSS feeds (Mortgage News Daily), stores articles in a PostgreSQL database, and generates AI-powered social media captions for loan officers. The app provides a dashboard showing the latest market updates and a gallery of generated captions.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

- **Framework**: React 18 with TypeScript
- **Routing**: Wouter (lightweight React router)
- **Styling**: Tailwind CSS with shadcn/ui component library (New York style)
- **State Management**: TanStack React Query for server state
- **Animations**: Framer Motion for smooth UI transitions
- **Build Tool**: Vite with React plugin

The frontend follows a component-based architecture with:
- Pages in `client/src/pages/`
- Reusable UI components in `client/src/components/ui/` (shadcn/ui)
- Custom components in `client/src/components/`
- Custom hooks in `client/src/hooks/`
- Path aliases: `@/` maps to `client/src/`, `@shared/` maps to `shared/`

### Backend Architecture

- **Framework**: Express.js with TypeScript
- **Runtime**: Node.js with TSX for TypeScript execution
- **API Pattern**: RESTful endpoints under `/api/`
- **Database ORM**: Drizzle ORM with PostgreSQL
- **Schema Location**: `shared/schema.ts` for database models

Key backend modules:
- `server/routes.ts` - API route definitions
- `server/storage.ts` - Database access layer (repository pattern)
- `server/db.ts` - Database connection setup
- `server/lib/rss.ts` - RSS feed parsing for mortgage news

### Data Storage

- **Database**: PostgreSQL via Drizzle ORM
- **Schema Definitions**: Located in `shared/schema.ts`
- **Tables**:
  - `posts` - Stores fetched mortgage news articles (title, link, content, pubDate, guid)
  - `posters` - Stores generated social media captions linked to posts
  - `conversations` / `messages` - Chat functionality for AI conversations

### AI Integrations

The app includes pre-built AI integration modules in `server/replit_integrations/`:
- **Chat**: OpenAI-powered chat with conversation persistence
- **Image**: Image generation using gpt-image-1 model
- **Batch**: Rate-limited batch processing utilities for LLM operations

These integrations use environment variables:
- `AI_INTEGRATIONS_OPENAI_API_KEY`
- `AI_INTEGRATIONS_OPENAI_BASE_URL`

### API Structure

Defined in `shared/routes.ts` using Zod for type safety:
- `GET /api/posts/latest` - Fetch latest mortgage news (with RSS upsert)
- `GET /api/posts` - List all posts
- `POST /api/posters` - Generate social media caption for a post
- `GET /api/posters` - List all generated captions

### Build Process

- **Development**: `npm run dev` - Uses Vite dev server with HMR
- **Production Build**: `npm run build` - Bundles frontend with Vite, backend with esbuild
- **Database Migrations**: `npm run db:push` - Drizzle Kit push to database

## External Dependencies

### Database
- PostgreSQL (required via `DATABASE_URL` environment variable)
- Drizzle ORM for schema management and queries
- connect-pg-simple for session storage

### AI Services
- OpenAI API (for chat and image generation)
- Configured via Replit AI Integrations

### External Data Sources
- Mortgage News Daily RSS feed (https://www.mortgagenewsdaily.com/rss/rates)
- Rate scraping from mortgagenewsdaily.com

### Key NPM Packages
- `rss-parser` - RSS feed parsing
- `date-fns` - Date formatting
- `framer-motion` - Animations
- `lucide-react` - Icons
- `zod` - Schema validation
- Full shadcn/ui component set via Radix primitives