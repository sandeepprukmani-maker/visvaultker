# VisionVault - Local Setup Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v20 or higher) - [Download here](https://nodejs.org/)
- **Python** (v3.11 or higher) - [Download here](https://www.python.org/downloads/)
- **Git** - [Download here](https://git-scm.com/)

## Installation Steps

### 1. Download from Replit (if applicable)

If you're downloading this project from Replit:
1. Navigate to the **Files** tool in your Replit workspace
2. Select the option to download the entire folder
3. Extract the downloaded ZIP file

Alternatively, clone from Git:
```bash
git clone <your-repo-url>
cd visionvault
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Install Python Dependencies

Create a Python virtual environment and install packages:

```bash
# Create virtual environment
python -m venv .pythonlibs

# Activate virtual environment
# On macOS/Linux:
source .pythonlibs/bin/activate
# On Windows:
.pythonlibs\Scripts\activate

# Install dependencies
pip install uvicorn fastapi sqlalchemy numpy
```

### 4. Database Setup

**No manual database setup required!** VisionVault uses SQLite, which automatically creates the database file (`visionvault.db`) on first run.

### 5. API Keys Setup

VisionVault requires AI model API keys. Create a `.env` file in the project root:

```bash
# Google Gemini (recommended for embeddings and automation)
GOOGLE_AI_API_KEY=your_gemini_api_key

# OpenAI (optional alternative)
OPENAI_API_KEY=your_openai_api_key

# Browserbase (optional - for cloud browser automation)
BROWSERBASE_API_KEY=your_browserbase_key
BROWSERBASE_PROJECT_ID=your_project_id

# Node Environment
NODE_ENV=development
```

**Get API Keys:**
- **Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenAI API**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Browserbase**: [Browserbase Dashboard](https://www.browserbase.com/)

### 6. Run the Application

The application uses both Node.js and Python servers:

#### Development Mode (with hot reload)

```bash
# Make the startup script executable (macOS/Linux only)
chmod +x start-servers.sh

# Start both servers
./start-servers.sh
```

**On Windows**, run both servers manually in separate terminals:

Terminal 1 (Python API):
```bash
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 (Node.js):
```bash
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5000
- **Node.js Backend**: http://localhost:5000/api
- **Python API**: http://localhost:8000

#### Production Mode

```bash
# Build the frontend
npm run build

# Start both servers in production mode
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 &
npm run start
```

## Project Structure

```
visionvault/
├── client/                  # Frontend React application
│   ├── src/
│   │   ├── pages/          # Page components (Home, History, Cache)
│   │   ├── components/     # Reusable UI components
│   │   └── lib/            # Utilities and helpers
├── server/                 # Backend servers
│   ├── index.ts           # Node.js Express server (port 5000)
│   ├── routes.ts          # API routes for automation
│   ├── locator-generator.ts  # Playwright code generation
│   ├── main.py            # Python FastAPI server (port 8000)
│   ├── models.py          # SQLAlchemy database models
│   ├── database.py        # SQLite connection
│   └── api-client.ts      # Node→Python API client
├── shared/                # Shared types and schemas
│   └── schema.ts          # TypeScript schemas
├── visionvault.db         # SQLite database (auto-created)
└── package.json
```

## Architecture

**Hybrid Node.js + Python Setup:**
- **Node.js (Port 5000)**: Frontend + Stagehand browser automation + WebSocket logs
- **Python (Port 8000)**: Database operations + Semantic search with NumPy
- **Database**: SQLite with JSON-stored embeddings (768-dimensional vectors)

## Available Scripts

```bash
# Development
npm run dev              # Start Node.js dev server only
./start-servers.sh       # Start both Node.js + Python servers

# Production
npm run build            # Build frontend for production
npm run start            # Start production server
```

## Troubleshooting

### Port Already in Use

**Port 5000 conflict:**
```bash
# On macOS/Linux
lsof -ti:5000 | xargs kill -9

# On Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Port 8000 conflict (Python API):**
```bash
# On macOS/Linux
lsof -ti:8000 | xargs kill -9

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Python Server Not Starting

If you get "No module named uvicorn":

```bash
# Activate virtual environment
source .pythonlibs/bin/activate  # macOS/Linux
.pythonlibs\Scripts\activate     # Windows

# Install dependencies
pip install uvicorn fastapi sqlalchemy numpy
```

### Database Issues

The SQLite database is automatically created. If you have issues:

```bash
# Delete and recreate database
rm visionvault.db

# Restart the servers - database will be recreated
./start-servers.sh
```

### Missing API Keys

If automation fails with API errors:

1. Check your `.env` file has `GOOGLE_AI_API_KEY` set
2. Verify the API key is valid at [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Restart the servers after adding the key

### Node Module Errors

```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Features

- ✅ **Natural Language Automation**: Describe tasks in plain English
- ✅ **Locator-Based Code Generation**: Generates rerunnable Playwright code with XPath
- ✅ **Semantic Caching**: Uses Gemini embeddings (768-dim) for intelligent caching
- ✅ **Element Highlighting**: Visual feedback during automation
- ✅ **Execution History**: View, replay, and delete past automations
- ✅ **Screenshot Capture**: Automatic screenshots of results
- ✅ **Multi-Mode Support**: act, observe, extract, and agent modes

## Tech Stack

- **Frontend**: React + Vite + TailwindCSS + shadcn/ui
- **Node.js Backend**: Express.js + TypeScript + Stagehand
- **Python Backend**: FastAPI + SQLAlchemy + NumPy
- **Database**: SQLite (file-based, no setup required)
- **AI Models**: Google Gemini 2.5 Flash (or OpenAI GPT-4)
- **Browser Automation**: Playwright via Stagehand

## Development Tips

1. **Both servers must run**: The Node.js server handles automation, Python handles database
2. **Database location**: `visionvault.db` file in project root
3. **View data**: Use a SQLite browser like [DB Browser for SQLite](https://sqlitebrowser.org/)
4. **API endpoints**:
   - Node.js automation: `http://localhost:5000/api/automate`
   - Python history: `http://localhost:8000/api/history`
   - Python cache: `http://localhost:8000/api/cache`
5. **WebSocket logs**: Real-time automation logs at `ws://localhost:5000`

## Seed Dummy Data

To add sample automation records for testing:

```bash
# Activate Python virtual environment first
source .pythonlibs/bin/activate  # macOS/Linux
.pythonlibs\Scripts\activate     # Windows

# Run seed script
python server/seed_dummy_data.py
```

This adds 5 sample automation records with embeddings.

## Next Steps

1. ✅ Install Node.js and Python dependencies
2. ✅ Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. ✅ Add API key to `.env` file
4. ✅ Run `./start-servers.sh` (or both servers manually on Windows)
5. ✅ Open http://localhost:5000
6. ✅ Try: "Go to example.com and find the heading"

## Example Automations to Try

```
Go to Google and search for 'web automation tools'
Navigate to GitHub and click the sign in button
Extract the main heading from Wikipedia
Go to Amazon and search for 'wireless headphones'
```

## Support

For issues or questions:
- Check the Troubleshooting section above
- Review terminal logs from both Node.js and Python servers
- Check browser console for frontend errors
- Verify both servers are running on ports 5000 and 8000

---

**Happy Automating! 🚀**
