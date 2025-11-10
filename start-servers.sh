#!/bin/bash

# Start Python API server in background
echo "Starting Python API server on port 8000..."
.pythonlibs/bin/python -m uvicorn server.main:app --host localhost --port 8000 --reload &
PYTHON_PID=$!

# Wait a bit for Python server to start
sleep 2

# Start Node.js server (foreground - this is the main process)
echo "Starting Node.js server on port 5000..."
NODE_ENV=development npm run dev

# If Node.js exits, kill Python server
kill $PYTHON_PID
