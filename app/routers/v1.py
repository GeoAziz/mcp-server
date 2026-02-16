"""
API Version 1 Router
All endpoints from the original MCP Server
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.auth import verify_api_key
from app.log_manager import LogManager
from app.database import get_db, SessionLocal
from app.models import User, Task, Config, Log
from app.services import user_service, task_service, config_service

# Configure logging
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Get rate limit from environment or use default
RATE_LIMIT = os.getenv("MCP_RATE_LIMIT", "100/minute")

# Initialize LogManager with database session factory
log_manager = LogManager(db_session_factory=SessionLocal)

# Create v1 router
router = APIRouter()

# ============================================================================
# DATABASE HELPER FUNCTIONS
# ============================================================================

def get_snapshot(db: Session) -> Dict[str, Any]:
    """Get complete memory snapshot from database"""
    # Get all users
    users = db.query(User).all()
    user_list = [u.username for u in users]
    
    # Get all tasks
    tasks = db.query(Task).all()
    task_list = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "assigned_to": t.assigned_to,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat()
        }
        for t in tasks
    ]
    
    # Get config
    config_entries = db.query(Config).all()
    config_dict = {c.key: c.value for c in config_entries}
    
    # Get log count
    log_count = log_manager.get_log_count(db=db)
    
    return {
        "users": user_list,
        "tasks": task_list,
        "projects": [],  # Keep for backward compatibility
        "config": config_dict,
        "session_data": {},  # Keep for backward compatibility
        "stats": {
            "total_users": len(user_list),
            "total_tasks": len(task_list),
            "total_projects": 0,
            "total_logs": log_count
        }
    }


def log_action(action: str, params: Dict[str, Any], result: Any, status: str = "success", db: Session = None):
    """Log agent actions for observability using structured logging"""
    # Truncate long results for payload
    payload = {
        "params": params,
        "result": str(result)[:200]  # Truncate long results
    }
    log_manager.log(action=action, payload=payload, status=status, db=db)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QueryRequest(BaseModel):
    """
    Standard query request format for performing actions
    
    The query endpoint uses an action-based architecture where you specify
    an action name and provide the necessary parameters.
    """
    action: str = Field(
        ..., 
        description="Name of the action to perform",
        examples=["list_users", "add_task", "search_tasks"]
    )
    params: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Parameters for the action (varies by action type)",
        examples=[
            {"username": "alice"},
            {"title": "Build feature", "priority": "high"},
            {"query": "database"}
        ]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "action": "list_users",
                    "params": {}
                },
                {
                    "action": "add_user",
                    "params": {
                        "username": "alice",
                        "role": "admin"
                    }
                },
                {
                    "action": "add_task",
                    "params": {
                        "title": "Implement API documentation",
                        "description": "Add OpenAPI/Swagger docs",
                        "priority": "high",
                        "assigned_to": "alice"
                    }
                },
                {
                    "action": "search_tasks",
                    "params": {
                        "query": "documentation"
                    }
                }
            ]
        }

class QueryResponse(BaseModel):
    """
    Standard response format for all API endpoints
    
    All successful and failed operations return this consistent structure.
    """
    success: bool = Field(
        ..., 
        description="Whether the operation was successful",
        examples=[True]
    )
    data: Any = Field(
        ..., 
        description="Response data (type varies by endpoint)",
        examples=[
            {"users": ["alice", "bob"]},
            {"username": "alice", "added": True}
        ]
    )
    message: Optional[str] = Field(
        None, 
        description="Human-readable message about the operation",
        examples=["Action 'list_users' completed successfully"]
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp when the response was generated",
        examples=["2026-02-16T16:00:00.000000"]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "data": ["alice", "bob", "charlie"],
                    "message": "Action 'list_users' completed successfully",
                    "timestamp": "2026-02-16T16:00:00.000000"
                }
            ]
        }

# ============================================================================
# V1 ENDPOINTS
# ============================================================================

@router.get(
    "/state",
    summary="Get Memory State",
    description="""
    Get memory snapshot with optional filtering and pagination.
    
    This endpoint provides access to all stored data including users, tasks, configuration, and logs.
    
    **Query Parameters:**
    - `entity`: Filter by entity type (`users` | `tasks` | `config` | `logs`)
    - `limit`: Maximum number of items to return
    - `offset`: Number of items to skip (for pagination)
    - `status`: Filter tasks by status (only applies when `entity=tasks`)
    
    **Examples:**
    
    Get full state:
    ```bash
    curl http://localhost:8000/api/v1/state
    ```
    
    Get only tasks:
    ```bash
    curl http://localhost:8000/api/v1/state?entity=tasks
    ```
    
    Get pending tasks with pagination:
    ```bash
    curl "http://localhost:8000/api/v1/state?entity=tasks&status=pending&limit=10"
    ```
    
    Get users (page 2, 20 per page):
    ```bash
    curl "http://localhost:8000/api/v1/state?entity=users&offset=20&limit=20"
    ```
    """,
    response_description="Memory snapshot with requested data"
)
@limiter.limit(RATE_LIMIT)
async def get_state(
    request: Request,
    entity: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    status: Optional[str] = None,
    _api_key: Optional[str] = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get memory snapshot with optional filtering and pagination
    
    Query Parameters:
    - entity: Filter by entity type (users | tasks | config | logs)
    - limit: Maximum number of items to return
    - offset: Number of items to skip (for pagination)
    - status: Filter tasks by status (only applies when entity=tasks)
    """
    try:
        # Validate entity parameter if provided
        valid_entities = ["users", "tasks", "config", "logs"]
        if entity and entity not in valid_entities:
            logger.warning(f"Invalid entity requested: {entity}")
            return QueryResponse(
                success=False,
                data={},
                message=f"Invalid entity '{entity}'. Valid options: {', '.join(valid_entities)}"
            )
        
        # If no parameters provided, return full snapshot (backward compatibility)
        if entity is None and limit is None and offset is None and status is None:
            snapshot = get_snapshot(db)
            logger.info("Full state snapshot requested")
            return QueryResponse(
                success=True,
                data=snapshot,
                message="Memory snapshot retrieved"
            )
        
        # Build filtered response
        filtered_data = {}
        
        if entity:
            # Filter by specific entity
            if entity == "users":
                users = db.query(User).all()
                user_list = [u.username for u in users]
                
                # Apply pagination
                total = len(user_list)
                if offset is not None:
                    user_list = user_list[offset:]
                if limit is not None:
                    user_list = user_list[:limit]
                
                filtered_data = {
                    "users": user_list,
                    "total": total,
                    "count": len(user_list)
                }
            
            elif entity == "tasks":
                # Start with query
                query = db.query(Task)
                
                # Apply status filter if provided
                if status:
                    query = query.filter(Task.status == status)
                
                # Get total count after filtering
                total_filtered = query.count()
                
                # Apply pagination
                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)
                
                tasks = query.all()
                task_list = [
                    {
                        "id": t.id,
                        "title": t.title,
                        "description": t.description,
                        "priority": t.priority,
                        "status": t.status,
                        "assigned_to": t.assigned_to,
                        "created_at": t.created_at.isoformat(),
                        "updated_at": t.updated_at.isoformat()
                    }
                    for t in tasks
                ]
                
                filtered_data = {
                    "tasks": task_list,
                    "total": total_filtered,
                    "count": len(task_list)
                }
                if status:
                    filtered_data["filtered_by_status"] = status
            
            elif entity == "config":
                config_entries = db.query(Config).all()
                config_dict = {c.key: c.value for c in config_entries}
                filtered_data = {
                    "config": config_dict
                }
            
            elif entity == "logs":
                logs = log_manager.get_logs(limit=limit, offset=offset or 0, db=db)
                filtered_data = {
                    "logs": logs,
                    "total": log_manager.get_log_count(db=db),
                    "count": len(logs)
                }
        else:
            # No entity specified, but limit/offset/status provided
            # Apply to all applicable entities
            snapshot = get_snapshot(db)
            filtered_data = snapshot.copy()
            
            # Apply limit/offset to lists
            if limit is not None or offset is not None:
                off = offset or 0
                lim = limit
                
                # Apply to users
                users_data = snapshot["users"][off:]
                if lim is not None:
                    users_data = users_data[:lim]
                filtered_data["users"] = users_data
                
                # Apply to tasks (with status filter if provided)
                tasks_data = snapshot["tasks"]
                if status:
                    tasks_data = [t for t in tasks_data if t.get("status") == status]
                tasks_data = tasks_data[off:]
                if lim is not None:
                    tasks_data = tasks_data[:lim]
                filtered_data["tasks"] = tasks_data
        
        logger.info(f"Filtered state requested - entity: {entity}, limit: {limit}, offset: {offset}, status: {status}")
        return QueryResponse(
            success=True,
            data=filtered_data,
            message="Filtered memory snapshot retrieved"
        )
    
    except Exception as e:
        logger.error(f"Error getting state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/query",
    summary="Execute Action",
    description="""
    Main query endpoint - handles all agent actions using an action-based architecture.
    
    **Supported Actions:**
    
    **User Management:**
    - `list_users` - Get all users
    - `add_user` - Add new user (params: username, role?, metadata?)
    - `remove_user` - Remove user (params: username)
    - `get_user` - Get user details (params: username)
    
    **Task Management:**
    - `list_tasks` - List all tasks (params: status?, assigned_to?)
    - `add_task` - Create new task (params: title, description?, priority?, assigned_to?)
    - `update_task` - Update task (params: task_id, title?, description?, priority?, status?, assigned_to?)
    - `delete_task` - Delete task (params: task_id)
    - `search_tasks` - Search tasks (params: query)
    
    **Configuration:**
    - `get_config` - Get config values (params: key?)
    - `update_config` - Update config (params: key, value)
    
    **Utilities:**
    - `calculate` - Perform calculations (params: operation, numbers)
    - `summarize_data` - Get data summary (params: none)
    
    **Examples:**
    
    List all users:
    ```bash
    curl -X POST http://localhost:8000/api/v1/query \\
      -H "Content-Type: application/json" \\
      -d '{"action": "list_users", "params": {}}'
    ```
    
    Add a new user:
    ```bash
    curl -X POST http://localhost:8000/api/v1/query \\
      -H "Content-Type: application/json" \\
      -d '{
        "action": "add_user",
        "params": {
          "username": "alice",
          "role": "admin"
        }
      }'
    ```
    
    Create a task:
    ```bash
    curl -X POST http://localhost:8000/api/v1/query \\
      -H "Content-Type: application/json" \\
      -d '{
        "action": "add_task",
        "params": {
          "title": "Implement feature X",
          "description": "Build the new feature",
          "priority": "high",
          "assigned_to": "alice"
        }
      }'
    ```
    
    Search tasks:
    ```bash
    curl -X POST http://localhost:8000/api/v1/query \\
      -H "Content-Type: application/json" \\
      -d '{
        "action": "search_tasks",
        "params": {
          "query": "feature"
        }
      }'
    ```
    """,
    response_description="Action result with success status and data"
)
@limiter.limit(RATE_LIMIT)
async def query(request: Request, body: QueryRequest, _api_key: Optional[str] = Depends(verify_api_key), db: Session = Depends(get_db)):
    """
    Main query endpoint - handles all agent actions
    
    Supported actions:
    - list_users
    - add_user
    - remove_user
    - list_tasks
    - add_task
    - update_task
    - delete_task
    - get_config
    - update_config
    - search_tasks
    """
    try:
        action = body.action
        params = body.params or {}
        
        logger.info(f"Query received - Action: {action}, Params: {params}")
        
        # Route to appropriate handler
        result = await handle_action(action, params, db)
        
        # Log the action with success status
        log_action(action, params, result, status="success", db=db)
        
        return QueryResponse(
            success=True,
            data=result,
            message=f"Action '{action}' completed successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Invalid action: {e}")
        # Log the failed action
        log_action(body.action, body.params or {}, str(e), status="error", db=db)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        # Log the failed action
        log_action(body.action, body.params or {}, str(e), status="error", db=db)
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/logs",
    summary="Get Action Logs",
    description="""
    Get recent agent action logs with structured information about all operations.
    
    Each log entry includes:
    - `timestamp` - When the action occurred (ISO 8601 format)
    - `action` - The action that was performed
    - `payload` - Parameters and truncated result
    - `status` - success or error
    
    Logs are automatically trimmed based on the retention limit (configurable via `MCP_LOG_RETENTION` environment variable).
    
    **Examples:**
    
    Get last 10 logs:
    ```bash
    curl http://localhost:8000/api/v1/logs?limit=10
    ```
    
    Get last 100 logs:
    ```bash
    curl http://localhost:8000/api/v1/logs?limit=100
    ```
    
    With authentication:
    ```bash
    curl http://localhost:8000/api/v1/logs?limit=20 \\
      -H "X-API-Key: your-secret-key"
    ```
    """,
    response_description="List of recent action logs"
)
@limiter.limit(RATE_LIMIT)
async def get_logs(request: Request, limit: int = 100, _api_key: Optional[str] = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Get recent agent action logs"""
    try:
        logs = log_manager.get_logs(limit=limit, db=db)
        return QueryResponse(
            success=True,
            data=logs,
            message=f"Retrieved {len(logs)} logs"
        )
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/reset",
    summary="Reset Memory",
    description="""
    Reset all memory including users, tasks, config, and logs.
    
    **⚠️ WARNING:** This operation is destructive and cannot be undone!
    
    All data will be permanently deleted including:
    - All users
    - All tasks
    - All configuration entries
    - All action logs
    
    After reset, default configuration values will be re-initialized.
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/reset \\
      -H "X-API-Key: your-secret-key"
    ```
    """,
    response_description="Confirmation of memory reset"
)
@limiter.limit(RATE_LIMIT)
async def reset_memory(request: Request, _api_key: Optional[str] = Depends(verify_api_key), db: Session = Depends(get_db)):
    """Reset all memory (use with caution!)"""
    logger.warning("Memory reset requested")
    
    # Delete all data from database
    db.query(User).delete()
    db.query(Task).delete()
    db.query(Config).delete()
    db.query(Log).delete()
    db.commit()
    
    # Re-initialize default config
    from app.database import init_db
    init_db()
    
    return QueryResponse(
        success=True,
        data={"reset": True},
        message="Memory reset complete"
    )

# ============================================================================
# ACTION HANDLERS
# ============================================================================

async def handle_action(action: str, params: Dict[str, Any], db: Session) -> Any:
    """Route actions to appropriate handlers"""
    
    handlers = {
        # User management
        "list_users": user_service.list_users,
        "add_user": user_service.add_user,
        "remove_user": user_service.remove_user,
        "get_user": user_service.get_user,
        
        # Task management
        "list_tasks": task_service.list_tasks,
        "add_task": task_service.add_task,
        "update_task": task_service.update_task,
        "delete_task": task_service.delete_task,
        "search_tasks": task_service.search_tasks,
        
        # Config management
        "get_config": config_service.get_config,
        "update_config": config_service.update_config,
        
        # Utility
        "calculate": config_service.calculate,
        "summarize_data": task_service.summarize_data,
    }
    
    handler = handlers.get(action)
    if not handler:
        raise ValueError(f"Unknown action: {action}")
    
    return await handler(params, db)
