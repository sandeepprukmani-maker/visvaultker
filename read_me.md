# Playwright MCP Automation Script Generator

## Overview

This project is a natural language to Playwright automation script generator. It uses AI models (Claude, GPT-4o, or Gemini) to convert plain English task descriptions into executable Python Playwright scripts through the Model Context Protocol (MCP). The system employs a multi-agent architecture where an Executor Agent performs browser automation tasks, a Code Generator Agent translates execution traces into reusable scripts, and a Healer Agent attempts to fix failed scripts automatically.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Multi-Agent Architecture

**Problem**: Need to convert natural language to reliable, reusable browser automation scripts.

**Solution**: Three-agent system with distinct responsibilities:
- **Executor Agent**: Performs live browser automation using Playwright MCP tools
- **Code Generator Agent**: Converts execution traces into standalone Python scripts
- **Healer Agent**: Analyzes and fixes failing scripts (optional, enabled by default)

**Rationale**: Separating execution from code generation allows the system to learn from actual browser interactions rather than generating code blindly. The healing layer adds robustness by automatically recovering from common automation failures.

### Model Abstraction Layer

**Problem**: Support multiple AI providers (Anthropic, OpenAI, Google) with different APIs.

**Solution**: Unified `ModelType` configuration system in `config.py` with provider-specific client initialization in agent classes.

**Implementation Details**:
- Each model has standardized configuration including name, API key, and display name
- Agents dynamically instantiate the appropriate client based on model selection
- Gemini integration is optional (graceful degradation if SDK unavailable)

**Alternatives Considered**: Could have used LangChain or similar abstraction, but opted for direct SDK usage for simplicity and control.

### MCP Integration Pattern

**Problem**: Enable AI agents to control browser automation tools through a standard protocol.

**Solution**: Playwright MCP client wrapper (`PlaywrightMCPClient`) that:
- Manages stdio-based communication with the Playwright MCP server
- Exposes browser automation capabilities as tool descriptions for AI consumption
- Handles tool execution and result formatting

**Key Design Decision**: The MCP server runs as an external Node.js process (`npx @playwright/mcp`), communicating via stdio. This keeps the Python codebase lightweight while leveraging the full Playwright ecosystem.

### Execution Trace System

**Problem**: Bridge the gap between interactive automation and script generation.

**Solution**: The Executor Agent maintains a detailed execution trace as it performs tasks. Each action (navigate, click, fill, etc.) is logged with parameters and results. This trace becomes the primary input for the Code Generator Agent.

**Benefits**:
- Provides concrete examples of working automation sequences
- Enables the Code Generator to produce accurate, tested scripts
- Allows the Healer to understand what was originally intended

### Configuration Management

**Problem**: Handle API keys, model selection, and runtime parameters securely.

**Solution**: Environment-based configuration through `config.py`:
- API keys loaded from environment variables
- Model configurations centralized with clear defaults
- Filesystem paths (output directories, trace storage) defined as constants

**Security Consideration**: API keys never hardcoded; must be provided via environment variables.

### Output Management

**Problem**: Organize generated scripts and execution traces for reusability and debugging.

**Solution**: 
- Generated scripts saved to `OUTPUT_DIR` (default: `generated_scripts/`)
- Execution traces saved to `TRACE_DIR` for analysis
- Auto-generated filenames with timestamps for uniqueness
- Rich console output for real-time progress visualization

### Error Recovery Architecture

**Problem**: Generated scripts may fail due to selector issues, timing problems, or site changes.

**Solution**: Optional auto-healing system (controllable via `--no-heal` flag):
- Healer Agent analyzes failure traces and error messages
- Attempts to fix common issues (up to `MAX_HEALING_ATTEMPTS` times)
- Uses AI to reason about failures and propose corrections

**Pros**: Significantly improves success rate for generated scripts
**Cons**: Adds execution time; may mask underlying design issues

## External Dependencies

### AI Model Providers

- **Anthropic Claude**: Primary recommended model (`claude-sonnet-4-20250514`)
- **OpenAI GPT-4o**: Alternative model option
- **Google Gemini**: Alternative model option (`gemini-2.0-flash-exp`)

All require API keys configured via environment variables.

### Model Context Protocol (MCP)

- **Playwright MCP Server**: Node.js-based server (`@playwright/mcp` npm package)
- **MCP Python SDK**: Client library for MCP communication (`mcp` package)
- Provides standardized browser automation tool interface

### UI and Output

- **Rich**: Terminal UI library for formatted console output, syntax highlighting, and progress visualization

### Browser Automation

- **Playwright**: (Indirect) The MCP server wraps Playwright, providing browser automation capabilities without direct Python SDK dependency

### Python Standard Library

- `asyncio`: Async/await pattern for MCP communication and agent coordination
- `argparse`: CLI argument parsing
- `json`: Data serialization for traces and tool descriptions
- `pathlib`: Cross-platform filesystem operations