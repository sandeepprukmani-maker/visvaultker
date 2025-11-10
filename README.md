# VisionVault

**AI-Powered Browser Automation with Rerunnable Code Generation**

VisionVault transforms natural language instructions into browser automations and generates rerunnable Playwright code with XPath locators—no LLM calls needed for re-execution.

![VisionVault Demo](https://img.shields.io/badge/Status-Production%20Ready-success)
![Node.js](https://img.shields.io/badge/Node.js-v20+-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-v14+-blue)

## ✨ Features

- 🤖 **Natural Language Automation** - Describe tasks in plain English
- 📝 **Locator-Based Code Generation** - Generates rerunnable Playwright code with XPath
- 🔄 **Semantic Caching** - Reuses similar automations using Gemini embeddings
- 👁️ **Element Highlighting** - Visual feedback during automation
- 📸 **Screenshot Capture** - Automatic screenshots of results
- 📊 **Execution History** - View and re-run past automations
- 💾 **Smart Storage** - PostgreSQL + pgvector for semantic search

## 🚀 Quick Start

### Prerequisites

- Node.js v20+
- PostgreSQL v14+
- Gemini or OpenAI API key

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd visionvault

# Install dependencies
npm install

# Setup database (see LOCAL_SETUP.md for details)
createdb visionvault
psql -d visionvault -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Configure environment
cp .env.example .env
# Add your API keys and database credentials

# Push database schema
npm run db:push

# Start development server
npm run dev
```

Visit http://localhost:5000 and start automating!

## 📖 Documentation

- **[Local Setup Guide](./LOCAL_SETUP.md)** - Detailed installation and configuration
- **[API Documentation](#)** - API endpoints and usage (coming soon)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           VisionVault Frontend          │
│   React + Vite + TailwindCSS + shadcn   │
└──────────────────┬──────────────────────┘
                   │ WebSocket + REST API
┌──────────────────┴──────────────────────┐
│       Express.js Backend Server         │
│    Natural Language → Automation        │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌──────▼─────┐  ┌───▼────┐
│Stagehand│  │  PostgreSQL │  │ Gemini │
│(Playwright)│  │+ pgvector  │  │  AI   │
└─────────┘  └────────────┘  └────────┘
```

**Tech Stack:**
- **Frontend**: React, Vite, TailwindCSS, shadcn/ui
- **Backend**: Express.js, TypeScript
- **Database**: PostgreSQL, Drizzle ORM, pgvector
- **Automation**: Stagehand (Playwright wrapper)
- **AI**: Google Gemini 2.5 Flash (or OpenAI GPT-4)

## 💡 Usage Examples

### Simple Click Action
```
Go to github.com and click the sign in button
```

### Form Filling
```
Navigate to example.com, fill the email field with test@email.com, and submit the form
```

### Data Extraction
```
Go to news.ycombinator.com and extract the top 5 story titles
```

### Multi-Step Agent
```
Go to amazon.com, search for "wireless mouse", and add the first result to cart
```

## 🎯 How It Works

1. **Natural Language Parsing** - Intelligent prompt analysis extracts URL and task
2. **Semantic Cache Check** - Searches for similar past automations (0.85 similarity)
3. **Browser Automation** - Stagehand executes using AI vision models
4. **Step Capture** - Records all interactions with XPath selectors
5. **Code Generation** - Creates two versions:
   - **Locator-based**: Rerunnable Playwright code (no AI needed)
   - **Template-based**: Starter code with your specific task
6. **Result Storage** - Saves to PostgreSQL with vector embeddings

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/visionvault

# AI Models (choose one or both)
GOOGLE_AI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Environment
NODE_ENV=development
```

## 📦 Project Structure

```
visionvault/
├── client/               # React frontend
│   ├── src/
│   │   ├── pages/       # Route pages (Home, History, Cache)
│   │   ├── components/  # UI components
│   │   └── lib/         # Utilities
├── server/              # Express backend
│   ├── index.ts         # Server entry
│   ├── routes.ts        # API endpoints
│   ├── locator-generator.ts  # Code generation
│   ├── intelligent-router.ts # Prompt parsing
│   └── semantic-cache.ts     # Vector search
├── shared/              # Shared types
│   └── schema.ts        # Database schemas
└── package.json
```

## 🛠️ Development

```bash
# Start dev server with hot reload
npm run dev

# Type checking
npm run check

# Build for production
npm run build

# Start production server
npm run start

# Database management
npm run db:push         # Push schema changes
npm run db:studio       # Open database GUI
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Stagehand](https://github.com/browserbase/stagehand) - Browser automation framework
- [Drizzle ORM](https://orm.drizzle.team/) - TypeScript ORM
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search

---

**Need help?** Check out the [Local Setup Guide](./LOCAL_SETUP.md) for detailed instructions.
