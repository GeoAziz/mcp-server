# Migration Guide: Monolithic → Modular Architecture

## Overview

The MCP Server has been reorganized for better maintainability. The monolithic implementation (`mcp_server.py`) is now deprecated in favor of the modular structure in `app/`. Both are functionally identical with **zero breaking changes**.

## Timeline

- **Now**: Both implementations work identically. Use at your own pace.
- **Recommended**: Switch to the modular version immediately for new projects.
- **Deprecation Path**: Legacy files at root level will remain available for backward compatibility.

---

## What Changed

### Directory Structure

```
BEFORE (Monolithic)          AFTER (Modular)
├── mcp_server.py            ├── app/
├── auth.py                  │   ├── main.py
├── database.py              │   ├── auth.py
├── log_manager.py           │   ├── database.py
├── models.py                │   ├── log_manager.py
└── routers/                 │   ├── models/
    ├── v1.py                │   │   └── __init__.py
    └── v2.py                │   ├── routers/
                             │   │   ├── v1.py
                             │   │   └── v2.py
                             │   └── services/
                             │       ├── user_service.py
                             │       ├── task_service.py
                             │       ├── config_service.py
                             │       └── integration_service.py
```

### Key Improvements

1. **Separation of Concerns**
   - `routers/` - HTTP handlers only
   - `services/` - Business logic (reusable)
   - `models/` - SQLAlchemy ORM definitions
   - `auth.py`, `database.py`, `log_manager.py` - Infrastructure

2. **Standardized Error Handling**
   - All `ValueError` exceptions → HTTP 400 Bad Request
   - Consistent error response format
   - Automatic logging of failures

3. **Better Testability**
   - Services can be tested independently
   - Cleaner dependency injection
   - In-memory SQLite database for tests

4. **Scalability**
   - Easy to add new services
   - Services layer enables code reuse
   - Clear patterns for new endpoints

---

## Migration Steps

### Step 1: Update Startup Command

**Old:**
```bash
python mcp_server.py
```

**New:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the shell task in VS Code if available.

### Step 2: Update Production Deployment

Change your startup script or systemd service to use the new command.

**Example systemd service:**
```ini
[Service]
WorkingDirectory=/path/to/mcp_server
ExecStart=/usr/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 3: Update Client Code (Optional)

**API endpoints remain identical.** However, if you're currently using `/mcp/*` routes, consider migrating to `/api/v1/*`:

```bash
# Old (still works)
curl -X POST http://localhost:8000/mcp/query \
  -H "Content-Type: application/json" \
  -d '{"action": "list_users", "params": {}}'

# New (recommended)
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"action": "list_users", "params": {}}'
```

### Step 4: Verify Compatibility

Run the test suite to ensure everything works:
```bash
pytest tests/ -v
```

All 89 tests should pass.

---

## API Compatibility

### Endpoints

| Route | Status | Note |
|-------|--------|------|
| `/api/v1/*` | ✅ Current | Use this for new clients |
| `/api/v2/*` | 📋 Available | Placeholder for future enhancements |
| `/mcp/*` | ⚠️ Deprecated | Still works, no expiration date |

### Response Format

Unchanged. All endpoints return:
```json
{
  "success": true,
  "data": { ... },
  "message": "...",
  "timestamp": "2026-03-25T..."
}
```

---

## What's Different for Developers

### Code Organization

If you're adding new features:

1. **Create a service** in `app/services/` for business logic
2. **Register it** in `app/routers/v1.py` handlers
3. **Write tests** in `tests/`
4. **Document** in README.md

Example: Adding a new action

```python
# app/services/notification_service.py
async def send_notification(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    user = params.get("user")
    message = params.get("message")
    
    if not user or not message:
        raise ValueError("user and message are required")
    
    # Business logic here
    return {"sent": True, "user": user}

# app/routers/v1.py - add to handlers dict
"send_notification": notification_service.send_notification,

# Test it
# pytest tests/test_new_feature.py
```

### Error Handling

All errors use a consistent pattern:

```python
# In services - raise ValueError for validation errors
if not username:
    raise ValueError("username is required")

# In routers - catch and respond
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

---

## FAQ

### Q: Do I need to update my client code?
**A:** Not required. Both implementations work identically. But migrating to `/api/v1/*` routes is recommended.

### Q: When will the old code be removed?
**A:** No specific timeline. Legacy files will be maintained for backward compatibility indefinitely or until announced.

### Q: Can I run both simultaneously?
**A:** No, they both listen on the same port (8000). Use only one.

### Q: Are there any breaking changes?
**A:** No. The modular version is a 1:1 drop-in replacement.

### Q: How do I add a new action?
**A:** Create a service function, register it in the handlers dictionary in `app/routers/v1.py`, and write tests. See examples in `app/services/`.

---

## Rollback Plan

If something goes wrong:

```bash
# Revert to monolithic version
python mcp_server.py

# This still works, no data loss
# Both versions use the same database
```

---

## Support

- **Tests:** `pytest tests/ -v`
- **API Docs:** http://localhost:8000/docs
- **Issues?** Check the logs: Check output from uvicorn for detailed errors
- **Questions?** See the README.md for detailed API documentation

---

**Last Updated:** March 2026  
**Status:** Active (both implementations supported)
