"""
Test cases for authentication and authorization
"""

import pytest
import os


def test_no_auth_when_api_key_not_set(client):
    """Test that endpoints work without authentication when MCP_API_KEY is not set"""
    # Ensure MCP_API_KEY is not set
    os.environ.pop("MCP_API_KEY", None)
    
    # All endpoints should work without X-API-Key header
    response = client.get("/")
    assert response.status_code == 200
    
    response = client.get("/mcp/state")
    assert response.status_code == 200
    
    response = client.post("/mcp/query", json={"action": "list_users", "params": {}})
    assert response.status_code == 200


def test_auth_required_when_api_key_set(client_with_auth):
    """Test that authentication is required when MCP_API_KEY is set"""
    # Request without API key should fail
    response = client_with_auth.get("/mcp/state")
    assert response.status_code == 401
    assert "Missing X-API-Key header" in response.json()["detail"]


def test_auth_with_valid_api_key(client_with_auth):
    """Test that requests with valid API key are accepted"""
    # Get the API key from the client
    api_key = client_with_auth.api_key
    
    # Request with valid API key
    response = client_with_auth.get(
        "/mcp/state",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_auth_with_invalid_api_key(client_with_auth):
    """Test that requests with invalid API key are rejected"""
    # Request with wrong API key
    response = client_with_auth.get(
        "/mcp/state",
        headers={"X-API-Key": "wrong-api-key"}
    )
    
    assert response.status_code == 403
    assert "Invalid API key" in response.json()["detail"]


def test_auth_all_endpoints_with_valid_key(client_with_auth):
    """Test that all endpoints accept valid API key"""
    api_key = client_with_auth.api_key
    headers = {"X-API-Key": api_key}
    
    # Test all endpoints
    response = client_with_auth.get("/", headers=headers)
    assert response.status_code == 200
    
    response = client_with_auth.get("/mcp/state", headers=headers)
    assert response.status_code == 200
    
    response = client_with_auth.post(
        "/mcp/query",
        json={"action": "list_users", "params": {}},
        headers=headers
    )
    assert response.status_code == 200
    
    response = client_with_auth.get("/mcp/logs", headers=headers)
    assert response.status_code == 200
    
    response = client_with_auth.post("/mcp/reset", headers=headers)
    assert response.status_code == 200


def test_auth_case_sensitive_header(client_with_auth):
    """Test that API key header name is case-insensitive (per HTTP standard)"""
    api_key = client_with_auth.api_key
    
    # HTTP headers are case-insensitive
    # FastAPI/Starlette should handle this automatically
    response = client_with_auth.get(
        "/mcp/state",
        headers={"x-api-key": api_key}  # lowercase
    )
    assert response.status_code == 200


def test_auth_operations_with_valid_key(client_with_auth):
    """Test CRUD operations with authentication"""
    api_key = client_with_auth.api_key
    headers = {"X-API-Key": api_key}
    
    # Add user
    response = client_with_auth.post(
        "/mcp/query",
        json={"action": "add_user", "params": {"username": "testuser"}},
        headers=headers
    )
    assert response.status_code == 200
    
    # List users
    response = client_with_auth.post(
        "/mcp/query",
        json={"action": "list_users", "params": {}},
        headers=headers
    )
    assert response.status_code == 200
    assert "testuser" in response.json()["data"]
    
    # Add task
    response = client_with_auth.post(
        "/mcp/query",
        json={"action": "add_task", "params": {"title": "Test Task"}},
        headers=headers
    )
    assert response.status_code == 200
    
    # Update config
    response = client_with_auth.post(
        "/mcp/query",
        json={"action": "update_config", "params": {"key": "test", "value": "value"}},
        headers=headers
    )
    assert response.status_code == 200
