# AutoPilot Studio X

## Overview

AutoPilot Studio X is a browser automation platform that enables users to create, execute, and manage web automation tasks using AI-assisted code generation and visual workflow building. The application combines natural language prompting, code editing, live browser previews, and recording capabilities to streamline web automation workflows powered by Playwright.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Framework & Build System**
- React 18 with TypeScript for type-safe component development
- Vite as the build tool and development server with HMR support
- Wouter for client-side routing (lightweight React Router alternative)

**UI Component System**
- shadcn/ui component library built on Radix UI primitives
- Tailwind CSS for utility-first styling with custom design tokens
- Custom theming system with light/dark mode support via next-themes
- Design follows developer-tool aesthetics (VS Code, Linear, Chrome DevTools inspired)
- Typography: Inter for UI text, JetBrains Mono for code display

**State Management**
- TanStack Query (React Query) for server state management and caching
- Local component state using React hooks
- Query invalidation patterns for optimistic updates

**Key UI Patterns**
- Multi-panel split-screen layouts with resizable dividers
- Information-dense, developer-focused interfaces
- Real-time execution status tracking with step-by-step visualization
- Live browser preview integration (prepared for WebRTC/WebSocket streaming)
- Monaco-style code editor for automation scripts

### Backend Architecture

**Runtime & Framework**
- Node.js with Express.js for HTTP server
- TypeScript throughout for type safety
- ESM (ES Modules) module system

**API Design**
- RESTful endpoints under `/api/*` namespace
- Session-based authentication with Replit OIDC integration
- Development mode auth bypass for local testing
- Request/response logging middleware with JSON capture

**Authentication & Session Management**
- OpenID Connect (OIDC) via Replit authentication provider
- Passport.js strategy for OAuth flow
- Express sessions stored in PostgreSQL using connect-pg-simple
- JWT token handling with automatic refresh
- Environment-based auth bypass for development (dev-user-1)

**Data Access Layer**
- Storage abstraction interface (IStorage) for database operations
- Separation of concerns: routes → storage → database
- User-scoped data access with userId filtering for multi-tenancy

### Database Architecture

**ORM & Schema Management**
- Drizzle ORM for type-safe database queries
- Neon PostgreSQL serverless database with WebSocket support
- Schema-first approach with Zod validation integration
- Automatic UUID generation for primary keys

**Data Model**
- **Users**: Authentication and profile information (email, name, profile image)
- **Tasks**: Individual automation scripts with code, language, and prompt history
- **Executions**: Task run history with status, logs, errors, and screenshots
- **Recordings**: Browser interaction recordings for code generation
- **Workflows**: Chained task sequences for complex automations
- **Voice Requests**: Voice-to-code feature for natural language automation creation
- **Sessions**: Server-side session storage for authentication state

**Data Relationships**
- Cascade deletion: User → Tasks, Executions, Recordings, Workflows
- Foreign key constraints maintain referential integrity
- Indexed session expiration for efficient cleanup

### External Dependencies

**Database & Storage**
- Neon Serverless PostgreSQL for relational data storage
- WebSocket-based connection pooling via @neondatabase/serverless
- Object storage integration planned for screenshots and recordings (S3/GCS/Azure Blob)

**Authentication Service**
- Replit OIDC provider for SSO authentication
- Configurable issuer URL (defaults to https://replit.com/oidc)
- Session secret management via environment variables

**Browser Automation**
- Playwright integration planned for headless browser control
- Chrome/Chromium as default browser engine
- Support for TypeScript and JavaScript automation scripts

**AI/LLM Services**
- OpenAI API integration for code generation from natural language prompts
- AI-powered automation creation from voice transcripts
- Code generation from recorded browser interactions

**UI Component Libraries**
- Radix UI primitives for accessible, unstyled components
- Lucide React for iconography
- cmdk for command palette functionality
- date-fns for date manipulation

**Development Tools**
- Replit-specific plugins for runtime error overlay, cartographer, and dev banner
- TypeScript compiler for type checking
- ESBuild for production server bundling

**Session & Caching**
- PostgreSQL-backed session storage (no Redis required in current architecture)
- In-memory query caching via TanStack Query on frontend