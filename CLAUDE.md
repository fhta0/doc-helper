# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**文心雕龙·AI (DocAI)** is a document format checking system that validates .docx files against predefined formatting rules. It combines rule-based checking with AI-powered content analysis.

**Architecture**: FastAPI backend + Vue 3 frontend, deployed with Docker Compose (Nginx reverse proxy)

## Development Commands

### Backend (Python/FastAPI)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize/reset database
python init_db.py

# Run development server (with hot reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest                           # all tests
pytest --cov=app                # with coverage
pytest -m unit                  # unit tests only
pytest -m integration           # integration tests only
pytest -m api                   # API tests only
pytest tests/test_specific.py   # single test file
pytest -k "test_name"           # tests matching pattern

# Test with specific markers (defined in pytest.ini):
# - unit: Unit tests
# - integration: Integration tests
# - slow: Slow running tests
# - api: API endpoint tests
# - service: Service layer tests
# - model: Model/database tests
```

### Frontend (Vue 3/Vite)
```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test                # run tests
npm run test:ui            # run tests with UI
npm run test:coverage      # run tests with coverage report
```

## Architecture Overview

### Backend Structure (`backend/`)

```
backend/
├── app/
│   ├── api/               # FastAPI route handlers (auth, checks, purchase, guest, rule_templates)
│   ├── core/              # Configuration, security, logging
│   ├── models/            # SQLAlchemy ORM models (User, Check, Order, RuleTemplate)
│   ├── services/          # Business logic layer
│   └── utils/             # Utilities
├── main.py                # FastAPI application entry point
└── init_db.py             # Database initialization
```

**Key Services:**
- `docx_parser.py`: Extracts structure and content from .docx files using python-docx
- `rule_engine.py`: Executes deterministic format rules (margins, fonts, paragraphs, headings, captions)
- `ai_checker.py`: OpenAI-compatible API integration for AI-powered rule checking
- `ai_content_checker.py`: Specialized AI for spell-checking and cross-reference validation
- `structure_checker.py`: Validates document hierarchy and structure
- `revision_engine.py`: Automatic document fixing capabilities (generates revised .docx with tracked changes)

**Rule Checking Flow:**
1. Upload → `docx_parser` extracts document data
2. `rule_engine` runs deterministic rules (checker="deterministic")
3. If enabled, `ai_checker` processes AI rules (checker="ai")
4. Results compiled and returned

**Database Models:**
- `User`: Authentication, quota management (3 free checks/month)
- `Check`: Document check records with results
- `Order`: Purchase history for paid check packages
- `RuleTemplate`: Configurable rules stored in database

### Frontend Structure (`frontend/`)

```
frontend/
├── src/
│   ├── api/               # Axios API client (auth.js, checks.js, etc.)
│   ├── router/            # Vue Router configuration
│   ├── stores/            # Pinia state management (auth, user)
│   ├── views/             # Page components
│   ├── components/        # Reusable components
│   ├── App.vue            # Root component
│   └── main.js            # Entry point
├── index.html
├── vite.config.js
└── vitest.config.js       # Test configuration
```

**State Management:** Pinia stores for `auth` (token, user info) and `user` (quota, profile)
- Path alias: `@` maps to `src/` (configured in both `vite.config.js` and `vitest.config.js`)

**Routing:** Vue Router with authentication guards

### API Design

- Base URL: `http://localhost:8000` (dev), proxied through Nginx in production
- Auto-generated docs: `/docs` (Swagger UI), `/redoc` (ReDoc)
- Authentication: JWT tokens (Bearer token in Authorization header)
- Response format: `{ code, message, data }`
- Frontend proxy: Vite dev server proxies `/api` to backend at `http://localhost:8000`

**Key Endpoints:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT)
- `GET /api/auth/user/profile` - Get current user info
- `POST /api/check/upload` - Upload .docx file
- `POST /api/check/submit` - Submit document for checking
- `GET /api/check/{check_id}` - Get check results
- `GET /api/check/recent/list` - Get recent check history
- `GET /api/check/rules/list` - Get available rules

## Rule System

Rules are database-stored templates with these key fields:

- `checker`: "deterministic" (rule-based) or "ai" (AI-powered)
- `category`: "page", "font", "paragraph", "heading", "figure", "table", "structure"
- `check_type`: Specific check within category
- `severity`: "error", "warning", "info"
- `ai_prompt`: Custom prompt for AI rules
- `enabled`: Active/inactive status

**Deterministic Rules**: Directly compare document properties (e.g., page margins, font sizes)

**AI Rules**: Send document context to LLM with custom prompt for semantic analysis

## AI Integration

- **Provider**: OpenAI-compatible API (configurable, supports DeepSeek, OpenAI)
- **Configuration**: Environment variables (`AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`)
- **Services**:
  - `ai_checker.py`: General AI-powered rule checking with custom prompts
  - `ai_content_checker.py`: Specialized for spell-checking and cross-reference validation
- **Enabled via**: `enable_ai` flag in check requests
- **Timeout**: 60 seconds (configurable via `AI_TIMEOUT`)

## Testing

**Backend**: pytest with coverage
- Test markers defined in `pytest.ini` (unit, integration, slow, api, service, model)
- Fixtures in `conftest.py`
- Coverage reports: terminal, HTML, and XML (generated automatically with `pytest`)
- Test files in `backend/tests/`

**Frontend**: Vitest with Vue Test Utils
- Happy DOM environment (configured in `vitest.config.js`)
- Coverage with v8 provider (reports: text, json, html)
- Setup file: `src/tests/setup.js` (mocks localStorage, sessionStorage, matchMedia, window.location)
- Test files: `src/tests/**/*.spec.js`

## Database

- **MySQL 5.7+** with SQLAlchemy ORM
- **Character set**: utf8mb4_unicode_ci
- **Connection**: Configured in `app/core/config.py` via environment variables
- **Initialization**: Run `python init_db.py` to create tables
- **PyMySQL** driver with `cryptography` for secure connections

## Configuration

Backend environment variables (create `.env` in project root, used by docker-compose):
- `DATABASE_URL`: MySQL connection string (default: `mysql+pymysql://root:password@localhost:3306/doc_ai`)
- `SECRET_KEY`: JWT signing key
- `AI_API_KEY`: AI service API key
- `AI_BASE_URL`: AI service base URL (default: `https://api.openai.com/v1`)
- `AI_MODEL`: Model name (default: `gpt-4o-mini`)
- `WECHAT_MCHID`, `WECHAT_APPID`, `WECHAT_APPSECRET`, `WECHAT_APIV3_KEY`: WeChat Pay credentials
- `LOG_LEVEL`: Logging level (default: `INFO`)

## Payment Integration

WeChat Pay support for purchasing check packages:
- Configuration via `WECHAT_*` environment variables
- Certificate-based authentication (merchant cert, private key, platform public key)
- Webhook notifications via `WECHAT_NOTIFY_URL`
- OAuth flow via `WECHAT_REDIRECT_URI`

## Development Notes

- Backend runs on port 8000, frontend dev server on 5173
- Production: Nginx on port 8080 (HTTP) / 443 (HTTPS) proxies to backend
- Frontend dev server proxies `/api` requests to backend via Vite proxy configuration
- CORS enabled for development
- Hot reload enabled on both ends (`uvicorn --reload` for backend, Vite HMR for frontend)
- Structured logging with configurable levels (logs written to `backend/logs/`)
- Global exception handler returns consistent error format
- JWT token expires after 7 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
