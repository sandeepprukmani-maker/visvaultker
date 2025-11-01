"""
Windows-compatible server startup script
Use this to start the server on Windows to avoid asyncio issues.
"""
import sys
import asyncio

# Apply Windows fix FIRST, before any other imports
if sys.platform == 'win32':
    print("Applying Windows compatibility fix for Playwright...")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    print("✓ Windows fix applied!")

# Now import uvicorn and start the server
import uvicorn

if __name__ == "__main__":
    print("\nStarting AI Automation Engine server...")
    print("Access the web UI at: http://localhost:5000\n")

    uvicorn.run(
        "src.api.main:app",
        port=5000,
        reload=True
    )
