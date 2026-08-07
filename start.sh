#!/usr/bin/env bash
# Start script for Render.com

set -o errexit

# Get port from environment or default to 8000
PORT="${PORT:-8000}"

echo "🚀 Starting application on port $PORT..."

# Start uvicorn
exec uvicorn backend.app:app --host 0.0.0.0 --port "$PORT" --workers 1
