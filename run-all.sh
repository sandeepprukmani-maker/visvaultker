#!/bin/bash

echo "=== Starting AutomateAI Platform ==="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "Starting Python FastAPI backend on port 8000..."
cd python_backend
python3 main.py &
PYTHON_PID=$!
cd "$PROJECT_ROOT"

sleep 3

echo "Starting Express + Vite server on port 5000..."
npm run dev &
NODE_PID=$!

echo "=== Both servers started ==="
echo "Python backend (FastAPI): http://localhost:8000"
echo "Frontend (Vite + Express): http://localhost:5000"
echo "Press Ctrl+C to stop all servers"

trap "kill $PYTHON_PID $NODE_PID 2>/dev/null" EXIT

wait
