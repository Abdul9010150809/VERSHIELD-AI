#!/bin/bash

# VeriShield Frontend Startup Script

echo "🚀 Starting VeriShield Frontend..."

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Start the development server
echo "✅ Starting Next.js server on http://localhost:3000"
npm run dev
