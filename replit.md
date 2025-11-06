# Playwright MCP Automation Script Generator

## Overview

This project converts natural language descriptions into executable Python Playwright automation scripts. It uses a multi-agent AI system (supporting Claude, GPT-4o, or Gemini) to perform live browser automation, observe the interactions, and then generate reusable Python scripts from those execution traces. The system includes optional self-healing capabilities to fix failing scripts automatically.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Multi-Agent Design Pattern

**Problem**: Converting natural language to reliable, reusable browser automation requires both understanding user intent and generating correct code.

**Solution**: Three specialized agents with distinct responsibilities:
- **Executor Agent**: Performs live browser automation using Playwright MCP tools, creating an execution trace
- **Code Generator Agent**: Transforms execution traces into standalone, rerunnable Python scripts
- **Healer Agent**: Analyzes script failures and automatically fixes issues (optional, enabled by default)

**Rationale**: This separation allows the system to learn from actual browser interactions rather than blindly generating code. The Executor Agent explores the real browser environment, the Code Generator Agent codifies those successful interactions, and the Healer Agent provides robustness through automatic error recovery.

**Pros**: More reliable script generation based on actual browser behavior; clear separation of concerns
**Cons**: Additional complexity compared to direct code generation; requires live browser execution

### Multi-Provider AI Model Support

**Problem**: Different users have access to different AI providers (Anthropic, OpenAI, Google), each with distinct APIs and capabilities.

**Solution**: Unified model abstraction layer in `config.py` with a `ModelType` literal type and standardized configuration dictionary. Each agent dynamically initializes the appropriate client based on model selection.

**Implementation**:
- Standardized model configuration with API keys, model names, and display names
- Provider-specific client initialization within agent constructors
- Graceful degradation for optional dependencies (Gemini SDK)

**Alternatives Considered**: LangChain or similar abstraction frameworks, but opted for direct SDK usage for simplicity and fine-grained control.

### MCP (Model Context Protocol) Integration

**Problem**: AI agents need a standardized way to control browser automation tools.

**Solution**: Custom `PlaywrightMCPClient` wrapper that:
- Manages stdio-based communication with the Playwright MCP server (Node.js process)
- Exposes browser automation capabilities (navigate, click, fill, screenshot, evaluate) as structured tool descriptions
- Handles tool execution requests and formats results for AI consumption

**Architecture Decision**: The MCP server runs as an external Node.js process (`npx @playwright/mcp`) communicating via stdio. This keeps the Python codebase lightweight while leveraging the official Playwright MCP implementation.

**Pros**: Standard protocol for tool usage; separation of concerns between Python agents and browser automation
**Cons**: Requires Node.js runtime; adds process management complexity

### Execution Trace System

**Problem**: Need to capture and replay browser automation sequences reliably.

**Solution**: The Executor Agent maintains an execution trace (list of dictionaries) recording each action, tool used, parameters, and results. This trace serves as the input for the Code Generator Agent.

**Rationale**: Traces provide a structured, complete record of successful automation sequences, making code generation more accurate than trying to generate code directly from natural language.

### File Organization and Output Management

**Problem**: Generated scripts and execution traces need organized storage.

**Solution**: 
- `OUTPUT_DIR` (default: "generated_scripts"): Stores generated Python Playwright scripts
- `TRACE_DIR` (default: "traces"): Stores JSON execution traces
- Auto-generated filenames or user-specified output paths via CLI

**Design Decision**: Separate directories for scripts vs. traces allows easy inspection of both the final output and the intermediate execution history.

## External Dependencies

### AI Model APIs

- **Anthropic Claude API**: Primary recommended model (Claude 4 Sonnet), accessed via `anthropic` Python SDK
- **OpenAI API**: GPT-4o support via `openai` Python SDK  
- **Google Gemini API**: Gemini 2.0 Flash support via `google-generativeai` SDK (optional dependency)

Configuration: API keys provided via environment variables (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`)

### Browser Automation Stack

- **Playwright**: Python browser automation library (v1.55.0)
- **Playwright MCP Server**: Node.js package (`@playwright/mcp`) that exposes Playwright functionality via Model Context Protocol
- **Chromium Browser**: Playwright-managed browser for automation execution

Installation requires both Python package (`playwright`) and system browser (`playwright install chromium`)

### Model Context Protocol (MCP)

- **MCP Python SDK**: Client library (v1.20.0) for communicating with MCP servers via stdio
- Protocol enables standardized AI-to-tool communication

### User Interface

- **Rich**: Terminal UI library for formatted console output, syntax highlighting, and progress display

### Runtime Requirements

- **Python 3.11+**: Required for modern type hints and async features
- **Node.js 20+**: Required for Playwright MCP server execution