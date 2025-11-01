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
- Currently uses in-memory storage (MemStorage class) for rapid prototyping
- IStorage interface abstraction allows swapping to database implementation
- All data is stored in memory and will be cleared on application restart
- For production use with persistent storage, migrate to DbStorage implementation

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
- `OPENAI_API_KEY` environment variable (mandatory for AI features) ✅ Configured
- `DATABASE_URL` environment variable (optional - only needed for PostgreSQL storage)
- `NODE_ENV` for environment-specific behavior

## Production Readiness Status

### ✅ Fully Implemented Features

**1. Web Crawling Engine**
- Playwright-based headless browser automation
- Configurable crawl depth (1-5 levels)
- Intelligent URL filtering and deduplication
- Same-domain restriction for focused crawling
- Screenshot capture for visual documentation
- Interactive element extraction (buttons, inputs, forms, links)
- Real-time crawl status tracking

**2. AI-Powered Analysis**
- OpenAI integration for semantic page understanding
- Vector embeddings for intelligent element search
- Page type classification (Login, Dashboard, Form, etc.)
- Element similarity matching using cosine similarity
- Natural language command parsing

**3. Automation Execution**
- Full browser automation with Playwright
- Supported actions: navigate, click, type, select, wait, verify
- AI-generated automation plans from natural language
- Real-time execution logging with screenshots
- Error handling and failure recovery
- Step-by-step execution tracking

**4. User Interface**
- Modern, responsive dashboard with dark mode support
- Real-time metrics and statistics
- Natural language command input with quick actions
- Crawl history with status indicators
- Automation history with execution logs
- Element and page browsers
- Settings management

### 🚀 How to Use

**Step 1: Crawl a Website**
1. Navigate to the "Crawl" page from the sidebar
2. Enter a website URL (e.g., `https://example.com`)
3. Set the crawl depth (1-5, default is 3)
4. Click "Start Crawl"
5. Monitor the crawl progress in the history table

**Step 2: Execute Automation**
1. Go to the "Dashboard" or "Automations" page
2. Enter a natural language command in the text area:
   - "Login as admin"
   - "Add a new user"
   - "Search for John Doe"
   - "Delete the first item"
3. Press ⌘+Enter or click the execute button
4. The AI will generate an automation plan and execute it
5. View real-time execution logs and screenshots

**Step 3: Browse Discovered Content**
- **Pages**: View all crawled pages with screenshots and metadata
- **Elements**: Search and explore discovered UI elements
- **Settings**: Configure automation behavior and preferences

### 📊 Current Limitations

**Data Persistence**
- Using in-memory storage (MemStorage)
- All data is cleared on application restart
- To enable persistence: migrate to DbStorage implementation

**Crawl Limits**
- Maximum 50 pages per crawl session (MVP limit)
- Maximum 20 elements per selector type
- Maximum 20 links per page

**Automation Constraints**
- Requires crawled pages for context
- OpenAI API usage incurs costs
- Browser automation timeout: 30 seconds per action

### 🔧 Technical Details

**API Endpoints:**
- `POST /api/crawl` - Start a new crawl session
- `GET /api/crawl` - List all crawl sessions
- `POST /api/automations` - Execute an automation command
- `GET /api/automations` - List all automations
- `GET /api/pages` - List all discovered pages
- `GET /api/elements?q={query}` - Search elements
- `GET /api/stats` - Get platform statistics
- `GET /api/settings` - Get settings
- `POST /api/settings` - Update settings

**Background Processing:**
- Crawls execute asynchronously in the background
- Automations run in separate Playwright browser instances
- Real-time status updates via polling (2-5 second intervals)

**AI Models Used:**
- `gpt-4o-mini` for page analysis (cost-effective)
- `gpt-4o` for automation plan generation (higher accuracy)
- `text-embedding-3-small` for element embeddings