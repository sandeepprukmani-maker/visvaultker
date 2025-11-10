# VisionVault - AI-Powered Browser Automation

## Overview

VisionVault is an AI-powered browser automation platform that enables users to automate web tasks using natural language prompts. The application leverages Stagehand (a browser automation library), Google Gemini AI for intelligent task interpretation, and implements semantic caching to reuse automation scripts for similar tasks. Users can describe what they want to do on a website in plain English, and the system will intelligently detect the URL, determine the best automation approach, execute the task, and generate reusable code.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack:**
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized production builds
- **Routing**: Wouter (lightweight client-side routing)
- **State Management**: TanStack Query (React Query) for server state management and caching
- **UI Components**: Radix UI primitives with shadcn/ui styling system
- **Styling**: Tailwind CSS with custom design tokens and CSS variables for theming

**Design Decisions:**
- Component-based architecture with reusable UI components in `/client/src/components`
- Context API for global settings (AI model selection, screenshot preferences)
- WebSocket integration for real-time automation feedback
- Dark/light theme support with CSS variable-based theming
- Responsive design with mobile considerations

**Key Pages:**
- Home: Main automation interface with unified natural language input
- History: Browse and replay past automation runs
- Cache: View semantically cached automations for reuse
- Settings: Configure AI model and screenshot capture preferences

### Backend Architecture

**Hybrid Architecture:**
- **Node.js/Express Server** (TypeScript): Main application server handling automation orchestration
- **Python FastAPI Server**: Dedicated service for history storage and semantic similarity search

**Node.js Backend (Primary):**
- **Framework**: Express.js with TypeScript
- **Automation Engine**: Stagehand v3 for browser automation (Playwright-based)
- **AI Integration**: Google Gemini API for prompt interpretation and task execution
- **WebSocket Server**: Real-time bidirectional communication for live automation updates
- **Session Management**: In-memory session storage with connect-pg-simple for PostgreSQL sessions

**Key Design Patterns:**
- Intelligent routing that automatically detects URLs and selects optimal automation modes
- Multi-mode automation support: `act` (perform actions), `observe` (find elements), `extract` (get data), `agent` (autonomous navigation)
- Locator generation that creates executable TypeScript code from automation runs
- Semantic caching to avoid redundant AI calls for similar prompts

**Python Backend (Specialized):**
- **Framework**: FastAPI for high-performance API endpoints
- **Purpose**: History persistence and vector similarity search
- **Database**: SQLite with SQLAlchemy ORM
- **Vector Operations**: NumPy for cosine similarity calculations on prompt embeddings

**Rationale for Hybrid Approach:**
- Node.js excels at real-time WebSocket communication and JavaScript-based browser automation
- Python provides robust scientific computing libraries (NumPy) for embedding similarity
- Separation of concerns: automation orchestration vs. data persistence/retrieval

### Data Storage Solutions

**PostgreSQL (Primary Database):**
- **ORM**: Drizzle ORM with Neon serverless driver
- **Connection**: WebSocket-based connection pooling for serverless compatibility
- **Schema Location**: `/shared/schema.ts`
- **Migrations**: Managed via drizzle-kit with migrations stored in `/migrations`

**Database Schema:**
- User management (in-memory fallback with MemStorage)
- Automation history tracking (delegated to Python service)
- Session storage using connect-pg-simple

**SQLite (Python Service):**
- **Purpose**: Stores automation history with vector embeddings
- **Schema**: AutomationHistory table with prompt embeddings (768-dimensional vectors)
- **Location**: `visionvault.db` in Python service directory

**Design Trade-offs:**
- PostgreSQL chosen for production scalability and ACID compliance
- SQLite used in Python service for simplicity and efficient vector operations
- Future consideration: Consolidate to single PostgreSQL database with pgvector extension

### Authentication and Authorization

**Current Implementation:**
- Basic user storage interface defined (`IStorage` in `/server/storage.ts`)
- In-memory user storage (MemStorage) for development
- PostgreSQL session support configured but not fully implemented
- No authentication middleware currently enforced on API routes

**Future Considerations:**
- Implement proper session-based or JWT authentication
- Add role-based access control for multi-tenant scenarios
- Secure WebSocket connections with authentication tokens

### External Dependencies

**AI Services:**
- **Google Gemini API** (`@google/genai`): Powers natural language understanding, task execution, and prompt embeddings
  - Models: gemini-2.5-flash (default), gemini-1.5-pro, gemini-embedding-001 (for semantic search)
  - API Key: Required via `GEMINI_API_KEY` environment variable

**Browser Automation:**
- **Stagehand** (`@browserbasehq/stagehand`): AI-powered browser automation framework
  - Version: 3.x with updated API (model vs. modelName)
  - Supports local and cloud browser sessions
  - Playwright-based with enhanced AI capabilities

**Database Services:**
- **Neon PostgreSQL** (`@neondatabase/serverless`): Serverless PostgreSQL database
  - Connection via DATABASE_URL environment variable
  - WebSocket-based for compatibility with serverless environments

**Development Tools:**
- **Replit Integration**: Custom Vite plugins for Replit environment
  - Runtime error overlay
  - Cartographer for code navigation
  - Development banner

**UI Component Libraries:**
- **Radix UI**: Headless accessible components (@radix-ui/react-*)
- **shadcn/ui**: Pre-styled component system built on Radix
- **Lucide React**: Icon library

**WebSocket:**
- **ws**: WebSocket library for Node.js server-side implementation
- Custom protocol for session-based message broadcasting

**Key Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string (required)
- `GEMINI_API_KEY`: Google AI API key (required)
- `PYTHON_API_URL`: URL for Python FastAPI service (defaults to http://localhost:8000)
- `SQLITE_DATABASE_URL`: SQLite database path for Python service

**Architecture Benefits:**
- Separation of concerns between automation execution and data persistence
- Semantic caching reduces API costs and improves response times
- Real-time feedback via WebSocket enhances user experience
- Flexible AI model selection for cost/performance optimization
- Reusable code generation enables automation portability