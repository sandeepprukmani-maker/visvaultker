# Playwright MCP Automation Script Generator

Convert natural language to production-ready Python Playwright automation scripts using AI and Microsoft's Playwright MCP.

**✅ Fully Cross-Platform: Windows 10/11, macOS, and Linux**

## Features

- 🤖 **AI-Powered Automation**: Describe tasks in plain English, watch them execute live
- 🔧 **Intelligent Code Generation**: Creates clean Python scripts with best-practice locators
- 🩹 **Auto-Healing**: Automatically fixes broken scripts by analyzing errors
- 🎯 **Smart Locators**: Prioritizes accessible selectors over fragile CSS
- 🚀 **Multi-Model Support**: Claude 4 Sonnet (recommended), GPT-4o, or Gemini 2.0 Flash
- 🌐 **Real MCP Integration**: Uses Microsoft's official `@playwright/mcp` server
- 💻 **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux

## Quick Start

### Windows Users

See **[WINDOWS.md](WINDOWS.md)** for detailed Windows setup instructions.

Quick setup (PowerShell):
```powershell
npm install -g @playwright/mcp
pip install -r requirements.txt
playwright install chromium
$env:ANTHROPIC_API_KEY="your-key-here"
python main.py "Go to example.com"
```

### macOS/Linux Users

See **[SETUP.md](SETUP.md)** for complete setup instructions.

Quick setup (Bash/Zsh):
```bash
npm install -g @playwright/mcp
pip install -r requirements.txt
playwright install chromium
export ANTHROPIC_API_KEY="your-key-here"
python main.py "Go to example.com"
```

## Installation

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**

### Install Dependencies

```bash
# Install Node.js package (Microsoft's Playwright MCP)
npm install -g @playwright/mcp

# Install Python packages
pip install -r requirements.txt

# Install browser
playwright install chromium
```

### Set API Key

You need at least one AI model API key:

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
```

**macOS/Linux (Bash):**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Usage

### Basic Usage

```bash
python main.py "Navigate to example.com and click the login button"
```

### Choose AI Model

```bash
# Use Claude (default, recommended)
python main.py "Your task description"

# Use GPT-4o
python main.py "Your task description" --model gpt4o

# Use Gemini
python main.py "Your task description" --model gemini
```

### Additional Options

```bash
# Custom output file
python main.py "Your task" --output custom_script.py

# Disable auto-healing
python main.py "Your task" --no-heal

# Show help
python main.py --help
```

## Example Tasks

### E-commerce Automation
```bash
python main.py "Go to amazon.com, search for laptop, and click the first result"
```

### Form Filling
```bash
python main.py "Navigate to example.com/contact and fill out the contact form"
```

### Web Scraping
```bash
python main.py "Go to news.ycombinator.com and get the top 5 story titles"
```

### Testing Workflow
```bash
python main.py "Go to github.com, search for playwright, and click the first repository"
```

## How It Works

### Two-Phase AI Workflow

1. **Execution Phase**: Executor agent performs the task live in a visible browser using MCP tools
2. **Generation Phase**: Code generator creates a clean, reusable Python script from the execution trace

### Auto-Healing

If the generated script fails during testing:
1. Healer agent analyzes the error and trace files
2. Identifies broken locators or timing issues
3. Regenerates the script with fixes
4. Saves as `*_healed.py`

## Generated Code Quality

Scripts include:
- ✅ Proper async/await patterns
- ✅ Intelligent locators (`get_by_role`, `get_by_label`, etc.)
- ✅ Error handling
- ✅ Clean imports and structure
- ✅ Comments for clarity

## Output

Generated scripts are saved to `generated_scripts/` directory with timestamps:
```
generated_scripts/
├── automation_Navigate_to_example_com_20251106_143022.py
├── automation_Fill_out_contact_form_20251106_144533.py
└── automation_Search_for_laptop_20251106_145612.py
```

Run any generated script:
```bash
python generated_scripts/automation_*.py
```

## Documentation

- **[WINDOWS.md](WINDOWS.md)** - Windows-specific setup guide
- **[SETUP.md](SETUP.md)** - Complete setup instructions for all platforms
- **[read_me.md](read_me.md)** - Technical architecture documentation
- **[requirements.txt](requirements.txt)** - Python dependencies

## Troubleshooting

### Windows Issues

See [WINDOWS.md](WINDOWS.md) for Windows-specific troubleshooting.

Common issues:
- `npx` not found: Restart terminal after installing Node.js
- Permission errors: Run PowerShell as Administrator
- Antivirus blocking: Add Python/Node.js to exclusions

### All Platforms

**MCP server failed to start:**
- Verify Node.js: `node --version`
- Verify MCP installed: `npm list -g @playwright/mcp`

**Missing API key:**
- Windows: `echo $env:ANTHROPIC_API_KEY`
- macOS/Linux: `echo $ANTHROPIC_API_KEY`

**Browser not found:**
```bash
playwright install chromium
```

## System Requirements

**Minimum:**
- Python 3.11+
- Node.js 20+
- 2GB RAM
- 1GB disk space

**Recommended:**
- Python 3.11+
- Node.js 20+
- 4GB RAM
- 2GB disk space

## Architecture

```
┌─────────────┐
│   CLI User  │
└──────┬──────┘
       │
       v
┌──────────────────┐
│    main.py       │ ← Entry point
└──────┬───────────┘
       │
       v
┌──────────────────────────────────────┐
│          MCP Client                  │
│  (mcp_client.py)                     │
│  Connects to @playwright/mcp server  │
└──────┬───────────────────────────────┘
       │
       v
┌──────────────────────────────────────┐
│       AI Agents (agents.py)          │
│  • ExecutorAgent                     │
│  • CodeGeneratorAgent                │
│  • HealerAgent                       │
└──────┬───────────────────────────────┘
       │
       v
┌──────────────────────────────────────┐
│   Generated Python Scripts           │
│   (generated_scripts/*.py)           │
└──────────────────────────────────────┘
```

## Getting API Keys

### Claude (Anthropic) - Recommended
1. Visit https://console.anthropic.com/
2. Sign up / Login
3. Go to "API Keys"
4. Create new key

### GPT-4o (OpenAI)
1. Visit https://platform.openai.com/
2. Sign up / Login
3. Go to "API Keys"
4. Create new secret key

### Gemini (Google)
1. Visit https://aistudio.google.com/
2. Sign up / Login
3. Click "Get API Key"
4. Create new API key

## Support

For detailed help:
- **Windows**: See [WINDOWS.md](WINDOWS.md)
- **All Platforms**: See [SETUP.md](SETUP.md)
- **Architecture**: See [read_me.md](read_me.md)

For issues with:
- **Playwright MCP**: https://github.com/microsoft/playwright-mcp
- **Claude API**: https://docs.anthropic.com/
- **OpenAI API**: https://platform.openai.com/docs
- **Gemini API**: https://ai.google.dev/docs

## License

MIT
