"""
Task management service
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Task


async def list_tasks(params: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """List tasks with optional filters"""
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


async def add_task(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Create a new task"""
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


async def update_task(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Update an existing task"""
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


async def delete_task(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Delete a task"""
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


async def search_tasks(params: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """Search tasks by query string"""
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


async def summarize_data(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Summarize current data state"""
    from app.models import User
    
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
