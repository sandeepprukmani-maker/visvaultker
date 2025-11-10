#!/bin/bash

# Start Node.js server only (no database or caching)
echo "Starting VisionVault automation server on port 5000..."
NODE_ENV=development npm run dev
