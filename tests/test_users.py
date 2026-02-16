"""
Test cases for user management operations
"""

import pytest


def test_list_users_empty(client):
    """Test listing users when database is empty"""
    response = client.post(
        "/mcp/query",
        json={"action": "list_users", "params": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"] == []


def test_add_user(client):
    """Test adding a new user"""
    response = client.post(
        "/mcp/query",
        json={
            "action": "add_user",
            "params": {
                "username": "testuser",
                "role": "admin"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["username"] == "testuser"
    assert data["data"]["added"] is True


def test_add_user_duplicate(client):
    """Test adding a user that already exists"""
    # Add user first time
    client.post(
        "/mcp/query",
        json={"action": "add_user", "params": {"username": "testuser"}}
    )
    
    # Try to add same user again
    response = client.post(
        "/mcp/query",
        json={"action": "add_user", "params": {"username": "testuser"}}
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_add_user_missing_username(client):
    """Test adding a user without username"""
    response = client.post(
        "/mcp/query",
        json={"action": "add_user", "params": {}}
    )
    
    assert response.status_code == 400
    assert "username is required" in response.json()["detail"].lower()


def test_list_users_with_data(client, sample_users):
    """Test listing users after adding them"""
    # Add users
    for user in sample_users:
        client.post("/mcp/query", json={"action": "add_user", "params": user})
    
    # List users
    response = client.post(
        "/mcp/query",
        json={"action": "list_users", "params": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]) == len(sample_users)
    
    # Check all usernames are present
    usernames = set(data["data"])
    expected_usernames = {u["username"] for u in sample_users}
    assert usernames == expected_usernames


def test_remove_user(client):
    """Test removing a user"""
    # Add user
    client.post(
        "/mcp/query",
        json={"action": "add_user", "params": {"username": "testuser"}}
    )
    
    # Remove user
    response = client.post(
        "/mcp/query",
        json={"action": "remove_user", "params": {"username": "testuser"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["username"] == "testuser"
    assert data["data"]["removed"] is True
    
    # Verify user is removed
    response = client.post(
        "/mcp/query",
        json={"action": "list_users", "params": {}}
    )
    assert "testuser" not in response.json()["data"]


def test_remove_user_not_found(client):
    """Test removing a user that doesn't exist"""
    response = client.post(
        "/mcp/query",
        json={"action": "remove_user", "params": {"username": "nonexistent"}}
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_remove_user_missing_username(client):
    """Test removing a user without username"""
    response = client.post(
        "/mcp/query",
        json={"action": "remove_user", "params": {}}
    )
    
    assert response.status_code == 400
    assert "username is required" in response.json()["detail"].lower()


def test_get_user_exists(client):
    """Test getting details of an existing user"""
    # Add user
    client.post(
        "/mcp/query",
        json={"action": "add_user", "params": {"username": "testuser"}}
    )
    
    # Get user
    response = client.post(
        "/mcp/query",
        json={"action": "get_user", "params": {"username": "testuser"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["username"] == "testuser"
    assert data["data"]["exists"] is True
    assert "task_count" in data["data"]
    assert "tasks" in data["data"]


def test_get_user_not_exists(client):
    """Test getting details of a non-existent user"""
    response = client.post(
        "/mcp/query",
        json={"action": "get_user", "params": {"username": "nonexistent"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["username"] == "nonexistent"
    assert data["data"]["exists"] is False


def test_get_user_with_tasks(client):
    """Test getting user details including assigned tasks"""
    # Add user
    client.post(
        "/mcp/query",
        json={"action": "add_user", "params": {"username": "testuser"}}
    )
    
    # Add tasks assigned to user
    for i in range(3):
        client.post(
            "/mcp/query",
            json={
                "action": "add_task",
                "params": {
                    "title": f"Task {i}",
                    "assigned_to": "testuser"
                }
            }
        )
    
    # Get user
    response = client.post(
        "/mcp/query",
        json={"action": "get_user", "params": {"username": "testuser"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["task_count"] == 3
    assert len(data["data"]["tasks"]) == 3
    
    # Verify all tasks are assigned to testuser
    for task in data["data"]["tasks"]:
        assert task["assigned_to"] == "testuser"
