# Running ZenSmart Executor Locally

This guide will help you set up and run the ZenSmart Executor application on your local machine.

## Prerequisites

- **Node.js** (v20 or higher)
- **npm** (comes with Node.js)
- **Git** (for cloning the repository)

## Installation Steps

### 1. Clone or Download the Project

```bash
# If using git
git clone <your-repository-url>
cd <project-directory>

# Or download and extract the ZIP file
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages including:
- Express (backend server)
- React + Vite (frontend)
- Stagehand (browser automation)
- OpenAI, Anthropic, and Google AI SDKs

### 3. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
# Copy the example file if it exists
cp .env.example .env

# Or create a new .env file
touch .env
```

Add your API keys to the `.env` file:

```env
# Required: At least one API key is needed
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GEMINI_API_KEY=your-google-api-key-here

# Optional: Database configuration
# If not set, the app will use in-memory storage
DATABASE_URL=your-database-url-here
```

### 4. Get API Keys

#### OpenAI API Key (for GPT-4o Mini)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste it into your `.env` file

#### Anthropic API Key (for Claude)
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy and paste it into your `.env` file

#### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign up or log in
3. Create a new API key
4. Copy and paste it into your `.env` file

### 5. Run the Application

```bash
npm run dev
```

This will start:
- **Backend server** on `http://localhost:5000`
- **Frontend development server** (Vite) integrated with backend

### 6. Access the Application

Open your browser and navigate to:

```
http://localhost:5000
```

## Current Configuration

### AI Models

The application currently uses:
- **OpenAI**: `gpt-4o-mini` (fast and cost-effective)
- **Anthropic**: `claude-3-5-sonnet-20241022` (advanced reasoning)
- **Google**: `gemini-2.0-flash-exp` (multimodal capabilities)

You can select which model to use from the Settings panel (gear icon) in the application.

## Project Structure

```
.
├── client/              # Frontend React application
│   └── src/
│       ├── components/  # UI components
│       ├── pages/      # Page components
│       └── lib/        # Utilities and helpers
├── server/             # Backend Express application
│   ├── index.ts       # Server entry point
│   ├── routes.ts      # API routes
│   ├── automation.ts  # Browser automation logic
│   └── storage.ts     # Data storage interface
├── shared/            # Shared types and schemas
│   └── schema.ts      # Database schemas
└── package.json       # Dependencies and scripts
```

## Available Scripts

```bash
# Development mode (runs both frontend and backend)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Database migrations (if using PostgreSQL)
npm run db:push

# Type checking
npm run check
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, you can change it in `server/index.ts`:

```typescript
const PORT = process.env.PORT || 5000; // Change 5000 to another port
```

### Missing API Keys

If you see an error about missing API keys:
1. Ensure your `.env` file exists in the root directory
2. Verify the API key variable names match exactly
3. Restart the development server after adding keys

### Browser Automation Issues

Stagehand uses Playwright under the hood. If you encounter browser-related issues:

```bash
# Install Playwright browsers
npx playwright install
```

## Production Deployment

For production deployment:

1. Set `NODE_ENV=production`
2. Build the application: `npm run build`
3. Start the server: `npm start`
4. Ensure all environment variables are set in your hosting environment

## Need Help?

- Check the [Replit deployment](your-replit-url) for a working example
- Review the code comments in key files
- Check the browser console for frontend errors
- Check the terminal output for backend errors

## Database

By default, the application uses **in-memory storage** (MemStorage). This means:
- Data is stored in RAM
- Data is lost when the server restarts
- Suitable for development and testing

For persistent storage, set up a PostgreSQL database and provide the `DATABASE_URL` in your `.env` file.
