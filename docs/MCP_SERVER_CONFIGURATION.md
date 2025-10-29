# Playwright MCP Server Configuration

## Overview

The Playwright MCP (Model Context Protocol) server can run in two modes to optimize for your specific needs:

- **`always_run`** - Keeps the server running persistently (default)
- **`on_demand`** - Starts the server only when needed

## Configuration

Edit `config/config.ini` and find the `[playwright_mcp]` section:

```ini
[playwright_mcp]
# Playwright MCP Server Mode
# Options:
#   always_run - Keep MCP server running continuously (faster response, uses more resources)
#   on_demand - Start MCP server only when needed (saves resources, slower first request)
server_mode = always_run
# Timeout for on-demand server startup (seconds)
startup_timeout = 30
```

## Mode Comparison

| Feature | always_run (Default) | on_demand |
|---------|---------------------|-----------|
| **First Request Speed** | ⚡ Fast | 🐌 Slower (server startup) |
| **Subsequent Requests** | ⚡ Fast | ⚡ Fast |
| **Memory Usage** | 📈 Higher | 📉 Lower |
| **CPU Usage (Idle)** | 🔄 Background process | 💤 None |
| **Best For** | Production, frequent use | Development, occasional use |

## When to Use Each Mode

### Use `always_run` when:
- You're running in production
- You make frequent automation requests
- Response time is critical
- You have sufficient system resources

### Use `on_demand` when:
- You're developing/testing
- You make infrequent automation requests
- You want to minimize resource usage
- You're running on resource-constrained systems

## API Endpoints

### Check Server Status
```bash
GET /api/mcp/status

# Response:
{
  "success": true,
  "server_mode": "always_run",
  "persistent_running": true,
  "message": "MCP server in 'always_run' mode"
}
```

### Restart Server (always_run mode only)
```bash
POST /api/mcp/restart
X-API-Key: your-api-key

# Response:
{
  "success": true,
  "message": "MCP server shutdown. It will restart on next request."
}
```

### Health Check (includes MCP status)
```bash
GET /health

# Response:
{
  "status": "healthy",
  "engines": {
    "browser_use": "available",
    "playwright_mcp": "available"
  },
  "mcp_server": {
    "mode": "always_run",
    "running": true
  },
  "message": "AI browser automation ready",
  ...
}
```

## How It Works

### Always Run Mode
1. Server starts when first Playwright MCP request is made
2. Server stays running in the background
3. All subsequent requests reuse the same server instance
4. Server automatically restarts if it crashes
5. Server shuts down gracefully when app exits

### On Demand Mode
1. Server starts fresh for each request
2. Server shuts down after request completes
3. Next request starts a new server instance
4. No persistent background process

## Implementation Details

- **Server Manager**: Singleton pattern ensures only one persistent server
- **Thread Safety**: Lock-based synchronization for concurrent requests
- **Auto-Cleanup**: `atexit` handler ensures proper shutdown
- **Health Checks**: Automatic process monitoring and restart
- **Logging**: Clear status messages for server lifecycle events

## Troubleshooting

### Server Won't Start
- Check logs for startup errors
- Verify Node.js is installed
- Ensure Playwright browsers are installed
- Check `startup_timeout` setting

### Server Keeps Restarting
- Check system resources (memory, CPU)
- Review application logs for crashes
- Consider switching to `on_demand` mode

### Slow Performance in always_run
- Check if server is actually running: `GET /api/mcp/status`
- Try restarting: `POST /api/mcp/restart`
- Review server logs for errors

### High Memory Usage
- Switch to `on_demand` mode to save resources
- Adjust `startup_timeout` if needed
- Monitor with `GET /api/mcp/status`

## Example Configuration Changes

### Switch to On-Demand Mode
```ini
[playwright_mcp]
server_mode = on_demand
startup_timeout = 30
```

### Switch to Always-Run Mode
```ini
[playwright_mcp]
server_mode = always_run
startup_timeout = 30
```

After changing the configuration, restart your application for changes to take effect.
