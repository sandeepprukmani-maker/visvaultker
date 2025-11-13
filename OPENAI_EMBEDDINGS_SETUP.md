# OpenAI Embeddings Setup Guide

This application uses **OpenAI text embeddings** for semantic caching of automation requests, powered by your custom OAuth-based LLM client.

## Configuration

### Required Environment Variables

Add these to your `.env` file or Replit Secrets:

```bash
# OpenAI Embedding Configuration
OPENAI_EMBEDDING_ENDPOINT=https://api.openai.com/v1/embeddings
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Custom LLM Configuration (for chat completions)
CUSTOM_LLM_API_ENDPOINT=https://your-llm-endpoint.com/v1/chat/completions
CUSTOM_LLM_MODEL_NAME=gpt-4o-1-2025-04-14-eastus-dz

# Python API (for database operations)
PYTHON_API_URL=http://localhost:8000
```

### OAuth Token Authentication

Both the embedding API and chat completion API use OAuth tokens fetched via `fetch_token.py`.

**Edit `fetch_token.py`** to implement your token fetching logic:

```python
def fetch_token():
    # Option 1: Fetch from Azure OAuth endpoint
    # import requests
    # response = requests.post("https://login.microsoftonline.com/...", ...)
    
    # Option 2: Use environment variable (development only)
    token = os.getenv("CUSTOM_LLM_API_KEY", "")
    
    if not token:
        return {"error": "No token available"}
    
    return {
        "access_token": token,
        "expires_in": 3600  # Optional: token expiration in seconds
    }
```

## Embedding Models

### OpenAI Text Embedding Models

| Model | Dimensions | Use Case |
|-------|-----------|----------|
| **text-embedding-3-small** | 1536 | Default - Fast, cost-effective |
| **text-embedding-3-large** | 3072 | Higher accuracy, more expensive |
| **text-embedding-ada-002** | 1536 | Legacy model |

**Current Configuration:** `text-embedding-3-small` with **1536 dimensions**

## How Semantic Caching Works

1. **User submits automation request** with a natural language prompt
2. **System generates embedding** (1536-dimensional vector) of the prompt using OpenAI
3. **Similarity search** finds previously cached automations with similar prompts
4. **Cache hit** (similarity ≥ 85%): Returns cached results instantly
5. **Cache miss**: Executes automation and stores with embedding for future use

### Example

```
User 1: "Go to Amazon and search for laptops"
→ Generates embedding → Executes automation → Caches result

User 2: "Navigate to Amazon.com and look for laptop computers"
→ Generates embedding → Finds similar cached request (92% match)
→ Returns cached results instantly ✨
```

## Database Schema

The `automation_history` table stores:
- `prompt`: Original user prompt
- `prompt_embedding`: 1536-dimensional vector (pgvector)
- `generated_code`: Automation code snippets
- `logs`, `screenshot`, and other metadata

Vector similarity search uses PostgreSQL's `pgvector` extension.

## Testing

To test semantic caching:

1. Submit an automation request
2. Check logs for: `"Saved automation with embedding (1536 dimensions)"`
3. Submit a similar request with different wording
4. Look for: `"Found similar automation with similarity: 0.XX"`

## Troubleshooting

### "No embedding generated"
- Check `fetch_token.py` returns valid OAuth token
- Verify `OPENAI_EMBEDDING_ENDPOINT` is accessible
- Check Python API is running on `PYTHON_API_URL`

### "OAuth token is invalid or missing"
- Ensure `fetch_token.py` returns `{"access_token": "...", "expires_in": 3600}`
- Test manually: `python fetch_token.py`

### Schema mismatch errors
If you see dimension errors, run:
```bash
npm run db:push --force
```

This syncs the schema with 1536 dimensions for OpenAI embeddings.
