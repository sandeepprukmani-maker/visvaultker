# Setup and Running Instructions

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** (for Playwright MCP server)

## Installation

### 1. Install Node.js Dependencies

```bash
npm install -g @playwright/mcp
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browser

```bash
playwright install chromium
```

On Linux, you may also need system dependencies:
```bash
playwright install-deps chromium
```

## Configuration

### Set Up API Keys

You need at least one AI model API key. Set as environment variables:

**For Claude (Recommended):**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**For GPT-4o:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**For Gemini:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
ANTHROPIC_API_KEY=your-api-key-here
OPENAI_API_KEY=your-api-key-here
GEMINI_API_KEY=your-api-key-here
```

## Running the Tool

### Basic Usage

```bash
python main.py "Navigate to example.com and click the login button"
```

### With Different Models

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

# Full help
python main.py --help
```

## Example Tasks

### E-commerce Automation
```bash
python main.py "Go to amazon.com, search for laptop, and click the first result"
```

### Form Filling
```bash
python main.py "Navigate to example.com/contact and fill out the contact form with test data"
```

### Web Scraping
```bash
python main.py "Go to news.ycombinator.com and get the top 5 story titles"
```

### Testing Workflow
```bash
python main.py "Go to github.com, search for playwright, and click the first repository"
```

## Output

Generated scripts are saved to `generated_scripts/` directory with timestamps:
```
generated_scripts/
├── automation_Navigate_to_example_com_20251106_143022.py
├── automation_Fill_out_contact_form_20251106_144533.py
└── automation_Search_for_laptop_20251106_145612.py
```

Each script is:
- ✅ Fully runnable standalone Python file
- ✅ Uses async/await patterns
- ✅ Has intelligent locators (get_by_role, get_by_label, etc.)
- ✅ Includes proper imports and error handling

## Running Generated Scripts

```bash
# Run any generated script directly
python generated_scripts/automation_*.py
```

## Troubleshooting

### "MCP server failed to start"
- Ensure Node.js is installed: `node --version`
- Verify @playwright/mcp is installed: `npm list -g @playwright/mcp`

### "Chromium browser not found"
```bash
playwright install chromium
```

### "Missing API key"
- Check environment variables are set: `echo $ANTHROPIC_API_KEY`
- Verify the key is valid and has credits

### "Import errors"
```bash
pip install -r requirements.txt --upgrade
```

## System Requirements

### Minimum
- Python 3.11+
- Node.js 20+
- 2GB RAM
- 1GB disk space

### Recommended
- Python 3.11+
- Node.js 20+
- 4GB RAM
- 2GB disk space
- Display server (X11/Wayland for visible browser)

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

## Quick Start (Copy-Paste)

```bash
# Install everything
npm install -g @playwright/mcp
pip install -r requirements.txt
playwright install chromium

# Set API key (choose one)
export ANTHROPIC_API_KEY="your-key-here"

# Run your first automation
python main.py "Go to example.com and click the More information link"

# Check the generated script
ls -la generated_scripts/
```

## Support

For issues with:
- **Playwright MCP**: https://github.com/microsoft/playwright-mcp
- **Claude API**: https://docs.anthropic.com/
- **OpenAI API**: https://platform.openai.com/docs
- **Gemini API**: https://ai.google.dev/docs
