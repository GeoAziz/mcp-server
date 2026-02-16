"""
Test cases for basic MCP Server endpoints
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test the root health check endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "running"
    assert data["service"] == "MCP Server"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_get_state_empty(client):
    """Test getting state from empty database"""
    response = client.get("/mcp/state")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["users"] == []
    assert data["data"]["tasks"] == []
    assert "config" in data["data"]
    assert "stats" in data["data"]
    assert data["data"]["stats"]["total_users"] == 0
    assert data["data"]["stats"]["total_tasks"] == 0


def test_get_state_with_data(client, sample_users, sample_tasks):
    """Test getting state with data"""
    # Add users
    for user in sample_users:
        response = client.post(
            "/mcp/query",
            json={"action": "add_user", "params": user}
        )
        assert response.status_code == 200
    
    # Add tasks
    for task in sample_tasks:
        response = client.post(
            "/mcp/query",
            json={"action": "add_task", "params": task}
        )
        assert response.status_code == 200
    
    # Get state
    response = client.get("/mcp/state")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]["users"]) == len(sample_users)
    assert len(data["data"]["tasks"]) == len(sample_tasks)
    assert data["data"]["stats"]["total_users"] == len(sample_users)
    assert data["data"]["stats"]["total_tasks"] == len(sample_tasks)


def test_get_state_filter_by_users(client, sample_users):
    """Test filtering state by entity=users"""
    # Add users
    for user in sample_users:
        client.post("/mcp/query", json={"action": "add_user", "params": user})
    
    # Get filtered state
    response = client.get("/mcp/state?entity=users")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "users" in data["data"]
    assert "total" in data["data"]
    assert "count" in data["data"]
    assert data["data"]["total"] == len(sample_users)
    assert len(data["data"]["users"]) == len(sample_users)


def test_get_state_filter_by_tasks(client, sample_tasks):
    """Test filtering state by entity=tasks"""
    # Add tasks
    for task in sample_tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # Get filtered state
    response = client.get("/mcp/state?entity=tasks")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "tasks" in data["data"]
    assert "total" in data["data"]
    assert "count" in data["data"]
    assert data["data"]["total"] == len(sample_tasks)
    assert len(data["data"]["tasks"]) == len(sample_tasks)


def test_get_state_filter_by_status(client, sample_tasks):
    """Test filtering tasks by status"""
    # Add tasks
    for task in sample_tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # Filter by status 'pending'
    response = client.get("/mcp/state?entity=tasks&status=pending")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    pending_tasks = [t for t in sample_tasks if t["status"] == "pending"]
    assert data["data"]["total"] == len(pending_tasks)
    assert data["data"]["filtered_by_status"] == "pending"


def test_get_state_with_pagination(client, sample_users):
    """Test state pagination with limit and offset"""
    # Add users
    for user in sample_users:
        client.post("/mcp/query", json={"action": "add_user", "params": user})
    
    # Get first 2 users
    response = client.get("/mcp/state?entity=users&limit=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["count"] == 2
    assert data["data"]["total"] == len(sample_users)
    
    # Get users with offset
    response = client.get("/mcp/state?entity=users&offset=1&limit=2")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["count"] == 2


def test_get_state_invalid_entity(client):
    """Test getting state with invalid entity parameter"""
    response = client.get("/mcp/state?entity=invalid")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is False
    assert "Invalid entity" in data["message"]


def test_reset_endpoint(client, sample_users, sample_tasks):
    """Test the reset endpoint"""
    # Add some data
    for user in sample_users:
        client.post("/mcp/query", json={"action": "add_user", "params": user})
    
    for task in sample_tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # Verify data exists
    response = client.get("/mcp/state")
    assert len(response.json()["data"]["users"]) > 0
    assert len(response.json()["data"]["tasks"]) > 0
    
    # Reset
    response = client.post("/mcp/reset")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["reset"] is True
    
    # Verify data is cleared
    response = client.get("/mcp/state")
    state_data = response.json()["data"]
    assert len(state_data["users"]) == 0
    assert len(state_data["tasks"]) == 0


def test_logs_endpoint(client):
    """Test the logs endpoint"""
    # Perform some actions to generate logs
    client.post("/mcp/query", json={"action": "list_users", "params": {}})
    client.post("/mcp/query", json={"action": "list_tasks", "params": {}})
    
    # Get logs
    response = client.get("/mcp/logs")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert isinstance(data["data"], list)
    # Should have at least 2 logs from actions above
    assert len(data["data"]) >= 2


def test_logs_endpoint_with_limit(client):
    """Test logs endpoint with limit parameter"""
    # Perform multiple actions
    for i in range(5):
        client.post("/mcp/query", json={"action": "list_users", "params": {}})
    
    # Get logs with limit
    response = client.get("/mcp/logs?limit=3")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]) <= 3
