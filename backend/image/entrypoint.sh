#!/bin/bash
set -e

echo "🚀 Starting Computer Use Demo..."

# Start all VNC-related services
echo "📺 Starting VNC services..."
./start_all.sh

# Wait a moment for VNC to stabilize
sleep 2

# Start noVNC web interface
echo "🌐 Starting noVNC web interface..."
./novnc_startup.sh

# Wait for noVNC to be ready
sleep 2

# Start HTTP server on a different port to avoid conflicts
echo "🌍 Starting HTTP server..."
python http_server.py > /tmp/server_logs.txt 2>&1 &

# Wait for core services to be ready
sleep 3

# Start FastAPI backend
echo "⚡ Starting FastAPI backend..."
cd /home/computeruse
python start_fastapi.py > /tmp/fastapi_stdout.log 2>&1 &
tail -f /tmp/fastapi_stdout.log

# Wait for FastAPI to start
sleep 5

echo "✨ Computer Use Demo is ready!"
echo "➡️  Backend API: http://localhost:8501"
echo "➡️  VNC Viewer: http://localhost:8080"
echo "➡️  API Documentation: http://localhost:8501/docs"
echo "➡️  HTTP Server: http://localhost:8081"

tail -f /tmp/fastapi_stdout.log

# Keep the container running
tail -f /dev/null
