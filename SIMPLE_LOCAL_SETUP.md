# VisionVault - Simple Local Setup (No Database)

Run VisionVault on your local machine with **just Node.js** - no PostgreSQL required!

## Quick Start (5 minutes)

### 1. Prerequisites

- **Node.js v20+** - [Download here](https://nodejs.org/)
- That's it! No database needed.

### 2. Download & Install

```bash
# If you have the project folder:
cd visionvault

# Install dependencies
npm install
```

### 3. Configure API Key

Create a `.env` file in the project root:

```bash
# Required: AI model for browser automation
OPENAI_API_KEY=sk-your-openai-api-key-here

# That's all you need!
```

**Get your OpenAI API key:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 4. Run the App

```bash
npm run dev
```

Visit **http://localhost:5000** and start automating!

---

## What Works Without Database

✅ **Browser Automation** - All automation modes (act, observe, extract, agent)
✅ **Code Generation** - Get TypeScript code for your automations  
✅ **Live Execution Logs** - See what's happening in real-time
✅ **Screenshots** - Capture results during automation

## What's Disabled

❌ **History** - Past automations aren't saved (lost when you close the app)
❌ **Semantic Cache** - Can't reuse similar automations
❌ **Cache Viewer** - No cache to view

---

## Example Automations to Try

Once the app is running, try these prompts:

```
Go to example.com and click the "More information" link
```

```
Navigate to github.com and find the search bar
```

```
Go to news.ycombinator.com and extract the top story title
```

---

## Advanced: Enable Database (Optional)

Want to save history and enable caching? You'll need PostgreSQL:

1. Install PostgreSQL v14+
2. Create a database: `createdb visionvault`
3. Enable vector extension: `psql -d visionvault -c "CREATE EXTENSION vector;"`
4. Add to `.env`:
   ```bash
   DATABASE_URL=postgresql://username:password@localhost:5432/visionvault
   ```
5. Push schema: `npm run db:push`
6. Restart: `npm run dev`

See **LOCAL_SETUP.md** for full database setup instructions.

---

## Troubleshooting

### Port 5000 Already in Use

```bash
# Kill the process using port 5000
# macOS/Linux:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### "OPENAI_API_KEY not set" Error

Make sure you:
1. Created the `.env` file in the project root (not in a subfolder)
2. Added your actual API key (starts with `sk-`)
3. Restarted the server after adding the key

---

## Need Help?

- Check **LOCAL_SETUP.md** for detailed setup with database
- Check **README.md** for project overview and architecture

---

**Happy Automating! 🚀**
