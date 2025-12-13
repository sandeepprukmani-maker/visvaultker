# AI Phone Caller Application

## Overview
A Python Streamlit web application that triggers AI phone calls using Bland AI with a self-improving knowledge base. The system:
- Accepts a phone number and website URL as input
- Scrapes the website content to build a knowledge base
- Initiates AI-powered phone calls via Bland AI
- Transcribes both sides of conversations
- Adds transcripts to the knowledge base for future calls

## Project Structure
```
├── app.py                    # Main Streamlit application
├── .streamlit/
│   └── config.toml          # Streamlit server configuration
├── pyproject.toml           # Python dependencies
└── replit.md                # Project documentation
```

## Key Features
1. **Website Scraping** - Uses trafilatura to extract text content from any URL
2. **Bland AI Integration** - Initiates outbound calls with custom prompts
3. **Dynamic Knowledge Base** - Combines website content with call transcripts
4. **Call History** - Tracks all calls with timestamps and status
5. **Transcript Retrieval** - Fetches and stores conversation transcripts

## How to Use
1. Enter your Bland AI API key in the sidebar (or set BLAND_AI_API_KEY environment variable)
2. Navigate to "Make a Call" tab
3. Enter the phone number to call (with country code, e.g., +1234567890)
4. Enter the website URL to use as knowledge base
5. Click "Start Call"
6. After the call completes, fetch the transcript from "Call History" tab

## API Requirements
- **Bland AI API Key** - Get from https://app.bland.ai/dashboard/settings
- The API key can be entered in the sidebar or stored as `BLAND_AI_API_KEY` secret

## Technical Notes
- Server runs on port 5000 (Streamlit)
- Session state is used for in-memory storage of call history and knowledge base
- Transcripts are deduplicated to prevent adding the same conversation twice
- Website content is cached in the knowledge base for reuse

## Recent Changes
- December 2024: Initial implementation with full Bland AI integration
- Added duplicate transcript prevention
- Fallback message saved when website scraping fails
