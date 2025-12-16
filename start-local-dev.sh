#!/bin/bash

# Start Local Development Environment
# This script starts both the mock API server and the frontend dev server

set -e

echo "🚀 Starting Local Development Environment"
echo "========================================"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start mock API server in background
echo "🔧 Starting mock API server on http://localhost:8000..."
node mock-api-server.js &
API_PID=$!

# Wait a moment for API server to start
sleep 2

# Check if API server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Failed to start mock API server"
    cleanup
    exit 1
fi

echo "✅ Mock API server started successfully"

# Start frontend dev server in background
echo "🎨 Starting frontend dev server on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend server to start
sleep 3

echo ""
echo "🎉 Development environment ready!"
echo "================================="
echo "📋 Mock API Server: http://localhost:8000"
echo "🎨 Frontend App:    http://localhost:5173"
echo ""
echo "📝 Available API endpoints:"
echo "   GET    /health"
echo "   GET    /accounts/targets"
echo "   POST   /accounts/targets"
echo "   PUT    /accounts/targets/:id"
echo "   DELETE /accounts/targets/:id"
echo "   POST   /accounts/targets/:id/validate"
echo "   GET    /drs/quotas"
echo "   POST   /drs/tag-sync"
echo ""
echo "💡 Use any token in Authorization header (e.g., 'Bearer test-token')"
echo "🔧 Local development mode automatically bypasses Cognito authentication"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for user to stop
wait