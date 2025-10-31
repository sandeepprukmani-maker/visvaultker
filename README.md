# Jira++ Application

A Flask-based application demonstrating OAuth authentication with OpenAI API for generating acceptance criteria.

## Features

- Generate acceptance criteria using OpenAI
- Support for both direct API key and OAuth authentication
- Simple web-based interface
- Test endpoint to verify OAuth configuration

## Setup

### 1. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

#### Required Settings:

- `SESSION_SECRET`: A random secret key for Flask sessions
- `USE_OAUTH_FOR_OPENAI`: Set to `true` for OAuth mode, `false` for direct API key

#### For Direct API Key Mode (USE_OAUTH_FOR_OPENAI=false):

- `OPENAI_API_KEY`: Your OpenAI API key from https://platform.openai.com/api-keys

#### For OAuth Mode (USE_OAUTH_FOR_OPENAI=true):

- `OAUTH_TOKEN_URL`: OAuth token endpoint URL
- `OAUTH_CLIENT_ID`: Your OAuth client ID
- `OAUTH_CLIENT_SECRET`: Your OAuth client secret
- `OAUTH_GRANT_TYPE`: Usually `client_credentials`
- `OAUTH_SCOPE`: Required scopes (e.g., `openai.api.read openai.api.write`)
- `GPT_BASE_URL`: (Optional) Custom OpenAI gateway URL

### 2. Running the Application

The application is configured to run automatically with:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

Access the application at the provided Replit URL.

## Authentication Modes

### Direct API Key (Recommended for most users)

This is the simplest method. Just get an API key from OpenAI and add it to your `.env` file:

```
USE_OAUTH_FOR_OPENAI=false
OPENAI_API_KEY=sk-your-key-here
```

### OAuth (For enterprise users)

If your organization uses an OAuth gateway for OpenAI access:

```
USE_OAUTH_FOR_OPENAI=true
OAUTH_TOKEN_URL=https://your-auth-server.com/oauth/token
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_GRANT_TYPE=client_credentials
OAUTH_SCOPE=openai.api.read openai.api.write
```

The application will automatically:
- Fetch OAuth tokens from your token endpoint
- Refresh tokens before they expire
- Retry failed requests

## Project Structure

```
.
├── app.py                      # Main Flask application  
├── main.py                     # Application entry point
├── services/
│   ├── ai_service.py          # OpenAI integration with OAuth support
│   ├── oauth_config.py        # OAuth configuration classes
│   └── openai_oauth.py        # Standalone OAuth client
├── templates/                  # HTML templates
├── static/                     # Static assets (CSS, JS, images)
└── .env.example               # Example environment configuration
```

## API Endpoints

### Test OAuth Configuration
```
GET /api/test-oauth
```
Returns the current OAuth configuration status.

### Generate Acceptance Criteria
```
GET /api/epic/<epic_id>
```
Generate acceptance criteria for a demo EPIC using OpenAI.

## Development

### Environment Variables in Replit

When deployed on Replit, you can also set environment variables through:
1. The Secrets tab (for sensitive values like API keys)
2. The `.env` file (for configuration values)

Replit Secrets take precedence over `.env` file values.

## License

Proprietary
