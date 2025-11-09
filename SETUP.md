# Stagehand Automation Studio - Setup Guide

## Prerequisites

- Node.js 20+ installed
- Chrome/Chromium browser installed on your system

## Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Install Playwright browsers:**
   ```bash
   npx playwright install chromium
   ```

3. **Set up environment variables:**
   
   Copy the example file:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your API key. **Choose one based on which AI model you want to use:**

   **For Google Gemini (recommended for beginners):**
   - Get your API key from: https://aistudio.google.com/app/apikey
   - Add to `.env`:
     ```
     GOOGLE_GENERATIVE_AI_API_KEY=your_actual_key_here
     ```

   **For OpenAI (GPT models):**
   - Get your API key from: https://platform.openai.com/api-keys
   - Add to `.env`:
     ```
     OPENAI_API_KEY=your_actual_key_here
     ```

   **For Anthropic (Claude models):**
   - Get your API key from: https://console.anthropic.com/
   - Add to `.env`:
     ```
     ANTHROPIC_API_KEY=your_actual_key_here
     ```

## Running the Application

**Development mode (with hot reload):**
```bash
npm run dev
```

The app will start on http://localhost:5000

**When you execute an automation:**
- A visible Chrome browser window will open on your screen
- You can watch the automation happen in real-time
- The execution log and generated code appear in the UI

## Available Models

You can select different models in the Advanced Configuration section of the UI:

- `google/gemini-2.5-flash` (default, fast and cheap)
- `google/gemini-2.5-pro` (more powerful)
- `openai/gpt-4.1-mini` (requires OpenAI key)
- `anthropic/claude-3.7-sonnet` (requires Anthropic key)

## Automation Modes

- **Act**: Execute single actions ("Click the login button")
- **Observe**: Discover available elements and actions on a page
- **Extract**: Pull structured data from pages using natural language
- **Agent**: Autonomous multi-step workflows

## Troubleshooting

**Error: "API key not found"**
- Make sure you created the `.env` file from `.env.example`
- Check that the API key matches the model provider you're using

**Error: "Executable doesn't exist"**
- Run `npx playwright install chromium`

**Browser doesn't open:**
- Check that Chrome/Chromium is installed on your system
- Make sure `headless: false` is set in `server/routes.ts`

## Cloud Alternative (BrowserBase)

If you want to use cloud browsers instead of local:

1. Sign up at https://browserbase.com
2. Get your API key and project ID
3. Add to `.env`:
   ```
   BROWSERBASE_API_KEY=your_key
   BROWSERBASE_PROJECT_ID=your_project_id
   ```
4. Change `env: "BROWSERBASE"` in `server/routes.ts`
