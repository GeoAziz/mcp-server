# Migration Guide: Monolithic to Modular Architecture

**Last Updated:** March 25, 2026  
**Status:** Recommended for all new projects  
**Breaking Changes:** None - both implementations are API-compatible

## Overview

The MCP Server codebase has been reorganized into a modular architecture for improved maintainability, testability, and scalability. The legacy monolithic implementation remains fully functional and is maintained for backward compatibility.

## Timeline

| Phase | Status | Recommendation |
|-------|--------|---|
| **Phase 1: Transition Period** | ✅ Complete | Use modular version for new projects; maintain legacy for backward compatibility |
| **Phase 2: Deprecation** | ➡️ Current | Legacy implementation clearly marked `@deprecated`; all features work identically |
| **Phase 3: Sunset** | ⏳ Planned for v2.0 | Monolithic files will be removed in next major release |

## What Changed

### File Structure

**Old (Monolithic):**
```
mcp_server/
├── mcp_server.py          # Main FastAPI app
├── routers/
│   ├── v1.py             # All v1 endpoints
│   └── v2.py             # v2 stubs
├── models.py              # SQLAlchemy models
├── auth.py                # Authentication
├── database.py            # Database config
└── log_manager.py         # Logging
```

**New (Modular):**
```
mcp_server/
└── app/
    ├── main.py            # FastAPI app (recommended)
    ├── auth.py            # Authentication
    ├── database.py        # Database config
    ├── log_manager.py     # Logging
    ├── models/
    │   ├── __init__.py    # All ORM models
    ├── routers/
    │   ├── v1.py         # v1 endpoints
    │   └── v2.py         # v2 endpoints
    └── services/
        ├── user_service.py
        ├── task_service.py
        ├── config_service.py
        └── integration_service.py
```

### Key Improvements

| Aspect | Old | New |
|--------|-----|-----|
| **Startup** | `python mcp_server.py` | `python -m uvicorn app.main:app --reload` |
| **Code Organization** | Mixed concerns in main file | Clean separation (routers → services → models) |
| **Testing** | Integration-heavy | Unit testable components |
| **Maintainability** | Hard to track changes | Clear module boundaries |
| **Scalability** | Everything in one file | Easy to add new services |

## Migration Steps

### Step 1: Update Startup Command

**Before:**
```bash
python mcp_server.py
```

**After (Development):**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**After (Production):**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 2: Verify API Compatibility

All endpoints have identical behavior:

```bash
# Both still work (legacy and new)
curl -X POST http://localhost:8000/mcp/query -H "Content-Type: application/json" \
  -d '{"action": "list_users", "params": {}}'

curl -X POST http://localhost:8000/api/v1/query -H "Content-Type: application/json" \
  -d '{"action": "list_users", "params": {}}'
```

**Recommendation:** Migrate clients to `/api/v1/*` endpoints for better long-term support.

### Step 3: Environment Variables (No Changes)

All environment variables remain the same:

```bash
export MCP_API_KEY="your-secret-key"
export MCP_GITHUB_TOKEN="your-github-token"
export MCP_FIGMA_TOKEN="your-figma-token"
export MCP_CORS_ORIGINS="https://yourdomain.com"
export MCP_RATE_LIMIT="100/minute"
export MCP_LOG_RETENTION="1000"
```

### Step 4: Deployment Configuration

**Docker:** No changes required - both implementations work identically

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

**Kubernetes/Cloud:** Update entrypoint command per Step 1

## Error Handling Standardization

The modular version implements consistent error handling:

| Error Type | HTTP Status | Response |
|---|---|---|
| `ValueError` | 400 | `{"detail": "error message"}` |
| `HTTPException` | Custom | `{"detail": "error message"}` |
| Unexpected | 500 | `{"detail": "Internal server error"}` |

## Database Migration Path (Future)

When Alembic migrations are configured:

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

**Current Status:** Alembic not yet configured. Using pure SQLAlchemy for schema management.

## Testing

Both implementations pass 89 identical tests:

```bash
pytest tests/ -v
```

All tests pass against `app.main` (modular version).

## Rollback Plan

If needed, revert to monolithic version:

```bash
# Stop new version
# Restart with old command
python mcp_server.py
```

No data loss - database remains unchanged regardless of implementation.

## FAQ

**Q: Do I need to migrate immediately?**  
A: No. Both versions work identically. Plan migration during next release cycle.

**Q: Will my API keys/authentication break?**  
A: No. Authentication is identical across both implementations.

**Q: Can I run both simultaneously?**  
A: Not on the same port. You can run one on 8000 and another on 8001 for testing.

**Q: What about my custom integrations?**  
A: Service layer is identical. Custom handlers in `app/services/` work the same way.

**Q: Will the legacy version be removed?**  
A: Yes, planned for v2.0. After migration period, monolithic files will be removed.

## Support

For issues during migration:
- Check [README.md](README.md#migration-from-legacy-monolithic-structure)
- Review [architecture decisions](docs/MCP_INTEGRATIONS.md)
- Run full test suite: `pytest tests/ -v`

---

**Recommendation:** Migrate all new deployments to modular version immediately. Existing deployments can migrate at their own pace.
