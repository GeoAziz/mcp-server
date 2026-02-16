# GitHub Copilot Instructions for MCP Server

## Project Overview

MCP Server (Model Context Protocol) is a FastAPI-based backend service that reduces AI agent context window bloat by centralizing memory, tools, and logic. Instead of embedding tool schemas and state in every LLM prompt, agents query this persistent server via HTTP.

**Core Value Proposition:** 90%+ reduction in context tokens by externalizing tool definitions and memory.

## Build, Test, and Run

### Installation
```bash
# Automated setup (includes demo)
python setup.py

# Manual installation
pip install -r requirements.txt
```

### Running the Server
```bash
# Development (port 8000)
python mcp_server.py

# With authentication
export MCP_API_KEY="your-secret-key"
python mcp_server.py

# With custom CORS and rate limiting
export MCP_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
export MCP_RATE_LIMIT="200/minute"
python mcp_server.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_users.py

# Run specific test function
pytest tests/test_tasks.py::test_add_task

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run tests marked as integration
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

All tests use an in-memory SQLite database for speed and isolation. See `tests/README.md` for details.

## Architecture

### Two Server Implementations

1. **`mcp_server.py`** - Legacy monolithic server (still functional, backward compatible)
2. **`app/main.py`** - New modular architecture (preferred for new features)

Both implement identical APIs but organize code differently. The modular version separates concerns:

```
app/
├── main.py           # FastAPI app initialization, CORS, rate limiting
├── auth.py           # API key authentication logic
├── database.py       # SQLAlchemy session management
├── log_manager.py    # Structured logging with retention
├── models/           # SQLAlchemy ORM models (User, Task, Config, Log)
├── routers/          # API route handlers
│   ├── v1.py         # Version 1 endpoints (stable, recommended)
│   └── v2.py         # Version 2 endpoints (placeholder for future)
└── services/         # Business logic separated from routes
    ├── user_service.py
    ├── task_service.py
    └── config_service.py
```

### Database Layer

**SQLAlchemy ORM** with support for SQLite (default) and PostgreSQL:
- **Development:** In-memory SQLite (`sqlite:///:memory:`)
- **Production:** File-based SQLite or PostgreSQL via `DATABASE_URL` env var
- **Models:** `User`, `Task`, `Config`, `Log` (see `app/models/`)
- **Migration-ready:** Alembic installed but not yet configured

### API Versioning Strategy

The server supports three API families for backward compatibility:

1. **`/api/v1/*`** - Current stable version (use this for new clients)
2. **`/api/v2/*`** - Placeholder for future enhancements
3. **`/mcp/*`** - Legacy endpoints (deprecated but maintained)

All versions implement identical functionality. Migration path: `/mcp/state` → `/api/v1/state`

### Action Handler Pattern

The core `/query` endpoint routes requests to handler functions based on `action` parameter:

```python
# Client sends
POST /api/v1/query
{
  "action": "add_task",
  "params": {"title": "New task", "priority": "high"}
}

# Server routes to handler
async def add_task(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    # Business logic here
    return {"id": task_id, "created": True}
```

Handlers are registered in a dictionary mapping action names to functions. See `routers/v1.py` for the complete handler registry.

### Middleware Stack

Applied in order (from outer to inner):
1. **CORS** - Configurable origins via `MCP_CORS_ORIGINS`
2. **Rate Limiting** - Per-IP throttling via `slowapi` (default: 100/minute)
3. **Authentication** - Optional API key validation when `MCP_API_KEY` is set
4. **Logging** - Structured JSON logs with automatic retention management

### Structured Logging

`log_manager.py` provides automatic action logging:
- Every action is logged with timestamp, params, result, and status
- Logs stored in database (`Log` model)
- Automatic trimming to `MCP_LOG_RETENTION` limit (default: 1000)
- Accessible via `/api/v1/logs` endpoint

## Key Conventions

### Database Session Management

**Always use dependency injection** for database sessions:

```python
# In routers - correct
@router.get("/api/v1/state")
async def get_state(db: Session = Depends(get_db)):
    users = db.query(User).all()
    # Session automatically closed after request

# In services - correct (session passed from router)
async def list_users(params: Dict[str, Any], db: Session) -> List[str]:
    users = db.query(User).all()
    return [u.username for u in users]
```

Never create sessions manually in route handlers. Use `Depends(get_db)` or pass the session from the router.

### Adding New Actions

To add a new action to the query endpoint:

1. **Create service function** in `app/services/`:
```python
# app/services/notification_service.py
async def send_notification(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    user = params.get("user")
    message = params.get("message")
    
    # Validation
    if not user or not message:
        raise ValueError("user and message are required")
    
    # Business logic
    # ...
    
    return {"sent": True, "user": user}
```

2. **Register handler** in `app/routers/v1.py`:
```python
from app.services import notification_service

# Add to handlers dictionary
handlers = {
    # ... existing handlers ...
    "send_notification": notification_service.send_notification,
}
```

3. **Document in README.md** under "Available Actions"

### Environment Variables

All configuration uses environment variables with sensible defaults:

- `DATABASE_URL` - Database connection (default: `sqlite:///./mcp_server.db`)
- `MCP_API_KEY` - Optional authentication key (no default)
- `MCP_CORS_ORIGINS` - Comma-separated allowed origins (default: `*`)
- `MCP_RATE_LIMIT` - Format: `100/minute`, `10/second`, `1000/hour` (default: `100/minute`)
- `MCP_LOG_RETENTION` - Max log entries (default: `1000`)

Never hardcode configuration values. Always use `os.getenv()` with a sensible default.

### Response Format

All endpoints return consistent JSON responses:

```python
{
    "success": true,
    "data": { ... },           # Actual response data
    "message": "...",          # Human-readable status
    "timestamp": "2026-02-16T..." # ISO 8601 timestamp
}
```

Error responses (HTTP 4xx/5xx):
```python
{
    "detail": "Error message explaining what went wrong"
}
```

### State Endpoint Filtering

The `/api/v1/state` endpoint supports query parameters for filtering and pagination:

- `entity` - Filter by type: `users`, `tasks`, `config`, `logs`
- `status` - Filter tasks by status (only with `entity=tasks`)
- `limit` - Max items to return
- `offset` - Skip items for pagination

Example: `/api/v1/state?entity=tasks&status=pending&limit=10`

### Testing Patterns

Tests use pytest fixtures from `tests/conftest.py`:

```python
def test_add_user(client):
    """Test with default client (no auth)"""
    response = client.post("/api/v1/query", json={
        "action": "add_user",
        "params": {"username": "alice"}
    })
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_with_auth(client_with_auth):
    """Test with authentication enabled"""
    response = client_with_auth.post(
        "/api/v1/query",
        json={"action": "list_users", "params": {}},
        headers={"X-API-Key": "test-key-12345"}
    )
    assert response.status_code == 200
```

**Important:** Tests run against in-memory SQLite database that resets between test functions. No external database required.

### Code Organization Rules

1. **Routers** (`app/routers/`) - Handle HTTP concerns (request/response, validation, dependencies)
2. **Services** (`app/services/`) - Implement business logic (no HTTP knowledge)
3. **Models** (`app/models/`) - SQLAlchemy ORM definitions only
4. **Database** (`app/database.py`) - Session management and initialization
5. **Auth** (`app/auth.py`) - Authentication logic only

Keep concerns separated. If a router function exceeds 20-30 lines, extract business logic to a service.

### Async Handlers

All action handlers are `async` for consistency, even if they don't use `await`:

```python
# Correct - async even without await
async def list_users(params: Dict[str, Any], db: Session) -> List[str]:
    users = db.query(User).all()
    return [u.username for u in users]
```

This maintains a uniform interface and supports future async operations.

### Error Handling Pattern

Raise appropriate exceptions; FastAPI converts them to HTTP responses:

```python
# Service layer - raise Python exceptions
if not username:
    raise ValueError("username is required")

if existing_user:
    raise ValueError(f"User {username} already exists")

# FastAPI automatically converts to:
# 400 Bad Request with {"detail": "username is required"}
```

For custom HTTP status codes, use `HTTPException` from FastAPI.

## Common Pitfalls

### ❌ Don't create database sessions manually in routes
```python
# Wrong
@router.get("/users")
async def get_users():
    db = SessionLocal()  # Don't do this
    users = db.query(User).all()
    db.close()
    return users
```

### ✅ Use dependency injection
```python
# Correct
@router.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

### ❌ Don't mix business logic in routers
```python
# Wrong - validation and DB logic mixed in router
@router.post("/api/v1/query")
async def query(request: QueryRequest, db: Session = Depends(get_db)):
    if request.action == "add_user":
        username = request.params.get("username")
        if not username:
            raise ValueError("...")
        existing = db.query(User).filter(...).first()
        # ... lots more logic ...
```

### ✅ Delegate to service layer
```python
# Correct - router delegates to service
@router.post("/api/v1/query")
async def query(request: QueryRequest, db: Session = Depends(get_db)):
    handler = handlers.get(request.action)
    if not handler:
        raise HTTPException(404, f"Unknown action: {request.action}")
    
    result = await handler(request.params, db)
    return {"success": True, "data": result}
```

### ❌ Don't forget to commit database changes
```python
# Wrong - changes not persisted
user = User(username="alice")
db.add(user)
# Missing: db.commit()
```

### ✅ Always commit after writes
```python
# Correct
user = User(username="alice")
db.add(user)
db.commit()
db.refresh(user)  # Load any DB-generated fields
```

## Documentation

- `README.md` - Comprehensive user guide, API reference, deployment instructions
- `QUICKSTART.md` - 5-minute getting started guide with integration patterns
- `IMPLEMENTATION_SUMMARY.md` - CORS and rate limiting implementation details
- `tests/README.md` - Test suite organization and conventions
- **Interactive API Docs** - http://localhost:8000/docs (when server running)

When adding features, update README.md if they're user-facing and this file if they affect development patterns.

## GitHub Workflows

CI/CD runs on every push and PR:
- `.github/workflows/test.yml` - Runs full test suite on Python 3.9-3.12, generates coverage
- `.github/workflows/ci.yml` - Additional checks (CodeQL, linting if configured)

Tests must pass for all Python versions before merging.
