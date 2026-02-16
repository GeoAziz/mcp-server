"""
Test cases for versioned API endpoints
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check_shows_api_versions(client):
    """Test that health check shows available API versions"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "running"
    assert "api_versions" in data
    assert "planned_versions" in data
    
    # Check v1 is stable
    assert "v1" in data["api_versions"]
    assert data["api_versions"]["v1"]["path"] == "/api/v1"
    assert data["api_versions"]["v1"]["status"] == "stable"
    
    # Check v2 is planned but not implemented
    assert "v2" in data["planned_versions"]
    assert data["planned_versions"]["v2"]["path"] == "/api/v2"
    assert data["planned_versions"]["v2"]["status"] == "not_implemented"


def test_v1_state_endpoint(client):
    """Test v1 state endpoint"""
    response = client.get("/api/v1/state")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    assert "users" in data["data"]
    assert "tasks" in data["data"]


def test_v1_query_endpoint(client, sample_users):
    """Test v1 query endpoint"""
    # Add a user via v1 endpoint
    user = sample_users[0]
    response = client.post(
        "/api/v1/query",
        json={"action": "add_user", "params": user}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["username"] == user["username"]
    assert data["data"]["added"] is True


def test_v1_logs_endpoint(client):
    """Test v1 logs endpoint"""
    response = client.get("/api/v1/logs")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)


def test_v1_reset_endpoint(client):
    """Test v1 reset endpoint"""
    response = client.post("/api/v1/reset")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["reset"] is True


def test_legacy_endpoints_still_work(client, sample_users):
    """Test that legacy /mcp/* endpoints still work for backward compatibility"""
    # Test legacy state endpoint
    response = client.get("/mcp/state")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Test legacy query endpoint
    user = sample_users[0]
    response = client.post(
        "/mcp/query",
        json={"action": "add_user", "params": user}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_v1_state_with_filters(client, sample_users, sample_tasks):
    """Test v1 state endpoint with filters"""
    # Add users
    for user in sample_users:
        client.post("/api/v1/query", json={"action": "add_user", "params": user})
    
    # Add tasks
    for task in sample_tasks:
        client.post("/api/v1/query", json={"action": "add_task", "params": task})
    
    # Test entity filter
    response = client.get("/api/v1/state?entity=tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data["data"]
    assert "total" in data["data"]
    
    # Test pagination
    response = client.get("/api/v1/state?entity=tasks&limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["count"] == 1


def test_v1_all_user_actions(client):
    """Test all user management actions via v1"""
    # List users (should be empty)
    response = client.post("/api/v1/query", json={"action": "list_users", "params": {}})
    assert response.status_code == 200
    assert response.json()["data"] == []
    
    # Add user
    response = client.post(
        "/api/v1/query",
        json={"action": "add_user", "params": {"username": "testuser"}}
    )
    assert response.status_code == 200
    assert response.json()["data"]["added"] is True
    
    # Get user
    response = client.post(
        "/api/v1/query",
        json={"action": "get_user", "params": {"username": "testuser"}}
    )
    assert response.status_code == 200
    assert response.json()["data"]["exists"] is True
    
    # Remove user
    response = client.post(
        "/api/v1/query",
        json={"action": "remove_user", "params": {"username": "testuser"}}
    )
    assert response.status_code == 200
    assert response.json()["data"]["removed"] is True


def test_v1_all_task_actions(client):
    """Test all task management actions via v1"""
    # Add task
    response = client.post(
        "/api/v1/query",
        json={
            "action": "add_task",
            "params": {
                "title": "Test Task",
                "description": "Test Description",
                "priority": "high"
            }
        }
    )
    assert response.status_code == 200
    task_id = response.json()["data"]["id"]
    
    # List tasks
    response = client.post("/api/v1/query", json={"action": "list_tasks", "params": {}})
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    
    # Update task
    response = client.post(
        "/api/v1/query",
        json={
            "action": "update_task",
            "params": {"task_id": task_id, "status": "completed"}
        }
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"
    
    # Search tasks
    response = client.post(
        "/api/v1/query",
        json={"action": "search_tasks", "params": {"query": "Test"}}
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    
    # Delete task
    response = client.post(
        "/api/v1/query",
        json={"action": "delete_task", "params": {"task_id": task_id}}
    )
    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True


def test_v1_config_actions(client):
    """Test config actions via v1"""
    # Update config
    response = client.post(
        "/api/v1/query",
        json={
            "action": "update_config",
            "params": {"key": "test_key", "value": "test_value"}
        }
    )
    assert response.status_code == 200
    assert response.json()["data"]["updated"] is True
    
    # Get specific config
    response = client.post(
        "/api/v1/query",
        json={"action": "get_config", "params": {"key": "test_key"}}
    )
    assert response.status_code == 200
    assert response.json()["data"]["test_key"] == "test_value"
    
    # Get all config
    response = client.post(
        "/api/v1/query",
        json={"action": "get_config", "params": {}}
    )
    assert response.status_code == 200
    assert "test_key" in response.json()["data"]


def test_v1_utility_actions(client):
    """Test utility actions via v1"""
    # Calculate
    response = client.post(
        "/api/v1/query",
        json={
            "action": "calculate",
            "params": {"operation": "sum", "numbers": [1, 2, 3, 4, 5]}
        }
    )
    assert response.status_code == 200
    assert response.json()["data"]["result"] == 15
    
    # Summarize data
    response = client.post(
        "/api/v1/query",
        json={"action": "summarize_data", "params": {}}
    )
    assert response.status_code == 200
    assert "summary" in response.json()["data"]
