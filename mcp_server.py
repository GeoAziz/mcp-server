"""
MCP Server - Model Context Protocol Server
A persistent backend service for AI agents to reduce context window bloat
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uvicorn
import logging
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from auth import verify_api_key
from log_manager import LogManager
from database import get_db, init_db, SessionLocal, reset_db
from models import User, Task, Config, Log

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Get rate limit from environment or use default
RATE_LIMIT = os.getenv("MCP_RATE_LIMIT", "100/minute")
logger.info(f"Rate limit configured: {RATE_LIMIT}")

# Get CORS origins from environment or use default
CORS_ORIGINS = os.getenv("MCP_CORS_ORIGINS", "*").split(",")
logger.info(f"CORS origins configured: {CORS_ORIGINS}")

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Persistent memory and tool server for AI agents",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
# Configure via MCP_CORS_ORIGINS environment variable (comma-separated)
# Example: MCP_CORS_ORIGINS="https://example.com,https://app.example.com"
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize LogManager with database session factory
log_manager = LogManager(db_session_factory=SessionLocal)

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
    """Standard query request format"""
    action: str = Field(..., description="Action to perform")
    params: Optional[Dict[str, Any]] = Field(default={}, description="Action parameters")

class QueryResponse(BaseModel):
    """Standard query response format"""
    success: bool
    data: Any
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class TaskCreate(BaseModel):
    """Task creation model"""
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    assigned_to: Optional[str] = None

class UserCreate(BaseModel):
    """User creation model"""
    username: str
    role: Optional[str] = "user"
    metadata: Optional[Dict[str, Any]] = {}

# ============================================================================
# CORE ENDPOINTS
# ============================================================================

@app.get("/")
@limiter.limit(RATE_LIMIT)
async def root(request: Request):
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "MCP Server",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/mcp/state")
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

@app.post("/mcp/query")
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

@app.get("/mcp/logs")
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

@app.post("/mcp/reset")
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
    from database import init_db
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
        "list_users": handle_list_users,
        "add_user": handle_add_user,
        "remove_user": handle_remove_user,
        "get_user": handle_get_user,
        
        # Task management
        "list_tasks": handle_list_tasks,
        "add_task": handle_add_task,
        "update_task": handle_update_task,
        "delete_task": handle_delete_task,
        "search_tasks": handle_search_tasks,
        
        # Config management
        "get_config": handle_get_config,
        "update_config": handle_update_config,
        
        # Utility
        "calculate": handle_calculate,
        "summarize_data": handle_summarize_data,
    }
    
    handler = handlers.get(action)
    if not handler:
        raise ValueError(f"Unknown action: {action}")
    
    return await handler(params, db)

# User handlers
async def handle_list_users(params: Dict[str, Any], db: Session) -> List[str]:
    users = db.query(User).all()
    return [u.username for u in users]

async def handle_add_user(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    username = params.get("username")
    if not username:
        raise ValueError("username is required")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise ValueError(f"User {username} already exists")
    
    # Create new user
    user = User(
        username=username,
        role=params.get("role", "user"),
        metadata=params.get("metadata", {})
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"username": username, "added": True}

async def handle_remove_user(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    username = params.get("username")
    if not username:
        raise ValueError("username is required")
    
    # Find user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError(f"User {username} not found")
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"username": username, "removed": True}

async def handle_get_user(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    username = params.get("username")
    
    # Find user
    user = db.query(User).filter(User.username == username).first()
    
    if user:
        # Get user's tasks
        tasks = db.query(Task).filter(Task.assigned_to == username).all()
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
        
        return {
            "username": username,
            "exists": True,
            "task_count": len(task_list),
            "tasks": task_list
        }
    
    return {"username": username, "exists": False}

# Task handlers
async def handle_list_tasks(params: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    status = params.get("status")
    assigned_to = params.get("assigned_to")
    
    # Start with base query
    query = db.query(Task)
    
    # Apply filters
    if status:
        query = query.filter(Task.status == status)
    
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    
    # Execute query and convert to dict
    tasks = query.all()
    return [
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

async def handle_add_task(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    title = params.get("title")
    if not title:
        raise ValueError("title is required")
    
    # Create new task
    task = Task(
        title=title,
        description=params.get("description", ""),
        priority=params.get("priority", "medium"),
        status=params.get("status", "pending"),
        assigned_to=params.get("assigned_to")
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat()
    }

async def handle_update_task(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    task_id = params.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")
    
    # Find task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    # Update fields
    for key in ["title", "description", "priority", "status", "assigned_to"]:
        if key in params:
            setattr(task, key, params[key])
    
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "assigned_to": task.assigned_to,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat()
    }

async def handle_delete_task(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    task_id = params.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")
    
    # Find task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    # Delete task
    db.delete(task)
    db.commit()
    
    return {"task_id": task_id, "deleted": True}

async def handle_search_tasks(params: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    query_str = params.get("query", "").lower()
    
    # Search in title and description
    tasks = db.query(Task).filter(
        (Task.title.ilike(f"%{query_str}%")) | 
        (Task.description.ilike(f"%{query_str}%"))
    ).all()
    
    return [
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

# Config handlers
async def handle_get_config(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    key = params.get("key")
    
    if key:
        # Get specific config value
        config = db.query(Config).filter(Config.key == key).first()
        if config:
            return {key: config.value}
        return {key: None}
    
    # Get all config
    config_entries = db.query(Config).all()
    return {c.key: c.value for c in config_entries}

async def handle_update_config(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    key = params.get("key")
    value = params.get("value")
    
    if not key:
        raise ValueError("key is required")
    
    # Check if config exists
    config = db.query(Config).filter(Config.key == key).first()
    
    if config:
        # Update existing config
        config.value = value
        config.updated_at = datetime.utcnow()
    else:
        # Create new config
        config = Config(key=key, value=value)
        db.add(config)
    
    db.commit()
    db.refresh(config)
    
    return {key: value, "updated": True}

# Utility handlers
async def handle_calculate(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Example tool: perform calculations"""
    operation = params.get("operation")
    numbers = params.get("numbers", [])
    
    if operation == "sum":
        result = sum(numbers)
    elif operation == "average":
        result = sum(numbers) / len(numbers) if numbers else 0
    elif operation == "max":
        result = max(numbers) if numbers else None
    elif operation == "min":
        result = min(numbers) if numbers else None
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    return {"operation": operation, "result": result}

async def handle_summarize_data(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Example tool: summarize current data state"""
    
    # Get counts from database
    total_users = db.query(User).count()
    total_tasks = db.query(Task).count()
    
    # Count tasks by status
    pending_count = db.query(Task).filter(Task.status == "pending").count()
    in_progress_count = db.query(Task).filter(Task.status == "in_progress").count()
    completed_count = db.query(Task).filter(Task.status == "completed").count()
    
    # Count tasks by priority
    high_count = db.query(Task).filter(Task.priority == "high").count()
    medium_count = db.query(Task).filter(Task.priority == "medium").count()
    low_count = db.query(Task).filter(Task.priority == "low").count()
    
    return {
        "summary": {
            "total_users": total_users,
            "total_tasks": total_tasks,
            "tasks_by_status": {
                "pending": pending_count,
                "in_progress": in_progress_count,
                "completed": completed_count
            },
            "tasks_by_priority": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            }
        }
    }

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization complete")

if __name__ == "__main__":
    logger.info("Starting MCP Server...")
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
