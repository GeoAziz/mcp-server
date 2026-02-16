"""
Configuration management service
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Config


async def get_config(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Get configuration values"""
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


async def update_config(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Update configuration value"""
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


async def calculate(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Perform calculations"""
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
