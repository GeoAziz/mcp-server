"""
User management service
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import User, Task


async def list_users(params: Dict[str, Any], db: Session) -> List[str]:
    """Get all users"""
    users = db.query(User).all()
    return [u.username for u in users]


async def add_user(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Add a new user"""
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
        user_metadata=params.get("metadata", {})
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"username": username, "added": True}


async def remove_user(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Remove a user"""
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


async def get_user(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Get user details with their tasks"""
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
