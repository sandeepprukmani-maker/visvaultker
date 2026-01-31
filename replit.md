# Mortgage News Video Generator

## Overview
The Mortgage News Video Generator is an application designed to automate the creation of professional AI-generated videos featuring mortgage news. It fetches content from RSS feeds, rephrases it into concise marketing scripts using AI, and then produces videos with custom promotional banner overlays via the HeyGen API. The primary purpose is to deliver engaging video content for first-time home buyers and refinancers, enhancing market reach and content production efficiency.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Core Functionality
The application automates video content creation through several stages: content fetching from RSS feeds, AI-driven script generation (25-second, 60-65 words) tailored for first-time home buyers and refinancers, HeyGen API integration for video generation with avatar settings, and FFmpeg post-processing for adding customizable promotional banner overlays. Videos can be reprocessed with updated banners.

### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: Wouter
- **State Management**: TanStack React Query
- **UI Components**: shadcn/ui (built on Radix UI)
- **Styling**: Tailwind CSS with custom CSS variables (light/dark mode)
- **Build Tool**: Vite

### Backend
- **Framework**: Express.js with TypeScript
- **API Design**: RESTful with Zod schema validation
- **Database ORM**: Drizzle ORM with PostgreSQL
- **Video Processing**: fluent-ffmpeg for banner overlays
- **AI Integration**: OpenAI API for content rephrasing
- **External APIs**: HeyGen API, Mortgage News Daily RSS

### Data Storage
- **Database**: PostgreSQL
- **ORM**: Drizzle ORM
- **Key Tables**: `users`, `videos` (metadata), `api_keys` (HeyGen key management), `conversations`, `messages`.

### Project Structure
- `client/`: React frontend.
- `server/`: Express backend, including API routes, database operations, and connection.
- `shared/`: Shared types, Drizzle schema, and API route definitions.
- `public/`: Stores uploaded banner images and processed videos.
- `attached_assets/`: Default assets.
- `migrations/`: Database migrations.

### Technical Implementations
- **FFmpeg Handling**: Videos are downloaded locally before FFmpeg processing to prevent streaming corruption. `movflags +faststart` is avoided, and H.264 baseline profile with level 3.0 is used for maximum compatibility.
- **API Key Management**: HeyGen API keys are managed via the UI and stored in the database, not as environment variables.
- **Error Handling**: Includes mechanisms to auto-delete stuck HeyGen videos after 20 minutes (only if HeyGen is still processing, not during FFmpeg reprocessing).

## External Dependencies

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string.
- `OPENAI_API_KEY`: OpenAI API key.
- `AI_INTEGRATIONS_OPENAI_API_KEY`: (Optional) OpenAI API key for Replit AI Integrations.
- `AI_INTEGRATIONS_OPENAI_BASE_URL`: (Optional) OpenAI base URL for Replit AI Integrations.

### Third-Party Services
- **PostgreSQL**: Primary database.
- **OpenAI API**: For rephrasing news content into marketing scripts.
- **HeyGen API**: For avatar-based video generation.
- **Mortgage News Daily RSS**: Source for mortgage news content.

### Key NPM Packages
- `drizzle-orm`, `drizzle-kit`
- `@tanstack/react-query`
- `openai`
- `fluent-ffmpeg`
- `xml2js`
- `zod`
- `express`
- `multer`