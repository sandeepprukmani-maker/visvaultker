# 🎭 Playwright-Inspired Test Agents Guide

## Overview

This application has been enhanced with three AI-powered test agents inspired by Playwright's test agent architecture:

1. **🎭 Planner Agent** - Explores applications and generates human-readable test plans
2. **🎭 Generator Agent** - Converts test plans into executable automation scripts
3. **🎭 Healer Agent** - Runs tests with automatic self-healing capabilities

These agents can work independently or be chained together in an **Agentic Loop** for fully automated test creation and execution.

---

## Architecture

```
┌─────────────────┐
│  🎭 Planner     │ ──────┐
│  Agent          │       │
│                 │       │  Explores app
│  Generates      │       │  Creates test specs
│  Markdown specs │       │
└─────────────────┘       │
                          ▼
                  ┌──────────────┐
                  │   App/URL    │
                  └──────────────┘
                          │
┌─────────────────┐       │
│  🎭 Generator   │ ◄─────┘
│  Agent          │
│                 │  Converts specs to
│  Creates        │  executable plans
│  executable     │  Verifies selectors
│  automation     │
└─────────────────┘
        │
        │  Generated tests
        ▼
┌─────────────────┐
│  🎭 Healer      │
│  Agent          │
│                 │  Executes tests
│  Runs tests +   │  Auto-heals failures
│  Self-healing   │  Iterative repair
└─────────────────┘
```

---

## 🎭 Planner Agent

### Purpose
Explores your application and generates comprehensive, human-readable test plans in Markdown format.

### Features
- Automated web crawling and UI element analysis
- Semantic labeling of interactive elements
- AI-powered scenario planning with GPT-4
- Markdown specification generation
- Support for seed contexts and PRDs

### API Endpoint

```http
POST /agents/plan
```

### Request Body

```json
{
  "url": "https://example.com",
  "scenarios": [
    "User login and authentication",
    "Add item to shopping cart",
    "Complete checkout process"
  ],
  "seed_context": {
    "credentials": {
      "username": "test@example.com",
      "password": "testpass123"
    }
  },
  "prd": "Optional product requirements document text..."
}
```

### Response

```json
{
  "spec_path": "data/specs/example_com_user-login-and-aut_20251101_123456.md",
  "scenarios_count": 3,
  "elements_analyzed": 45,
  "plan_preview": "# Test Plan for https://example.com\n\n## Scenario 1: User Login...",
  "created_at": "2025-11-01T12:34:56"
}
```

### Example cURL

```bash
curl -X POST http://localhost:5000/agents/plan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "scenarios": ["User login", "Password reset"]
  }'
```

---

## 🎭 Generator Agent

### Purpose
Transforms Markdown test specifications into executable automation plans with verified selectors.

### Features
- Parses Markdown specs to extract scenarios and steps
- Generates structured JSON automation plans
- Live selector verification against current page state
- AI-powered selector optimization
- Automatic selector healing suggestions

### API Endpoint

```http
POST /agents/generate
```

### Request Body

```json
{
  "spec_filename": "example_com_user-login-and-aut_20251101_123456.md",
  "seed_url": "https://example.com",
  "verify_selectors": true
}
```

### Response

```json
{
  "test_path": "data/tests/example_com_user-login-and-aut_generated_20251101_130000.json",
  "spec_source": "example_com_user-login-and-aut_20251101_123456.md",
  "scenarios_generated": 3,
  "seed_url": "https://example.com",
  "selector_verification": true,
  "created_at": "2025-11-01T13:00:00",
  "tests": [
    {
      "scenario_name": "User login and authentication",
      "automation_plan": {
        "actions": [
          {
            "action": "navigate",
            "url": "https://example.com/login"
          },
          {
            "action": "fill",
            "selector": "input[name='email']",
            "value": "test@example.com",
            "selector_verified": true
          },
          {
            "action": "click",
            "selector": "button[type='submit']",
            "selector_verified": true
          },
          {
            "action": "expect",
            "selector": ".dashboard",
            "condition": "visible",
            "selector_verified": true
          }
        ]
      },
      "steps_count": 4,
      "verified": true
    }
  ]
}
```

### Example cURL

```bash
curl -X POST http://localhost:5000/agents/generate \
  -H "Content-Type: application/json" \
  -d '{
    "spec_filename": "example_com_user-login_20251101_123456.md",
    "seed_url": "https://example.com",
    "verify_selectors": true
  }'
```

---

## 🎭 Healer Agent

### Purpose
Executes test suites with automatic self-healing for broken selectors and failed tests.

### Features
- Iterative test execution with healing loops
- Intelligent failure analysis (selector vs functional issues)
- Configurable healing attempts and confidence thresholds
- Automatic test skipping for broken functionality
- Comprehensive healing reports

### Guardrails
- **Max Healing Attempts**: Prevents infinite healing loops (default: 3)
- **Confidence Threshold**: Minimum confidence for applying heals (default: 0.75)
- **Functional Failure Detection**: Skips tests with broken functionality vs selector issues

### API Endpoint

```http
POST /agents/heal
```

### Request Body

```json
{
  "test_filename": "example_com_user-login_generated_20251101_130000.json",
  "max_heal_attempts": 3,
  "confidence_threshold": 0.75
}
```

### Response

```json
{
  "test_suite_name": "example_com_user-login_20251101_123456.md",
  "start_time": "2025-11-01T13:05:00",
  "end_time": "2025-11-01T13:07:30",
  "tests": [
    {
      "scenario_name": "User login and authentication",
      "final_status": "healed",
      "healing_applied": true,
      "healed_actions": [
        {
          "action_index": 2,
          "original_selector": "button[type='submit']",
          "healed_selector": "button.login-button",
          "confidence": 0.89
        }
      ],
      "attempts": [
        {
          "attempt": 1,
          "status": "failed",
          "error": "Timeout waiting for selector",
          "failed_action": {"action": "click", "selector": "button[type='submit']"}
        },
        {
          "attempt": 2,
          "status": "success",
          "steps_completed": 4,
          "steps_total": 4
        }
      ]
    }
  ],
  "summary": {
    "total": 3,
    "passed": 1,
    "healed": 2,
    "failed": 0,
    "skipped": 0
  },
  "success_rate": 1.0,
  "report_path": "data/healing_reports/healing_report_20251101_130730.json"
}
```

### Example cURL

```bash
curl -X POST http://localhost:5000/agents/heal \
  -H "Content-Type: application/json" \
  -d '{
    "test_filename": "example_com_generated_20251101_130000.json",
    "max_heal_attempts": 3,
    "confidence_threshold": 0.75
  }'
```

---

## 🎭 Agentic Loop

### Purpose
Chains all three agents together in a single automated pipeline: Plan → Generate → Heal.

### Features
- End-to-end test automation from URL to executed tests
- One API call for complete test coverage
- Automatic error recovery at each stage
- Comprehensive results from all agents

### API Endpoint

```http
POST /agents/loop
```

### Request Body

```json
{
  "url": "https://example.com",
  "scenarios": [
    "User login",
    "Add to cart",
    "Checkout"
  ],
  "seed_context": {
    "user": {
      "email": "test@example.com",
      "password": "testpass123"
    }
  },
  "prd": "Optional PRD text...",
  "max_heal_attempts": 3,
  "confidence_threshold": 0.75
}
```

### Response

```json
{
  "url": "https://example.com",
  "scenarios": ["User login", "Add to cart", "Checkout"],
  "start_time": "2025-11-01T14:00:00",
  "end_time": "2025-11-01T14:15:30",
  "success": true,
  "test_success_rate": 0.95,
  "stages": {
    "planning": {
      "status": "success",
      "result": {
        "spec_path": "data/specs/...",
        "scenarios_count": 3,
        "elements_analyzed": 67
      },
      "timestamp": "2025-11-01T14:02:00"
    },
    "generation": {
      "status": "success",
      "result": {
        "test_path": "data/tests/...",
        "scenarios_generated": 3,
        "selector_verification": true
      },
      "timestamp": "2025-11-01T14:05:00"
    },
    "healing": {
      "status": "success",
      "result": {
        "summary": {
          "total": 3,
          "passed": 2,
          "healed": 1,
          "failed": 0
        },
        "success_rate": 1.0
      },
      "timestamp": "2025-11-01T14:15:30"
    }
  },
  "result_path": "data/loop_results/loop_result_20251101_141530.json"
}
```

### Example cURL

```bash
curl -X POST http://localhost:5000/agents/loop \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "scenarios": ["User login", "Shopping cart flow"]
  }'
```

---

## List and Retrieve Artifacts

### List All Specs

```http
GET /agents/specs
```

Returns list of all generated test specifications.

### List All Tests

```http
GET /agents/tests
```

Returns list of all generated test suites.

### List All Healing Reports

```http
GET /agents/reports
```

Returns list of all healing execution reports.

### Get Specific Spec

```http
GET /agents/specs/{filename}
```

Returns the full Markdown content of a specific test spec.

### Get Specific Test

```http
GET /agents/tests/{filename}
```

Returns the full JSON content of a specific test suite.

---

## Workflow Examples

### Example 1: Generate and Run Tests for E-commerce Checkout

```bash
# Step 1: Generate test plan
curl -X POST http://localhost:5000/agents/plan \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://shop.example.com",
    "scenarios": [
      "Guest checkout with credit card",
      "Registered user checkout with saved address",
      "Apply coupon code during checkout"
    ]
  }' > plan_response.json

# Extract spec filename
SPEC_FILE=$(jq -r '.spec_path | split("/")[-1]' plan_response.json)

# Step 2: Generate executable tests
curl -X POST http://localhost:5000/agents/generate \
  -H "Content-Type: application/json" \
  -d "{
    \"spec_filename\": \"$SPEC_FILE\",
    \"seed_url\": \"https://shop.example.com\",
    \"verify_selectors\": true
  }" > generate_response.json

# Extract test filename
TEST_FILE=$(jq -r '.test_path | split("/")[-1]' generate_response.json)

# Step 3: Run tests with healing
curl -X POST http://localhost:5000/agents/heal \
  -H "Content-Type: application/json" \
  -d "{
    \"test_filename\": \"$TEST_FILE\",
    \"max_heal_attempts\": 5,
    \"confidence_threshold\": 0.80
  }"
```

### Example 2: Full Agentic Loop (One Command)

```bash
curl -X POST http://localhost:5000/agents/loop \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://app.example.com",
    "scenarios": [
      "User signup and email verification",
      "Complete user profile",
      "Upload profile photo"
    ],
    "seed_context": {
      "email_domain": "@test.example.com"
    },
    "max_heal_attempts": 3,
    "confidence_threshold": 0.75
  }' | jq '.'
```

---

## Best Practices

### 1. Scenario Design
- Keep scenarios focused and atomic
- Include both happy path and edge cases
- Provide clear, actionable scenario names
- Group related scenarios together

### 2. Seed Context
- Provide test data that works in your environment
- Include credentials for authenticated flows
- Define any required initial state

### 3. Healing Configuration
- Start with default settings (3 attempts, 0.75 threshold)
- Increase attempts for flaky applications
- Raise threshold for critical production tests
- Monitor healing reports to identify systemic issues

### 4. Selector Verification
- Always enable for new applications
- Use to catch broken selectors early
- Review verification warnings in generator output

### 5. Continuous Testing
- Schedule regular agentic loop runs
- Monitor success rates over time
- Use healing reports to improve application stability

---

## Troubleshooting

### Planner generates incomplete specs
- Increase crawl depth for complex applications
- Provide more detailed scenarios
- Include a comprehensive PRD for context

### Generator creates invalid selectors
- Enable selector verification
- Ensure seed_url is accessible
- Check that page structure hasn't changed

### Healer can't fix failures
- Review healing reports for confidence scores
- Check if failures are functional vs selector issues
- Increase max_heal_attempts for complex pages
- Lower confidence_threshold cautiously

### Agentic loop fails mid-execution
- Check logs for specific stage that failed
- Run stages individually to isolate issue
- Ensure OPENAI_API_KEY is configured
- Verify URL is accessible

---

## Integration with Existing Features

The test agents seamlessly integrate with existing automation capabilities:

- **Crawling**: Planner uses the same crawler for page exploration
- **Embeddings**: All agents leverage semantic similarity for element matching
- **Self-Healing**: Healer enhances existing self-healing with iterative loops
- **Versioning**: Test specs and results are versioned for rollback
- **Metrics**: All agent activities are tracked in metrics dashboard

---

## Performance Considerations

- **Planner**: 10-30 seconds per scenario (depends on crawl depth)
- **Generator**: 5-15 seconds per scenario (with selector verification)
- **Healer**: 30s-5min per test (depends on test complexity and healing needs)
- **Full Loop**: 1-10 minutes (varies by application complexity and scenario count)

Costs are optimized with:
- Embedding caching (60-80% cost reduction)
- Rate limiting (prevents API abuse)
- Async operations (improved throughput)

---

## Comparison to Playwright Test Agents

| Feature | Playwright | This Implementation |
|---------|-----------|-------------------|
| Planner | ✅ Explores and plans | ✅ Enhanced with semantic analysis |
| Generator | ✅ Generates Playwright tests | ✅ Generates JSON automation plans |
| Healer | ✅ Repairs test code | ✅ Repairs + execution monitoring |
| Selector Verification | ✅ Live verification | ✅ Live + semantic matching |
| Self-Healing | ✅ Code repairs | ✅ Runtime + iterative loops |
| Output Format | TypeScript/JS tests | Markdown specs + JSON automation |
| Integration | VS Code / Claude Code | REST API |

---

## What's Next?

Enhance your test automation further with:

1. **Schedule automated test runs** using `/schedule` endpoint
2. **Monitor test health** with `/metrics/dashboard`
3. **Version control** test specs for change tracking
4. **Custom seed tests** for complex initialization flows
5. **PRD-driven planning** for requirements traceability

---

For more information, see:
- Main API documentation: `replit.md`
- Original features: `PHASES_1-9_COMPLETE.md` and `PHASES_10-14_COMPLETE.md`
- Example usage: `EXAMPLE_USAGE.md`
