# OAuth Gen AI Gateway Setup Guide

This tool now supports **OAuth-based authentication through Gen AI Gateway**, providing enterprise-grade security and centralized API key management.

## Authentication Options

You have **two options** for authentication:

### Option 1: OAuth Gen AI Gateway (Recommended for Enterprise)
✅ **Advantages:**
- Centralized authentication and API key management
- Token rotation and refresh handled automatically
- Enterprise security compliance
- No need to manage individual LLM API keys
- Unified access to multiple LLM providers

### Option 2: Direct API Keys (Simple Setup)
✅ **Advantages:**
- Quick setup for personal projects
- Direct connection to LLM providers
- No gateway infrastructure needed

## Setup Instructions

### Option 1: Using OAuth Gen AI Gateway

#### Step 1: Install Dependencies

```bash
pip install python-dotenv genai-gateway-tools tbc-security
```

**Note:** `genai-gateway-tools` and `tbc-security` are internal libraries. If you don't have access, contact your IT team or use Option 2 (Direct API Keys).

#### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Enable OAuth Gateway
USE_OAUTH_GATEWAY=true

# OAuth Configuration
OAUTH_TOKEN_URL=https://your-oauth-server.com/oauth/token
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_GRANT_TYPE=client_credentials
OAUTH_SCOPE=your-required-scope

# Gateway Base URL
GW_BASE_URL=https://your-gen-ai-gateway.com/v1
```

#### Step 3: Verify Configuration

Run the tool with help to verify setup:

```bash
python main.py --help
```

You should see: `Using OAuth Gen AI Gateway for Claude 4 Sonnet via Gateway`

### Option 2: Using Direct API Keys

#### Step 1: Disable OAuth Gateway

Create a `.env` file:

```bash
# Disable OAuth Gateway
USE_OAUTH_GATEWAY=false

# Add your API keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
# OR
OPENAI_API_KEY=sk-xxxxx
# OR
GEMINI_API_KEY=xxxxx
```

#### Step 2: Verify

```bash
python main.py --help
```

## Available Models

### With OAuth Gateway (`USE_OAUTH_GATEWAY=true`):

```bash
python main.py "your task" --model claude
# Uses: ms.anthropic.claude-sonnet-4-5-20250929-v1:0

python main.py "your task" --model gpt4o
# Uses: ms.openai.gpt-4o

python main.py "your task" --model gemini
# Uses: ms.google.gemini-2.0-flash-exp
```

### With Direct API Keys (`USE_OAUTH_GATEWAY=false`):

```bash
python main.py "your task" --model claude
# Uses: claude-sonnet-4-20250514

python main.py "your task" --model gpt4o
# Uses: gpt-4o

python main.py "your task" --model gemini
# Uses: gemini-2.0-flash-exp
```

## How It Works

### OAuth Gateway Flow:

```
1. Tool starts
   ↓
2. Loads OAuth config from .env
   ↓
3. Fetches OAuth token using client credentials
   ↓
4. Initializes OpenAI client with gateway base URL
   ↓
5. All LLM calls go through gateway with OAuth token
   ↓
6. Gateway routes to appropriate LLM provider
   ↓
7. Token refresh handled automatically
```

### Direct API Flow:

```
1. Tool starts
   ↓
2. Loads API keys from .env
   ↓
3. Initializes provider-specific clients
   ↓
4. Direct calls to LLM APIs
```

## Troubleshooting

### OAuth Gateway Issues

**Error: "Missing required environment variables"**
```
Solution: Verify all OAuth variables are set in .env:
- OAUTH_TOKEN_URL
- OAUTH_CLIENT_ID
- OAUTH_CLIENT_SECRET
- OAUTH_GRANT_TYPE
- OAUTH_SCOPE
- GW_BASE_URL
```

**Error: "OAuth dependencies not available"**
```
Solution: Install required packages:
pip install genai-gateway-tools tbc-security

If these packages aren't available, switch to direct API keys:
USE_OAUTH_GATEWAY=false
```

**Error: "Attempt 1 failed: Unauthorized"**
```
Solution: 
1. Verify OAuth credentials are correct
2. Check that client has required scopes
3. Confirm gateway URL is accessible
```

### Direct API Key Issues

**Error: "API key not found"**
```
Solution: Set the appropriate API key in .env:
ANTHROPIC_API_KEY=your-key  # For Claude
OPENAI_API_KEY=your-key     # For GPT-4
GEMINI_API_KEY=your-key     # For Gemini
```

## Security Best Practices

### For OAuth Gateway:
✅ Store credentials in `.env` (already in .gitignore)
✅ Never commit `.env` to version control
✅ Use environment-specific credentials (dev/prod)
✅ Rotate OAuth secrets regularly
✅ Limit scope to minimum required permissions

### For Direct API Keys:
✅ Store keys in `.env` (already in .gitignore)
✅ Never hardcode API keys in code
✅ Use separate keys for dev/prod
✅ Monitor API usage regularly
✅ Rotate keys periodically

## Example .env Files

### Enterprise Setup (OAuth Gateway):
```bash
USE_OAUTH_GATEWAY=true
OAUTH_TOKEN_URL=https://auth.company.com/oauth/token
OAUTH_CLIENT_ID=playwright-automation-client
OAUTH_CLIENT_SECRET=super-secret-value
OAUTH_GRANT_TYPE=client_credentials
OAUTH_SCOPE=genai:read genai:write
GW_BASE_URL=https://genai-gateway.company.com/v1
```

### Personal/Development Setup (Direct Keys):
```bash
USE_OAUTH_GATEWAY=false
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

## Migration Between Options

### Switching from Direct Keys → OAuth Gateway:

1. Install OAuth dependencies:
   ```bash
   pip install genai-gateway-tools tbc-security
   ```

2. Update `.env`:
   ```bash
   USE_OAUTH_GATEWAY=true
   # Add OAuth variables
   # Keep API keys commented out as backup
   ```

3. Test:
   ```bash
   python main.py --help
   ```

### Switching from OAuth Gateway → Direct Keys:

1. Update `.env`:
   ```bash
   USE_OAUTH_GATEWAY=false
   ANTHROPIC_API_KEY=your-key
   ```

2. Comment out OAuth variables:
   ```bash
   # OAUTH_TOKEN_URL=...
   # OAUTH_CLIENT_ID=...
   # etc.
   ```

## Support

- OAuth Gateway issues: Contact your IT/DevOps team
- Direct API key issues: Contact LLM provider support
- Tool issues: Check existing GitHub issues or create new one
