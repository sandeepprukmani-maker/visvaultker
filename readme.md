# VisionVault

## Overview
VisionVault is an intelligent web automation platform that uses natural language processing and AI to automate browser interactions. Users can describe what they want to automate in plain English, and the system automatically detects URLs, determines the appropriate automation mode, and executes the task while generating reusable code.

## Project Architecture

### Tech Stack
- **Frontend**: React + TypeScript + Vite + Tailwind CSS + Radix UI
- **Backend**: Express.js + TypeScript
- **Database**: PostgreSQL (Neon) with pgvector extension for semantic caching
- **Automation**: Stagehand v3 (Browser automation framework)
- **AI Models**: Supports multiple providers (Google Gemini, GPT-4, Claude, etc.)
- **Real-time Communication**: WebSocket for live automation updates

### Project Structure
```
├── client/               # React frontend
│   ├── src/
│   │   ├── components/  # UI components (Radix UI based)
│   │   ├── pages/       # Main pages (Home, History, Cache, Settings)
│   │   ├── hooks/       # Custom hooks (WebSocket, toast)
│   │   └── contexts/    # React contexts (Settings)
│   └── public/
├── server/              # Express backend
│   ├── index.ts        # Entry point
│   ├── routes.ts       # API routes
│   ├── websocket.ts    # WebSocket server
│   ├── intelligent-router.ts  # Prompt parsing and mode detection
│   ├── semantic-cache.ts      # Embedding-based caching
│   └── locator-generator.ts   # Resilient selector generation
├── shared/             # Shared TypeScript schemas (Zod)
└── migrations/         # Drizzle ORM migrations
```

## Core Features

### 1. Intelligent Automation Modes
- **Act**: Perform actions (click, type, submit)
- **Observe**: Find and locate elements
- **Extract**: Scrape and retrieve data
- **Agent**: Multi-step autonomous workflows

### 2. Smart URL Detection
The system automatically extracts URLs from natural language prompts, so users can say:
- "Go to example.com and click the login button"
- "Extract all product names from amazon.com"

### 3. Semantic Caching
Uses vector embeddings (Gemini embeddings, 768 dimensions) to:
- Find similar past automations (85% similarity threshold)
- Reuse cached results for faster execution
- Reduce API costs by avoiding duplicate AI calls

### 4. Code Generation
Generates multiple code variants:
- **TypeScript**: Standard Stagehand code
- **Cached**: Code with semantic caching enabled
- **Agent**: Autonomous agent-based code
- **Locators**: Resilient selectors using best practices

### 5. Real-time Execution
- Live log streaming via WebSocket
- Progress tracking with status updates
- Screenshot capture during automation

## Configuration

### Environment Variables
Required for the application to function:
- `DATABASE_URL`: PostgreSQL connection string (auto-configured in Replit)
- `GEMINI_API_KEY`: For AI model access and embeddings
- `PORT`: Server port (default: 5000)

### Optional Environment Variables
- `AUTH_MODE`: "standard" or "oauth" (default: "standard")
- Model-specific API keys (if not using OAuth):
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - etc.

## Development Setup

### Database Setup
1. PostgreSQL database is auto-configured in Replit
2. Vector extension enabled for semantic search
3. Schema managed via Drizzle ORM
4. Run `npm run db:push` to sync schema changes

### Running the Application
```bash
npm run dev
```
This starts both the Express server and Vite dev server on port 5000.

### Build for Production
```bash
npm run build  # Builds frontend and backend
npm start      # Runs production server
```

## API Endpoints

### POST /api/automate-unified
Unified endpoint that accepts natural language prompts
- Auto-detects URL from prompt
- Suggests optimal automation mode
- Streams progress via WebSocket
- Saves to history with embeddings

### GET /api/history
Retrieves automation execution history

### GET /api/cache
Retrieves semantically cached automations

### POST /api/history/:id/reexecute
Re-runs a previous automation

### DELETE /api/history/:id
Deletes a specific history item

## Key Dependencies

### Backend
- `@browserbasehq/stagehand`: Browser automation engine
- `@google/genai`: Gemini AI for embeddings
- `drizzle-orm`: Type-safe ORM
- `express`: Web framework
- `ws`: WebSocket server

### Frontend
- `react`: UI library
- `wouter`: Lightweight routing
- `@tanstack/react-query`: Data fetching
- `@radix-ui/*`: Accessible UI primitives
- `tailwindcss`: Styling

## Recent Changes
- 2025-11-10: Initial Replit environment setup
  - Installed dependencies with legacy peer deps flag
  - Created PostgreSQL database
  - Enabled pgvector extension
  - Pushed database schema via Drizzle
  - Configured dev workflow on port 5000
  - Verified application is running successfully

## User Preferences
None configured yet.

## Notes
- The Vite HMR WebSocket warning in browser console is a known issue in Replit environments and doesn't affect functionality
- The application's own WebSocket for automation updates works correctly
- Server binds to 0.0.0.0:5000 for Replit proxy compatibility
- HMR configured for WSS protocol on port 443 for Replit infrastructure
