# Architecture Decision Log (ADL)

**Project:** MCP Server  
**Last Updated:** March 25, 2026  
**Status:** Active

## ADL-001: Monolithic to Modular Architecture Transition

**Date:** March 25, 2026  
**Status:** ✅ APPROVED & IMPLEMENTED  
**Justification Level:** HIGH

### Decision

Transition the MCP Server codebase from a monolithic single-file architecture to a modular service-based architecture, with the legacy implementation maintained for backward compatibility.

### Context

The original implementation consolidated all functionality in:
- `mcp_server.py` (1169 lines) - Main FastAPI application + all handlers
- `routers/v1.py`, `routers/v2.py` - API endpoints, mixed with business logic
- `models.py`, `auth.py`, `database.py`, `log_manager.py` - Utility modules scattered at root

### Problem

| Issue | Impact |
|-------|--------|
| Single 1169-line file | Difficult to navigate, test, maintain |
| Mixed concerns | Business logic embedded in HTTP handlers |
| Hard to test | Must mock FastAPI Request/Response for unit tests |
| Scalability friction | Adding new features requires editing main.py |
| Unclear imports | Circular dependencies possible, unclear dependencies |
| No service layer | Code duplication between actions |

### Solution

Reorganize into `app/` package with clear separation:

```
app/
├── main.py              # FastAPI initialization only
├── auth.py              # Authentication logic (single concern)
├── database.py          # Database configuration (single concern)
├── log_manager.py       # Logging logic (single concern)
├── models/
│   └── __init__.py      # SQLAlchemy ORM models only
├── routers/
│   ├── v1.py           # HTTP endpoint definitions
│   └── v2.py           # Future endpoints
└── services/           # ⭐ New: Business logic layer
    ├── user_service.py
    ├── task_service.py
    ├── config_service.py
    └── integration_service.py
```

### Benefits

✅ **Separation of Concerns**
- HTTP layer (routers) handles only request/response
- Business logic (services) handles only domain operations
- Models handle only data representation

✅ **Testability**
- Services can be unit tested without FastAPI Request
- Each service is independently testable
- No external dependencies needed for logic tests

✅ **Maintainability**
- Clear module boundaries
- Easy to locate where changes belong
- Reduced cognitive load (each file has single purpose)

✅ **Scalability**
- Add new service directly without touching existing code
- Easy to add new routes that reuse existing services
- Supports future microservices extraction

✅ **Reusability**
- Services can be imported by CLI, scheduled tasks, or other services
- Avoids HTTP-specific imports in business logic

### Tradeoffs

| Cost | Mitigation |
|------|-----------|
| Two implementations during transition | Clear deprecation path; both functionally identical |
| More files to navigate | Better organized; easier to find things |
| Slightly more indirection | Services are thin; easy to understand call chain |

### Backward Compatibility

✅ **100% API Compatible**
- All `/mcp/*` endpoints still work (marked `@deprecated`)
- All `/api/v1/*` endpoints unchanged
- Applications using old version can migrate at their own pace

### Implementation

| Component | Status | Details |
|-----------|--------|---------|
| Modular codebase created | ✅ Complete | `app/` package fully functional |
| Services layer established | ✅ Complete | User, Task, Config, Integration services |
| Deprecation warnings added | ✅ Complete | All legacy files marked deprecated |
| Testing | ✅ Complete | 89 tests pass on modular version |
| Documentation | ✅ Complete | Migration guide, deployment guide |

### Migration Path

**Phase 1: Transition (NOW)**
- Legacy version fully functional, marked deprecated
- Modular version recommended for new projects
- Both implementations support all features

**Phase 2: Consolidation (v1.1)**
- Consider removing legacy routers/models at root
- Simplify imports to use only `app.*`

**Phase 3: Sunset (v2.0)**
- Remove monolithic `mcp_server.py`
- Keep `app/` as sole implementation

### Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Existing clients break | LOW | API fully compatible, tested |
| Developers confused about which to use | MEDIUM | Clear documentation, deprecation warnings |
| Migration becomes urgent unexpectedly | LOW | Modular version works identically |

### Decision Criteria Met

✅ **Does it solve the identified problem?** Yes - clear separation of concerns  
✅ **Is implementation feasible?** Yes - completed in single iteration  
✅ **Does it maintain backward compatibility?** Yes - 100% API compatible  
✅ **Does it improve testability?** Yes - services independently testable  
✅ **Does it reduce future friction?** Yes - easier to add features  

### Related ADLs

- ADL-002: Error Handling Standardization
- ADL-003: API Versioning Strategy

---

## ADL-002: Error Handling Standardization

**Date:** March 25, 2026  
**Status:** ✅ APPROVED & IMPLEMENTED  
**Justification Level:** MEDIUM

### Decision

Standardize error handling across MCP Server: all `ValueError` exceptions in business logic automatically return HTTP 400 Bad Request.

### Context

Previously, error handling was mixed:
- Services raised `ValueError` for validation errors
- Routers converted `ValueError` → `HTTPException(400)`
- Some endpoints used `HTTPException` directly
- Inconsistent error response format

### Problem

- Unclear which layer should validate input
- Error responses inconsistent across endpoints
- Difficult to reason about what HTTP status is returned
- No global exception handler

### Solution

**Consistent pattern across all services:**

```python
# Services raise ValueError for validation/business logic errors
async def add_user(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    username = params.get("username")
    if not username:
        raise ValueError("username is required")  # ← Consistent
    # ...

# Routers catch ValueError and convert to HTTP 400
try:
    result = await handler(params, db)
    return {"success": True, "data": result}
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))  # ← Consistent
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # ← Consistent
```

**Benefits:**

✅ All validation errors → HTTP 400  
✅ All unexpected errors → HTTP 500  
✅ Single exception pattern across codebase  
✅ Easy to reason about error behavior  

### Impact

- No breaking changes to API
- Makes error responses predictable
- Simplifies error handling in client code

---

## ADL-003: Maintain Dual Implementation During Transition

**Date:** March 25, 2026  
**Status:** ✅ APPROVED & IMPLEMENTED  
**Justification Level:** MEDIUM

### Decision

Maintain both monolithic (`mcp_server.py`) and modular (`app/main.py`) implementations in parallel during transition period.

### Rationale

**Option A: Big Bang Replacement** ❌
- Risk: Breaks existing deployments
- Risk: Difficult debugging if issues arise
- Cost: High friction for migrations

**Option B: Dual Implementation** ✅
- Risk: Low - leverages identical logic
- Benefit: Existing deployment stable
- Benefit: New deployments use better architecture
- Benefit: Proven testing before migration
- Cleanup: Remove legacy in v2.0

### Implementation

Legacy files marked with deprecation notice:
```python
"""
⚠️ DEPRECATED - [File Purpose]
Use '[new_path]' instead.
"""
```

README updated with migration guide and clear recommendations.

### Timeline

| Phase | Duration | Action |
|-------|----------|--------|
| Now | v1.0 | Both work, modular recommended |
| Soon | v1.1 | Deprecation warnings, guide docs |
| Later | v2.0 | Remove legacy implementation |

### Exit Criteria

Both implementations can continue indefinitely if:
- Maintenance burden is acceptable
- APIs remain synchronized
- Tests keep both versions in sync

Current assessment: **Removable in v2.0** with low disruption

---

## ADL-004: Service Layer Pattern

**Date:** March 25, 2026  
**Status:** ✅ APPROVED & IMPLEMENTED  
**Justification Level:** HIGH

### Decision

Implement service layer (`app/services/`) that contains all business logic and action handler functions.

### Pattern

```
Request → Router → Service → Model → Database → Response
  ↓        ↓        ↓        ↓       ↓         ↓
HTTP    HTTP      Business   ORM   SQLAlchemy JSON
Handler Logic    Operations Object
```

### Benefits

✅ **Layered Isolation**
- HTTP concerns stay in routers
- Business logic stays in services  
- Data concerns stay in models

✅ **Reusable Logic**
- Services can be called from CLI, cron jobs, WebSocket handlers
- No HTTP-specific imports in services

✅ **Testable**
- Services testable without FastAPI context
- Mock database easily
- Pure Python unit tests

✅ **Extensible**
- Add new service endpoints without new handler code
- Add new handlers by importing service and adding to router

### Service Contract

All services follow pattern:

```python
async def action_name(params: Dict[str, Any], db: Session) -> Any:
    """
    Perform action_name
    
    Args:
        params: User-provided parameters (already parsed)
        db: SQLAlchemy session for database access
    
    Returns:
        Serializable result (dict, list, str, etc.)
    
    Raises:
        ValueError: If validation fails
        Any Exception: If unexpected error (converted to 500)
    """
    # Validation
    if not params.get("required_param"):
        raise ValueError("required_param is required")
    
    # Business logic
    # ...
    
    # Return serializable result
    return {"result": value}
```

### Current Services

| Service | Responsibility | Actions |
|---------|---|---|
| `user_service` | User CRUD | list, add, remove, get |
| `task_service` | Task CRUD + search | list, add, update, delete, search, summarize |
| `config_service` | App configuration | get, update, calculate |
| `integration_service` | External APIs | github_*, figma_*, playwright_* |

### Future Services

- `notification_service` - Email/Slack alerts
- `backup_service` - Database backups
- `analytics_service` - Usage analytics
- `cache_service` - Redis caching

---

## Summary

| ADL | Decision | Status | Impact |
|-----|----------|--------|--------|
| ADL-001 | Monolithic → Modular | ✅ DONE | Architecture cleaner, easier to maintain |
| ADL-002 | Error handling standard | ✅ DONE | Responses predictable, debugging easier |
| ADL-003 | Dual implementation during transition | ✅ DONE | Low-risk migration path |
| ADL-004 | Service layer pattern | ✅ DONE | Business logic reusable, testable |

**Recommendation for v2.0:** Remove legacy implementation after sunset period.

---

**Approval Status:** ✅ APPROVED FOR PRODUCTION
