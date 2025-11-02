# AI-Powered Web Automation Platform - Enterprise Edition

## Overview

This project is an enterprise-grade AI-powered web automation platform, offering advanced crawling, visual intelligence, self-healing automation, and comprehensive data extraction. It aims to provide capabilities comparable to leading platforms like Comet and Atlas Browser. The platform focuses on robust and intelligent web interaction for businesses.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework:** React with TypeScript (Vite build tool)
**Routing:** wouter
**UI Component System:** shadcn/ui with Radix UI primitives, Tailwind CSS for styling. The design is inspired by "Modern Developer Tools" (Linear, Vercel, Playwright DevTools), emphasizing technical precision and real-time feedback. Typography uses Inter for UI and JetBrains Mono for code.
**State Management:** TanStack Query for server state and API interactions; React hooks for local component state.
**Key UI Patterns:** Dashboard with sidebar navigation, theme switching, command-driven interface, real-time status indicators, and metric cards.

### Backend Architecture

**Runtime:** Python 3 with Flask server.
**API Design:** RESTful endpoints under `/api` for crawling, automations, and data storage.
**Background Processing:** Asynchronous operations for crawling and automation using threading with dedicated asyncio event loops for non-blocking execution.
**Services Layer:**
- `CrawlerService`: Playwright-based web crawling and element extraction.
- `OpenAIService`: AI analysis and natural language processing.
- `AutomationService`: Automation execution engine.
**Data Models:** Pydantic models for type-safe validation and automatic case conversion, mirroring Drizzle TypeScript schemas.

### Data Storage

**Primary Database:** PostgreSQL via Neon serverless driver.
**ORM:** Drizzle ORM for type-safe operations.
**Schema Design:** Tables for `crawl_sessions`, `pages`, `elements`, `automations`, and `automation_logs`.
**Data Storage Pattern:** Currently uses in-memory storage (`MemStorage`) for prototyping, with an `IStorage` interface for future migration to persistent `DbStorage`.
**Vector Storage Strategy:** Element embeddings stored as text in PostgreSQL, enabling semantic search via OpenAI embedding similarity and template detection through hash-based grouping.

### System Design Choices & Key Features

*   **Advanced Web Crawling:** Playwright-based with iframe/shadow DOM support, dynamic content handling, anti-bot evasion, proxy support, and session management.
*   **Visual Intelligence:** GPT-4 Vision for screenshot analysis, visual element location, UI change detection, and layout analysis.
*   **Smart Self-Healing Automation:** Multiple selector strategies (CSS, XPath, text, ARIA) with automatic fallback and AI-generated selectors. Includes retry logic and comprehensive error handling. Supports various actions like navigate, click, type, and data extraction.
*   **Data Extraction Engine:** Structured data and table extraction, multi-element extraction, with CSV/JSON export capabilities.
*   **Session Management:** Persistent cookies, localStorage/sessionStorage, authentication state, proxy configuration, and custom headers.
*   **Action Recording:** Real-time capture of user interactions to generate automation scripts.
*   **Natural Language Interface:** Execute complex automations through conversational commands.
*   **Per-Request Isolation:** Each crawl/automation uses a fresh Playwright browser context, ensuring isolation and preventing state leakage. Browser instances are reused or relaunched based on configuration changes.

## External Dependencies

**AI Services:**
- **OpenAI API**: Used for semantic understanding, intent recognition (`text-embedding-3-small`), GPT models for page analysis, automation plan generation, and natural language command parsing.

**Web Automation:**
- **Playwright**: Enterprise browser automation framework for headless Chromium, anti-bot detection evasion, iframe/shadow DOM support, dynamic content, screenshot capture, cookie/session management, proxy support, and multiple selector strategies.

**Database:**
- **Neon Database**: Serverless PostgreSQL database. Requires `DATABASE_URL` environment variable.

**Session Management:**
- **connect-pg-simple**: PostgreSQL session store for Express (used for user session persistence).

**Development Tools:**
- **Replit Integrations**: Vite plugin, Cartographer plugin, Dev banner plugin.

**Configuration Requirements:**
- `OPENAI_API_KEY` (mandatory for AI features)
- `DATABASE_URL` (optional, for PostgreSQL storage)
- `NODE_ENV`