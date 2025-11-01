# AI-Powered Web Automation Platform - Enterprise Edition

## Overview

This is a powerful enterprise-grade AI-powered web automation platform that rivals Comet and Atlas Browser capabilities. The system provides advanced crawling, visual intelligence, self-healing automation, and comprehensive data extraction capabilities.

**Core Capabilities:**
- **Advanced Web Crawling**: Playwright-based crawling with iframe support, shadow DOM traversal, dynamic content handling, and anti-bot detection evasion
- **Visual Intelligence**: GPT-4 Vision for screenshot analysis, visual element location, and change detection
- **Smart Self-Healing Selectors**: Multiple selector strategies (CSS, XPath, text, ARIA) with automatic fallback when selectors fail
- **Robust Automation**: Retry logic with exponential backoff, parallel execution, conditional steps, and comprehensive error handling
- **Data Extraction Engine**: Table extraction, structured data scraping, pagination handling, CSV/JSON export
- **Session Management**: Cookie handling, localStorage/sessionStorage persistence, authentication state management, proxy support
- **Action Recording**: Capture user interactions in real-time and generate automation scripts
- **Natural Language Interface**: Execute complex automations through conversational commands

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
- **Playwright**: Enterprise browser automation framework
  - Headless Chromium with anti-bot detection evasion
  - Iframe and shadow DOM support
  - Dynamic content and SPA handling
  - Screenshot capture with GPT-4 Vision analysis
  - Cookie and session management
  - Proxy support for distributed crawling
  - Multiple selector strategies with fallback mechanisms

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

### ✅ Fully Implemented Enterprise Features

**1. Advanced Web Crawling Engine**
- Playwright-based headless browser with anti-bot evasion
- Configurable crawl depth (1-5 levels, up to 100 pages)
- Intelligent URL filtering and deduplication
- Same-domain restriction for focused crawling
- **NEW**: Iframe content extraction and analysis
- **NEW**: Shadow DOM traversal for modern web apps
- **NEW**: Dynamic content detection with network idle waiting
- **NEW**: Custom selector waiting and viewport configuration
- **NEW**: Proxy support for distributed crawling
- **NEW**: Cookie and session state management
- Interactive element extraction with enhanced selectors
- Real-time crawl status tracking with performance metrics
- Screenshot capture with full-page support

**2. Visual Intelligence (NEW)**
- **GPT-4 Vision Integration**: Advanced screenshot analysis
- **Visual Element Location**: Find elements by description instead of selectors
- **Screenshot Comparison**: Detect UI changes between versions
- **Layout Analysis**: Understand page structure visually
- **Accessibility Suggestions**: AI-powered UX recommendations

**3. Smart Self-Healing Automation**
- **Multiple Selector Strategies**: CSS, XPath, text-based, ARIA labels
- **Automatic Fallback**: Tries alternative selectors when primary fails
- **Retry Logic**: Exponential backoff for transient failures (configurable retries)
- **AI-Generated Selectors**: OpenAI creates robust selectors based on context
- **Visual Element Finding**: Falls back to GPT-4 Vision when selectors fail
- Supported actions: navigate, click, type, select, wait, waitForElement, scroll, hover, pressKey, verify, extract, extractTable, screenshot
- AI-generated automation plans from natural language
- Real-time execution logging with screenshots
- Comprehensive error handling and recovery
- Step-by-step execution tracking

**4. Data Extraction Engine (NEW)**
- **Structured Data Extraction**: Extract specific data using selectors
- **Table Extraction**: Automatically parse HTML tables into JSON
- **Multi-element Extraction**: Batch extract similar elements
- **CSV/JSON Export**: Export extracted data in multiple formats
- **Attribute Extraction**: Capture element attributes, text, and values

**5. Session Management (NEW)**
- **Cookie Persistence**: Save and restore cookies across sessions
- **localStorage/sessionStorage**: Maintain application state
- **Authentication State**: Preserve login sessions
- **Proxy Configuration**: Route traffic through proxies
- **Custom Headers**: Set user agents and custom headers

**6. Action Recorder (NEW)**
- **Real-time Recording**: Capture user interactions as they happen
- **Automation Generation**: Convert recordings to automation scripts
- **Export/Import**: Save and share automation templates
- **Event Tracking**: Record clicks, inputs, and navigation

**7. User Interface**
- Modern, responsive dashboard with dark mode support
- Real-time metrics and statistics
- Natural language command input with quick actions
- Crawl history with status indicators
- Automation history with execution logs and data exports
- Element and page browsers with advanced filters
- Settings management
- **NEW**: Visual automation builder (in progress)
- **NEW**: Real-time execution preview
- **NEW**: Data export interface

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

**Core API Endpoints:**
- `POST /api/crawl` - Start a new crawl session
- `GET /api/crawl` - List all crawl sessions
- `POST /api/automations` - Execute an automation command
- `GET /api/automations` - List all automations
- `GET /api/pages` - List all discovered pages
- `GET /api/elements?q={query}` - Search elements
- `GET /api/stats` - Get platform statistics
- `GET /api/settings` - Get settings
- `POST /api/settings` - Update settings

**Visual Intelligence API Endpoints:**
- `POST /api/visual/analyze-screenshot` - Analyze screenshots with GPT-4 Vision
  - Body: `{ screenshot: string, query?: string }`
  - Returns: AI analysis of the screenshot
- `POST /api/visual/compare-screenshots` - Compare two screenshots for changes
  - Body: `{ screenshot1: string, screenshot2: string }`
  - Returns: Detailed comparison highlighting differences
- `POST /api/visual/find-element` - Find element by visual description
  - Body: `{ screenshot: string, description: string }`
  - Returns: Element location coordinates
- `POST /api/visual/generate-selectors` - Generate smart selectors for elements
  - Body: `{ elementDescription: string, pageUrl: string }`
  - Returns: Array of selector strategies (CSS, XPath, text, ARIA)

**Action Recorder API Endpoints:**
- `POST /api/recorder/start` - Start recording user interactions
  - Body: `{ url: string, duration?: number }`
  - Returns: Array of recorded actions
- `POST /api/recorder/export` - Export recorded actions as automation template
  - Body: `{ actions: array, name?: string, description?: string }`
  - Returns: Automation template ready for execution

**Data Extraction API Endpoints:**
- `POST /api/extract/data` - Extract structured data or tables from pages
  - Body: `{ url: string, selector: string, type?: 'table' | 'data' }`
  - Returns: Extracted data in JSON format
- `POST /api/extract/export` - Export extracted data as CSV or JSON
  - Body: `{ data: array, format: 'csv' | 'json' }`
  - Returns: File download (CSV or JSON)

**Session Management API Endpoints:**
- `GET /api/session/cookies` - Get current browser cookies
  - Returns: Array of cookies
- `POST /api/session/cookies` - Set browser cookies
  - Body: `{ cookies: array }`
  - Returns: Success confirmation
- `GET /api/session/storage/:url` - Get localStorage for a specific URL
  - Returns: localStorage data for the URL

**Per-Request Isolation:**
- Each crawl/automation request creates a fresh Playwright browser context
- Proxy settings are honored at browser launch (browser is relaunched when proxy changes)
- Cookies and session data are isolated per request
- No state leakage between different automation sessions

**Background Processing:**
- Crawls execute asynchronously in the background
- Automations run in separate Playwright browser instances
- Real-time status updates via polling (2-5 second intervals)
- Browser instances are automatically reused when options haven't changed (performance optimization)
- Browser instances are relaunched when proxy or headless settings change (isolation guarantee)

**AI Models Used:**
- `gpt-4o` for GPT-4 Vision screenshot analysis and automation planning (high accuracy)
- `gpt-4o-mini` for page analysis and selector generation (cost-effective)
- `text-embedding-3-small` for element embeddings and semantic search