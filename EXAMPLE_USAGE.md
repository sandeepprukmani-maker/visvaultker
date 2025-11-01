# Example Usage Guide

## Getting Started

### 1. Set Your OpenAI API Key

The system requires an OpenAI API key to function. You can set it as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:
```
OPENAI_API_KEY=your-api-key-here
```

### 2. Access the API

The FastAPI server is running at `http://localhost:5000` (or your Replit URL).

Visit the root endpoint for API documentation:
```
GET /
```

## Example Workflows

### Example 1: Crawl a Website

Crawl and analyze a website to extract its structure:

```bash
curl -X POST http://localhost:5000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "depth": 1
  }'
```

Response:
```json
{
  "status": "success",
  "pages_crawled": 1,
  "unique_templates": 1,
  "results": [
    {
      "url": "https://example.com",
      "template_id": "template_abc123def456",
      "structure_hash": "sha256hash...",
      "screenshot": "./data/screenshots/page_abc123_20231101_120000.png",
      "elements_count": 45,
      "semantic_label": {
        "page_type": "landing page",
        "purpose": "Company homepage",
        "key_components": [...]
      }
    }
  ]
}
```

### Example 2: Search for UI Elements

Search for specific UI elements using natural language:

```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "login button",
    "top_k": 5
  }'
```

Response:
```json
{
  "query": "login button",
  "results_count": 5,
  "results": [
    {
      "selector": "body > header > nav > button#login",
      "description": "button element with role 'button' labeled 'Sign In'",
      "similarity": 0.92,
      "element": {
        "tag": "button",
        "id": "login",
        "text": "Sign In",
        ...
      }
    }
  ]
}
```

### Example 3: Run Automation from Natural Language

Create and execute an automation plan:

```bash
curl -X POST http://localhost:5000/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Click the login button and navigate to the dashboard",
    "start_url": "https://example.com",
    "context_limit": 10
  }'
```

Response:
```json
{
  "status": "success",
  "task": "Click the login button and navigate to the dashboard",
  "context_items": 5,
  "plan_steps": 3,
  "plan": [
    {
      "step": 1,
      "action_type": "navigate",
      "selector": "",
      "value": "https://example.com",
      "description": "Navigate to the homepage"
    },
    {
      "step": 2,
      "action_type": "click",
      "selector": "button#login",
      "value": "",
      "description": "Click the login button"
    }
  ],
  "execution": {
    "status": "success",
    "steps_completed": 3,
    "steps_failed": 0,
    "logs": [...],
    "screenshots": [...]
  }
}
```

### Example 4: View Discovered Templates

See all unique page templates that have been discovered:

```bash
curl http://localhost:5000/templates
```

Response:
```json
{
  "total_templates": 3,
  "templates": [
    {
      "template_id": "template_abc123def456",
      "match_count": 5,
      "urls": [
        "https://example.com",
        "https://example.com/about",
        ...
      ]
    }
  ]
}
```

## Python Usage Example

```python
import requests

API_URL = "http://localhost:5000"

# 1. Crawl a website
response = requests.post(f"{API_URL}/crawl", json={
    "url": "https://example.com",
    "depth": 1
})
crawl_results = response.json()
print(f"Crawled {crawl_results['pages_crawled']} pages")

# 2. Search for elements
response = requests.post(f"{API_URL}/search", json={
    "query": "submit button",
    "top_k": 5
})
search_results = response.json()
print(f"Found {len(search_results['results'])} matching elements")

# 3. Run automation
response = requests.post(f"{API_URL}/run", json={
    "task": "Fill out the contact form and submit",
    "start_url": "https://example.com/contact",
    "context_limit": 10
})
automation_results = response.json()
print(f"Automation status: {automation_results['status']}")
print(f"Steps completed: {automation_results['execution']['steps_completed']}")
```

## Interactive API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

## Tips

1. **Start Small**: Begin by crawling a simple page to understand the structure
2. **Build Context**: Crawl multiple pages to build up the vector database
3. **Natural Language**: Use descriptive natural language for search and automation tasks
4. **Check Screenshots**: The system saves screenshots at each step for debugging
5. **Monitor Logs**: Check the FastAPI server logs for detailed execution information
