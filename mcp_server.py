"""
MCP Server - Model Context Protocol Server
A persistent backend service for AI agents to reduce context window bloat
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uvicorn
import logging
from auth import verify_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Persistent memory and tool server for AI agents",
    version="1.0.0"
)

# Add CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# IN-MEMORY STORAGE (Replace with DB for production)
# ============================================================================

class MemoryStore:
    """Centralized memory management"""
    
    def __init__(self):
        self.users: List[str] = []
        self.tasks: List[Dict[str, Any]] = []
        self.projects: List[Dict[str, Any]] = []
        self.agent_logs: List[Dict[str, Any]] = []
        self.config: Dict[str, Any] = {
            "max_tasks": 100,
            "default_priority": "medium"
        }
        self.session_data: Dict[str, Any] = {}
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get complete memory snapshot"""
        return {
            "users": self.users,
            "tasks": self.tasks,
            "projects": self.projects,
            "config": self.config,
            "session_data": self.session_data,
            "stats": {
                "total_users": len(self.users),
                "total_tasks": len(self.tasks),
                "total_projects": len(self.projects),
                "total_logs": len(self.agent_logs)
            }
        }
    
    def log_action(self, action: str, params: Dict[str, Any], result: Any):
        """Log agent actions for observability"""
        self.agent_logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "params": params,
            "result": str(result)[:200]  # Truncate long results
        })
        
        # Keep only last 1000 logs
        if len(self.agent_logs) > 1000:
            self.agent_logs = self.agent_logs[-1000:]

# Initialize memory
memory = MemoryStore()

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
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "MCP Server",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/mcp/state")
async def get_state(api_key: str = Depends(verify_api_key)):
    """Get complete memory snapshot"""
    try:
        snapshot = memory.get_snapshot()
        logger.info("State snapshot requested")
        return QueryResponse(
            success=True,
            data=snapshot,
            message="Memory snapshot retrieved"
        )
    except Exception as e:
        logger.error(f"Error getting state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/query")
async def query(request: QueryRequest, api_key: str = Depends(verify_api_key)):
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
        action = request.action
        params = request.params or {}
        
        logger.info(f"Query received - Action: {action}, Params: {params}")
        
        # Route to appropriate handler
        result = await handle_action(action, params)
        
        # Log the action
        memory.log_action(action, params, result)
        
        return QueryResponse(
            success=True,
            data=result,
            message=f"Action '{action}' completed successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Invalid action: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/logs")
async def get_logs(limit: int = 100, api_key: str = Depends(verify_api_key)):
    """Get recent agent action logs"""
    try:
        logs = memory.agent_logs[-limit:]
        return QueryResponse(
            success=True,
            data=logs,
            message=f"Retrieved {len(logs)} logs"
        )
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/reset")
async def reset_memory(api_key: str = Depends(verify_api_key)):
    """Reset all memory (use with caution!)"""
    global memory
    logger.warning("Memory reset requested")
    memory = MemoryStore()
    return QueryResponse(
        success=True,
        data={"reset": True},
        message="Memory reset complete"
    )

# ============================================================================
# ACTION HANDLERS
# ============================================================================

async def handle_action(action: str, params: Dict[str, Any]) -> Any:
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
    
    return await handler(params)

# User handlers
async def handle_list_users(params: Dict[str, Any]) -> List[str]:
    return memory.users

async def handle_add_user(params: Dict[str, Any]) -> Dict[str, Any]:
    username = params.get("username")
    if not username:
        raise ValueError("username is required")
    
    if username in memory.users:
        raise ValueError(f"User {username} already exists")
    
    memory.users.append(username)
    return {"username": username, "added": True}

async def handle_remove_user(params: Dict[str, Any]) -> Dict[str, Any]:
    username = params.get("username")
    if not username:
        raise ValueError("username is required")
    
    if username not in memory.users:
        raise ValueError(f"User {username} not found")
    
    memory.users.remove(username)
    return {"username": username, "removed": True}

async def handle_get_user(params: Dict[str, Any]) -> Dict[str, Any]:
    username = params.get("username")
    if username in memory.users:
        # Get user's tasks
        user_tasks = [t for t in memory.tasks if t.get("assigned_to") == username]
        return {
            "username": username,
            "exists": True,
            "task_count": len(user_tasks),
            "tasks": user_tasks
        }
    return {"username": username, "exists": False}

# Task handlers
async def handle_list_tasks(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    status = params.get("status")
    assigned_to = params.get("assigned_to")
    
    tasks = memory.tasks
    
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    
    if assigned_to:
        tasks = [t for t in tasks if t.get("assigned_to") == assigned_to]
    
    return tasks

async def handle_add_task(params: Dict[str, Any]) -> Dict[str, Any]:
    title = params.get("title")
    if not title:
        raise ValueError("title is required")
    
    task_id = len(memory.tasks) + 1
    task = {
        "id": task_id,
        "title": title,
        "description": params.get("description", ""),
        "priority": params.get("priority", "medium"),
        "status": params.get("status", "pending"),
        "assigned_to": params.get("assigned_to"),
        "created_at": datetime.utcnow().isoformat()
    }
    
    memory.tasks.append(task)
    return task

async def handle_update_task(params: Dict[str, Any]) -> Dict[str, Any]:
    task_id = params.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")
    
    task = next((t for t in memory.tasks if t["id"] == task_id), None)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    # Update fields
    for key in ["title", "description", "priority", "status", "assigned_to"]:
        if key in params:
            task[key] = params[key]
    
    task["updated_at"] = datetime.utcnow().isoformat()
    return task

async def handle_delete_task(params: Dict[str, Any]) -> Dict[str, Any]:
    task_id = params.get("task_id")
    if not task_id:
        raise ValueError("task_id is required")
    
    task = next((t for t in memory.tasks if t["id"] == task_id), None)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    memory.tasks.remove(task)
    return {"task_id": task_id, "deleted": True}

async def handle_search_tasks(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = params.get("query", "").lower()
    
    results = [
        t for t in memory.tasks
        if query in t.get("title", "").lower() or query in t.get("description", "").lower()
    ]
    
    return results

# Config handlers
async def handle_get_config(params: Dict[str, Any]) -> Dict[str, Any]:
    key = params.get("key")
    if key:
        return {key: memory.config.get(key)}
    return memory.config

async def handle_update_config(params: Dict[str, Any]) -> Dict[str, Any]:
    key = params.get("key")
    value = params.get("value")
    
    if not key:
        raise ValueError("key is required")
    
    memory.config[key] = value
    return {key: value, "updated": True}

# Utility handlers
async def handle_calculate(params: Dict[str, Any]) -> Dict[str, Any]:
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

async def handle_summarize_data(params: Dict[str, Any]) -> Dict[str, Any]:
    """Example tool: summarize current data state"""
    return {
        "summary": {
            "total_users": len(memory.users),
            "total_tasks": len(memory.tasks),
            "tasks_by_status": {
                "pending": len([t for t in memory.tasks if t.get("status") == "pending"]),
                "in_progress": len([t for t in memory.tasks if t.get("status") == "in_progress"]),
                "completed": len([t for t in memory.tasks if t.get("status") == "completed"])
            },
            "tasks_by_priority": {
                "high": len([t for t in memory.tasks if t.get("priority") == "high"]),
                "medium": len([t for t in memory.tasks if t.get("priority") == "medium"]),
                "low": len([t for t in memory.tasks if t.get("priority") == "low"])
            }
        }
    }

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting MCP Server...")
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
