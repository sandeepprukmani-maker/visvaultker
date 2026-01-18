# Visvaultker - Mortgage Pulse Application

## Overview

This is a full-stack mortgage market intelligence application called "Mortgage Pulse." It fetches real-time mortgage rate news from RSS feeds (Mortgage News Daily), stores articles in a PostgreSQL database, and generates AI-powered social media captions for loan officers using Replit's native OpenAI integration.

## User Preferences

- Simple, everyday language.
- Prefers using Replit native integrations.

## System Architecture

### Frontend Architecture
- React 18 with TypeScript, Wouter, Tailwind CSS, shadcn/ui.
- Bound to port 5000 on 0.0.0.0.

### Backend Architecture
- Express.js, Node.js, Drizzle ORM, PostgreSQL.
- Native OpenAI integration for caption generation.

### Integration
- `blueprint:javascript_openai_ai_integrations` used for AI features.
- Chat and Image modules included.

## Recent Changes
- Fixed AI configuration error by switching to Replit's native OpenAI integration.
- Configured PostgreSQL database and pushed schema.
- Set up development and production workflows.
- Cleaned up redundant directories from GitHub import.
