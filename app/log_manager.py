"""
Log Manager - Structured logging with database persistence
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from sqlalchemy.orm import Session

# Configure logging
logger = logging.getLogger(__name__)


class LogManager:
    """Manages structured JSON logs with database persistence"""
    
    def __init__(self, db_session_factory=None, max_logs: int = None):
        """
        Initialize LogManager with database session factory
        
        Args:
            db_session_factory: Factory function to create database sessions
            max_logs: Maximum number of logs to retain. 
                     If None, reads from MCP_LOG_RETENTION env var, defaults to 1000
        """
        if max_logs is None:
            max_logs = int(os.getenv("MCP_LOG_RETENTION", "1000"))
        
        self.max_logs = max_logs
        self.db_session_factory = db_session_factory
        logger.info(f"LogManager initialized with retention limit: {self.max_logs}")
    
    def log(self, action: str, payload: Dict[str, Any] = None, status: str = "success", db: Session = None) -> Dict[str, Any]:
        """
        Log a structured entry
        
        Args:
            action: The action being logged
            payload: Optional payload/parameters for the action
            status: Status of the action (success, error, pending, etc.)
            db: Database session (optional, will create one if not provided)
        
        Returns:
            The created log entry
        """
        from app.models import Log
        
        entry_data = {
            "timestamp": datetime.utcnow(),
            "action": action,
            "payload": payload or {},
            "status": status
        }
        
        # Use provided session or create a new one
        close_session = False
        if db is None:
            if self.db_session_factory is None:
                raise ValueError("No database session provided and no session factory configured")
            db = self.db_session_factory()
            close_session = True
        
        try:
            # Create log entry
            log_entry = Log(**entry_data)
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            
            # Enforce retention limit - delete oldest logs if exceeded
            total_logs = db.query(Log).count()
            if total_logs > self.max_logs:
                # Delete oldest logs
                logs_to_delete = total_logs - self.max_logs
                oldest_logs = db.query(Log).order_by(Log.id.asc()).limit(logs_to_delete).all()
                for old_log in oldest_logs:
                    db.delete(old_log)
                db.commit()
                logger.debug(f"Trimmed {logs_to_delete} old logs to maintain {self.max_logs} limit")
            
            # Return entry as dict with ISO format timestamp
            return {
                "timestamp": log_entry.timestamp.isoformat(),
                "action": log_entry.action,
                "payload": log_entry.payload,
                "status": log_entry.status
            }
        
        finally:
            if close_session:
                db.close()
    
    def get_logs(self, limit: Optional[int] = None, offset: int = 0, db: Session = None) -> List[Dict[str, Any]]:
        """
        Retrieve logs with optional pagination
        
        Args:
            limit: Maximum number of logs to return (None = all)
            offset: Number of logs to skip from the end
            db: Database session (optional, will create one if not provided)
        
        Returns:
            List of log entries
        """
        from app.models import Log
        
        # Use provided session or create a new one
        close_session = False
        if db is None:
            if self.db_session_factory is None:
                raise ValueError("No database session provided and no session factory configured")
            db = self.db_session_factory()
            close_session = True
        
        try:
            # Query logs ordered by timestamp descending (most recent first)
            query = db.query(Log).order_by(Log.timestamp.desc())
            
            # Apply offset
            if offset > 0:
                query = query.offset(offset)
            
            # Apply limit
            if limit is not None:
                query = query.limit(limit)
            
            # Fetch and convert to dict
            logs = query.all()
            
            # Reverse to get chronological order (oldest to newest in the result set)
            logs = list(reversed(logs))
            
            return [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "payload": log.payload,
                    "status": log.status
                }
                for log in logs
            ]
        
        finally:
            if close_session:
                db.close()
    
    def get_log_count(self, db: Session = None) -> int:
        """
        Get total number of logs currently stored
        
        Args:
            db: Database session (optional, will create one if not provided)
        """
        from app.models import Log
        
        # Use provided session or create a new one
        close_session = False
        if db is None:
            if self.db_session_factory is None:
                raise ValueError("No database session provided and no session factory configured")
            db = self.db_session_factory()
            close_session = True
        
        try:
            return db.query(Log).count()
        finally:
            if close_session:
                db.close()
    
    def clear_logs(self, db: Session = None):
        """
        Clear all logs
        
        Args:
            db: Database session (optional, will create one if not provided)
        """
        from app.models import Log
        
        # Use provided session or create a new one
        close_session = False
        if db is None:
            if self.db_session_factory is None:
                raise ValueError("No database session provided and no session factory configured")
            db = self.db_session_factory()
            close_session = True
        
        try:
            db.query(Log).delete()
            db.commit()
            logger.info("All logs cleared")
        finally:
            if close_session:
                db.close()
    
    def get_logs_by_action(self, action: str, db: Session = None) -> List[Dict[str, Any]]:
        """
        Get logs filtered by action
        
        Args:
            action: The action to filter by
            db: Database session (optional, will create one if not provided)
        
        Returns:
            List of matching log entries
        """
        from app.models import Log
        
        # Use provided session or create a new one
        close_session = False
        if db is None:
            if self.db_session_factory is None:
                raise ValueError("No database session provided and no session factory configured")
            db = self.db_session_factory()
            close_session = True
        
        try:
            logs = db.query(Log).filter(Log.action == action).order_by(Log.timestamp.desc()).all()
            return [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "payload": log.payload,
                    "status": log.status
                }
                for log in logs
            ]
        finally:
            if close_session:
                db.close()
    
    def get_logs_by_status(self, status: str, db: Session = None) -> List[Dict[str, Any]]:
        """
        Get logs filtered by status
        
        Args:
            status: The status to filter by
            db: Database session (optional, will create one if not provided)
        
        Returns:
            List of matching log entries
        """
        from app.models import Log
        
        # Use provided session or create a new one
        close_session = False
        if db is None:
            if self.db_session_factory is None:
                raise ValueError("No database session provided and no session factory configured")
            db = self.db_session_factory()
            close_session = True
        
        try:
            logs = db.query(Log).filter(Log.status == status).order_by(Log.timestamp.desc()).all()
            return [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "payload": log.payload,
                    "status": log.status
                }
                for log in logs
            ]
        finally:
            if close_session:
                db.close()

