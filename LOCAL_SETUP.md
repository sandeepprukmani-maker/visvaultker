# VisionVault - Local Setup Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v20 or higher) - [Download here](https://nodejs.org/)
- **PostgreSQL** (v14 or higher) - [Download here](https://www.postgresql.org/download/)
- **Git** - [Download here](https://git-scm.com/)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd visionvault
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Database Setup

#### Create PostgreSQL Database

```bash
# Login to PostgreSQL
psql -U postgres

# Create a new database
CREATE DATABASE visionvault;

# Enable pgvector extension
\c visionvault
CREATE EXTENSION IF NOT EXISTS vector;

# Exit psql
\q
```

#### Configure Database Connection

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/visionvault
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=your_password
PGDATABASE=visionvault

# Node Environment
NODE_ENV=development
```

**Replace `your_password` with your PostgreSQL password.**

#### Push Database Schema

```bash
npm run db:push
```

This will create all necessary tables with the pgvector extension enabled.

### 4. API Keys Setup

VisionVault requires AI model API keys. Add them to your `.env` file:

```bash
# Google Gemini (recommended)
GOOGLE_AI_API_KEY=your_gemini_api_key

# OR OpenAI (alternative)
OPENAI_API_KEY=your_openai_api_key
```

**Get API Keys:**
- **Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI API**: [OpenAI Platform](https://platform.openai.com/api-keys)

### 5. Run the Application

#### Development Mode (with hot reload)

```bash
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:5000/api

#### Production Mode

```bash
# Build the application
npm run build

# Start production server
npm run start
```

## Project Structure

```
visionvault/
├── client/               # Frontend React application
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable UI components
│   │   └── lib/         # Utilities and helpers
├── server/              # Backend Express server
│   ├── index.ts         # Server entry point
│   ├── routes.ts        # API routes
│   ├── locator-generator.ts  # Code generation
│   └── semantic-cache.ts     # Gemini embeddings
├── shared/              # Shared types and schemas
│   └── schema.ts        # Database & API schemas
└── package.json
```

## Available Scripts

```bash
# Development
npm run dev              # Start dev server (port 5000)

# Database
npm run db:push          # Push schema changes to database
npm run db:studio        # Open Drizzle Studio (database GUI)

# Production
npm run build            # Build for production
npm run start            # Start production server
```

## Troubleshooting

### Port 5000 Already in Use

If port 5000 is already in use:

1. Find and kill the process using port 5000:
   ```bash
   # On macOS/Linux
   lsof -ti:5000 | xargs kill -9
   
   # On Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

2. Or change the port in `vite.config.ts`:
   ```typescript
   server: {
     port: 3000, // Change to any available port
   }
   ```

### Database Connection Issues

If you get database connection errors:

1. Verify PostgreSQL is running:
   ```bash
   # macOS
   brew services list
   
   # Linux
   sudo systemctl status postgresql
   
   # Windows
   # Check Services app for PostgreSQL service
   ```

2. Test your database connection:
   ```bash
   psql -U postgres -d visionvault -c "SELECT 1;"
   ```

3. Check your `.env` file has the correct credentials

### pgvector Extension Error

If you get "type 'vector' does not exist":

```bash
# Connect to your database
psql -U postgres -d visionvault

# Enable the extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Missing Dependencies

If you get module not found errors:

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Features

- **Natural Language Automation**: Describe what you want to automate in plain English
- **Locator-Based Code Generation**: Generates rerunnable Playwright code with XPath locators
- **Semantic Caching**: Uses Gemini embeddings to cache and reuse automations
- **Element Highlighting**: Visual feedback showing which elements are being interacted with
- **Execution History**: View and re-run past automations
- **Screenshot Capture**: Automatic screenshots of automation results

## Architecture

- **Frontend**: React + Vite + TailwindCSS + shadcn/ui
- **Backend**: Express.js + TypeScript
- **Database**: PostgreSQL + Drizzle ORM + pgvector
- **Automation**: Stagehand (Playwright wrapper)
- **AI Models**: Google Gemini 2.5 Flash (or OpenAI GPT-4)

## Development Tips

1. **Database Changes**: After modifying `shared/schema.ts`, run `npm run db:push` to sync
2. **View Database**: Use `npm run db:studio` to open Drizzle Studio GUI
3. **API Testing**: Backend API is available at `http://localhost:5000/api/*`
4. **WebSocket**: Real-time logs are streamed via WebSocket at `ws://localhost:5000`

## Next Steps

1. Get your API keys (Gemini or OpenAI)
2. Set up the database
3. Run `npm run dev`
4. Open http://localhost:5000
5. Try an automation: "Go to example.com and click the login button"

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review server logs in the terminal
- Check browser console for frontend errors
