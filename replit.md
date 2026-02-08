# RateEngine - UWM Instant Price Quote Broker Portal

## Overview

RateEngine is a mortgage pricing engine web application that serves as a broker portal for generating instant price quotes via the UWM (United Wholesale Mortgage) Public API. Brokers can authenticate, submit loan parameters (mortgage or HELOC), receive pricing quotes with rate/fee breakdowns, and save/review past scenarios. The application acts as a frontend and proxy layer to the UWM Instant Price Quote API, which is accessed through an SSH tunnel to an Azure VM with whitelisted access.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend

- **Framework:** React 18 with TypeScript, bundled by Vite
- **Routing:** Wouter (lightweight client-side router) with two main pages: Home (quote form + results) and Scenarios (saved quote history)
- **State Management:** TanStack React Query for server state (caching, mutations, invalidation)
- **Forms:** React Hook Form with Zod resolvers for validation
- **UI Components:** shadcn/ui component library (New York style) built on Radix UI primitives with Tailwind CSS
- **Styling:** Tailwind CSS with CSS variables for theming (professional blue financial theme), custom fonts (Plus Jakarta Sans for body, Outfit for display)
- **Animations:** Framer Motion for page transitions and micro-interactions
- **Path aliases:** `@/` maps to `client/src/`, `@shared/` maps to `shared/`

### Backend

- **Framework:** Express 5 running on Node.js with TypeScript (via tsx)
- **API Structure:** RESTful endpoints defined in `shared/routes.ts` as a typed route map, with Zod schemas for request/response validation
- **Key endpoints:**
  - `POST /adfs/oauth2/token` — Authentication (proxy to UWM OAuth)
  - `POST /api/uwm/instantpricequote/v1/mortgagepricinglayout` — Get mortgage form layout
  - `POST /api/uwm/instantpricequote/v1/heloclayout` — Get HELOC form layout
  - `POST /api/uwm/instantpricequote/v1/mortgagepricingquote` — Get mortgage quote
  - `POST /api/uwm/instantpricequote/v1/helocquote` — Get HELOC quote
  - CRUD endpoints for saved scenarios
- **API Documentation:** Swagger/OpenAPI via swagger-jsdoc and swagger-ui-express at `/api-docs`
- **Build:** Custom build script using esbuild for server and Vite for client, outputs to `dist/`

### Shared Layer

- `shared/schema.ts` — Drizzle ORM table definitions and Zod validation schemas shared between client and server
- `shared/routes.ts` — Typed API route definitions with method, path, input schema, and response schemas, used by both frontend hooks and backend handlers

### Database

- **ORM:** Drizzle ORM with PostgreSQL dialect
- **Connection:** node-postgres (pg) Pool using `DATABASE_URL` environment variable
- **Schema:** Single `scenarios` table storing saved quotes with fields: id, loanAmount, borrowerName, creditScore, propertyZipCode, rawRequest (JSONB), rawResponse (JSONB), createdAt
- **Migrations:** Drizzle Kit with `db:push` command for schema sync

### Authentication

- Token-based auth proxying UWM's ADFS OAuth2 flow (password grant + refresh token)
- Client-side token stored in localStorage (demo/development approach)
- Custom `useAuth` hook manages login state, token storage, and provides `getToken()` for authenticated API calls
- All data-fetching hooks check for token before making requests

### UWM API Integration

- The app proxies requests to UWM's internal API (`uwm.internal.api:443`)
- Access requires an SSH tunnel through an Azure VM (PEM key auth) — the VM IP is whitelisted by UWM
- SSH tunnel maps `localhost:9000` to `uwm.internal.api:443`
- The UWM API reference (FastAPI-based) is captured in `attached_assets/uwm_api_*.py`

## External Dependencies

- **Database:** PostgreSQL (required, connection via `DATABASE_URL` env var)
- **UWM Public API:** United Wholesale Mortgage Instant Price Quote API v3.0 — requires OAuth2 credentials (client_id, client_secret, username, password) and network access via SSH tunnel
- **Azure VM:** SSH tunnel endpoint for accessing UWM's whitelisted internal API (PEM key at `~/.ssh/valargen-staging_key.pem`)
- **Google Fonts:** Plus Jakarta Sans, Outfit (loaded via CSS import and HTML link)
- **npm packages of note:** express, drizzle-orm, drizzle-zod, zod, @tanstack/react-query, react-hook-form, framer-motion, recharts, swagger-jsdoc, swagger-ui-express, wouter, date-fns