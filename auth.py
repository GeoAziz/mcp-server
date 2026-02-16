"""
Authentication module for MCP Server
Provides API key authentication for protected endpoints
"""

import os
import secrets
import logging
from fastapi import Header, HTTPException, status
from typing import Optional

logger = logging.getLogger(__name__)

# Flag to track if we've already logged the warning about disabled auth
_auth_disabled_warning_logged = False


def get_api_key_from_env() -> Optional[str]:
    """
    Get the API key from environment variable.
    Returns None if not set.
    """
    return os.getenv("MCP_API_KEY")


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """
    FastAPI dependency for API key authentication.
    
    Validates the X-API-Key header against the MCP_API_KEY environment variable.
    
    Args:
        x_api_key: The API key from the X-API-Key header
        
    Returns:
        The validated API key, or None if authentication is disabled
        
    Raises:
        HTTPException: 401 if X-API-Key header is missing
        HTTPException: 403 if X-API-Key header is invalid
    """
    global _auth_disabled_warning_logged
    
    expected_api_key = get_api_key_from_env()
    
    # If no API key is configured, skip authentication
    if expected_api_key is None:
        # Log warning only once to avoid excessive logging
        if not _auth_disabled_warning_logged:
            logger.warning(
                "MCP_API_KEY environment variable not set - authentication is disabled. "
                "Set MCP_API_KEY to enable API key authentication."
            )
            _auth_disabled_warning_logged = True
        return None
    
    # Check if X-API-Key header is provided
    if x_api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )
    
    # Validate the API key using constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return x_api_key
