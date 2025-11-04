#!/usr/bin/env python3
"""
Start the Python backend server
"""

import uvicorn
from backend.database import init_db

if __name__ == "__main__":
    # Initialize database tables
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    
    # Start FastAPI server
    print("Starting FastAPI server on http://0.0.0.0:8000")
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
