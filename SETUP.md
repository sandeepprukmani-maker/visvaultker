# Setup Instructions for Stagehand UI

This document provides instructions for setting up and running the Stagehand UI project in a local environment.

## Prerequisites

- **Node.js**: Version 18 or higher.
- **Python**: Version 3.x.
- **Chromium/Chrome**: Installed on your system.

## Environment Variables

Ensure the following environment variable is set:

- `CHROME_PATH`: The full path to your Chromium or Chrome executable.

On Replit, this is typically:
`/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium`

## Installation

1. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

2. **Database Setup**:
   The project uses SQLite for local development. The database file `sqlite.db` is created automatically. To initialize or sync the schema, run:
   ```bash
   npm run db:push
   ```
   (Note: You might need to use `--force` if switching from an existing PostgreSQL database).

## Configuration

1. **OAuth Token**:
   The application uses `fetch_token.py` to retrieve an OAuth token for the custom AI provider. Update `fetch_token.py` with your real OAuth logic.

2. **Custom AI Provider**:
   The backend is configured to use an internal RBC endpoint. If you need to change the model or endpoint, update `server/stagehand.ts`.

## Running the Application

Start the development server (runs both frontend and backend):
```bash
npm run dev
```

The application will be available at `http://0.0.0.0:5000`.

## Project Structure

- `client/`: React frontend source code.
- `server/`: Express backend, Stagehand logic, and database storage.
- `shared/`: Shared types, Zod schemas, and route definitions.
- `fetch_token.py`: Python script for OAuth token retrieval.
