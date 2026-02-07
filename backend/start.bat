@echo off
REM DocAI Backend Startup Script (Windows)

echo Starting DocAI Backend...

REM Check if .env file exists
if not exist .env (
    echo .env file not found, copying from .env.example...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

REM Create virtual environment if needed
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python init_db.py

REM Start the server
echo Starting server...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
