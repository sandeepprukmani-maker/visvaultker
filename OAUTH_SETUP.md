# OAuth Integration Setup

This project includes TypeScript OAuth integration for connecting to your organization's custom AI models through an OpenAI-compatible gateway.

## Required Environment Variables

The following environment variables must be configured in Replit's Secrets manager:

1. **OAUTH_TOKEN_URL** - The OAuth token endpoint URL provided by your organization
2. **OAUTH_CLIENT_ID** - Your OAuth client ID
3. **OAUTH_CLIENT_SECRET** - Your OAuth client secret
4. **OAUTH_GRANT_TYPE** - Usually `client_credentials`
5. **OAUTH_SCOPE** - The required OAuth scope
6. **GW_BASE_URL** - The AI gateway base URL (OpenAI-compatible endpoint)
7. **CA_CERT_PATH** (Optional) - Path to your CA certificate PEM file if using custom SSL certificates

## How to Add Secrets in Replit

1. Click on the "Tools" button in the left sidebar
2. Select "Secrets"
3. Add each environment variable with its corresponding value
4. The secrets will be automatically available to your application

## Custom SSL Certificates (PEM Files)

If your organization uses custom CA certificates for HTTPS connections:

### Step 1: Upload your PEM file

1. Upload your certificate file (e.g., `ca-certificate.pem`) to the project root or a `certs/` directory
2. The file should contain your organization's CA certificate in PEM format

### Step 2: Add CA_CERT_PATH to Secrets

Add the full path to your certificate in Replit Secrets:
- **Key**: `CA_CERT_PATH`
- **Value**: `/home/runner/YourProjectName/ca-certificate.pem` (adjust path as needed)

**Example paths:**
- Root directory: `/home/runner/YourProjectName/ca-certificate.pem`
- Certs folder: `/home/runner/YourProjectName/certs/ca-certificate.pem`

The OAuth client will automatically use this certificate for all HTTPS connections to your organization's services.

## Usage in Code

### Option 1: Direct AI Chat Requests

For simple AI chat requests without browser automation:

```typescript
import { sendChatRequest } from './lib/ai-client';

// Send a chat request to your custom AI model
const messages = [
  { role: 'user', content: 'What is the weather today?' }
];

const response = await sendChatRequest(messages, 'gpt-4');
console.log(response.choices[0].message.content);
```

### Option 2: Stagehand Browser Automation (Recommended)

For browser automation using your custom AI models with Stagehand:

```typescript
import { Stagehand } from '@browserbasehq/stagehand';
import { createStagehandLLMClient } from './lib/ai-client';

// Create the LLM client with your OAuth credentials
const llmClient = await createStagehandLLMClient('gpt-4');

// Initialize Stagehand with your custom AI model
const stagehand = new Stagehand({
  env: "LOCAL",
  llmClient: llmClient,
  localBrowserLaunchOptions: {
    headless: false,
  },
});

await stagehand.init();
const page = stagehand.context.pages()[0];

// Now Stagehand will use your custom AI models for all operations
await page.goto('https://example.com');
await stagehand.act('Click the login button');
await stagehand.close();
```

## How It Works

1. **Token Caching**: The OAuth token is automatically cached and refreshed before expiration
2. **Auto-Refresh**: Tokens are refreshed 5 minutes before they expire (configurable)
3. **OpenAI Compatible**: Uses the OpenAI SDK to communicate with your custom gateway

## Files

- `server/lib/oauth.ts` - OAuth configuration and token fetcher
- `server/lib/ai-client.ts` - AI client wrapper for making requests
- `.env.example` - Example environment variables

## Integration with Automation Routes

To use your custom AI models in the existing VisionVault automation:

1. **Import the function**: `import { createStagehandLLMClient } from './lib/ai-client'`
2. **Create the client**: `const llmClient = await createStagehandLLMClient(modelName)`
3. **Pass to Stagehand**: Use `llmClient` instead of the `model` parameter

Example integration in `server/routes.ts`:

```typescript
// Instead of:
const stagehand = new Stagehand({
  env: "LOCAL",
  model: "gpt-4o", // Default OpenAI
});

// Use:
const llmClient = await createStagehandLLMClient("gpt-4");
const stagehand = new Stagehand({
  env: "LOCAL",
  llmClient: llmClient, // Your custom OAuth model
});
```

See `server/examples/custom-ai-automation.ts` for complete working examples.

## Next Steps

1. Add your OAuth credentials to Replit Secrets
2. Test the connection: Visit `/api/test-oauth`
3. Use `createStagehandLLMClient()` in your automation routes
4. All browser automations will now use your organization's AI models!
