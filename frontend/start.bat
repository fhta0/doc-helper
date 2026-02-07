@echo off
echo Starting DocAI Frontend...

REM Install dependencies if needed
if not exist node_modules (
    echo Installing dependencies...
    npm install
)

REM Start dev server
echo Starting dev server...
npm run dev
