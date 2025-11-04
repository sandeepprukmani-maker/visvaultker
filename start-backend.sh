#!/bin/bash

echo "Starting Python FastAPI backend..."
cd python_backend && python3 main.py &
PYTHON_PID=$!

echo "Python backend started with PID $PYTHON_PID"
echo "Python backend running at http://localhost:8000"

wait $PYTHON_PID
