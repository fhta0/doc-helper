#!/bin/bash

echo "Starting DocAI Frontend..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start dev server
echo "Starting dev server..."
npm run dev
