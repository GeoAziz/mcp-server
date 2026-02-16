"""
Log Manager - Structured logging with configurable retention
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

# Configure logging
logger = logging.getLogger(__name__)


class LogManager:
    """Manages structured JSON logs with configurable retention"""
    
    def __init__(self, max_logs: int = None):
        """
        Initialize LogManager with configurable retention
        
        Args:
            max_logs: Maximum number of logs to retain. 
                     If None, reads from MCP_LOG_RETENTION env var, defaults to 1000
        """
        if max_logs is None:
            max_logs = int(os.getenv("MCP_LOG_RETENTION", "1000"))
        
        self.max_logs = max_logs
        self.logs: List[Dict[str, Any]] = []
        logger.info(f"LogManager initialized with retention limit: {self.max_logs}")
    
    def log(self, action: str, payload: Dict[str, Any] = None, status: str = "success") -> Dict[str, Any]:
        """
        Log a structured entry
        
        Args:
            action: The action being logged
            payload: Optional payload/parameters for the action
            status: Status of the action (success, error, pending, etc.)
        
        Returns:
            The created log entry
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "payload": payload or {},
            "status": status
        }
        
        self.logs.append(entry)
        
        # Enforce retention limit - keep only the most recent logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
            logger.debug(f"Trimmed logs to {self.max_logs} entries")
        
        return entry
    
    def get_logs(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve logs with optional pagination
        
        Args:
            limit: Maximum number of logs to return (None = all)
            offset: Number of logs to skip from the end
        
        Returns:
            List of log entries
        """
        # Get logs from the end (most recent)
        if offset > 0:
            end_idx = len(self.logs) - offset
            logs = self.logs[:end_idx] if end_idx > 0 else []
        else:
            logs = self.logs
        
        if limit is not None:
            # Return the last 'limit' logs
            return logs[-limit:]
        
        return logs
    
    def get_log_count(self) -> int:
        """Get total number of logs currently stored"""
        return len(self.logs)
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
        logger.info("All logs cleared")
    
    def get_logs_by_action(self, action: str) -> List[Dict[str, Any]]:
        """
        Get logs filtered by action
        
        Args:
            action: The action to filter by
        
        Returns:
            List of matching log entries
        """
        return [log for log in self.logs if log.get("action") == action]
    
    def get_logs_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get logs filtered by status
        
        Args:
            status: The status to filter by
        
        Returns:
            List of matching log entries
        """
        return [log for log in self.logs if log.get("status") == status]
