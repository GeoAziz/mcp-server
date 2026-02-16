"""
Test cases for task management operations
"""

import pytest


def test_list_tasks_empty(client):
    """Test listing tasks when database is empty"""
    response = client.post(
        "/mcp/query",
        json={"action": "list_tasks", "params": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"] == []


def test_add_task(client):
    """Test adding a new task"""
    response = client.post(
        "/mcp/query",
        json={
            "action": "add_task",
            "params": {
                "title": "Test Task",
                "description": "Test description",
                "priority": "high",
                "status": "pending"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["title"] == "Test Task"
    assert data["data"]["description"] == "Test description"
    assert data["data"]["priority"] == "high"
    assert data["data"]["status"] == "pending"
    assert "id" in data["data"]
    assert "created_at" in data["data"]
    assert "updated_at" in data["data"]


def test_add_task_minimal(client):
    """Test adding a task with only required fields"""
    response = client.post(
        "/mcp/query",
        json={
            "action": "add_task",
            "params": {
                "title": "Minimal Task"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["title"] == "Minimal Task"
    # Check defaults
    assert data["data"]["priority"] == "medium"
    assert data["data"]["status"] == "pending"


def test_add_task_missing_title(client):
    """Test adding a task without title"""
    response = client.post(
        "/mcp/query",
        json={"action": "add_task", "params": {}}
    )
    
    assert response.status_code == 400
    assert "title is required" in response.json()["detail"].lower()


def test_list_tasks_with_data(client, sample_tasks):
    """Test listing tasks after adding them"""
    # Add tasks
    for task in sample_tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # List tasks
    response = client.post(
        "/mcp/query",
        json={"action": "list_tasks", "params": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]) == len(sample_tasks)


def test_list_tasks_filter_by_status(client, sample_tasks):
    """Test listing tasks filtered by status"""
    # Add tasks
    for task in sample_tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # Filter by status
    response = client.post(
        "/mcp/query",
        json={"action": "list_tasks", "params": {"status": "pending"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    # All returned tasks should have status "pending"
    for task in data["data"]:
        assert task["status"] == "pending"
    
    # Count should match sample data
    pending_count = sum(1 for t in sample_tasks if t["status"] == "pending")
    assert len(data["data"]) == pending_count


def test_list_tasks_filter_by_assigned_to(client, sample_tasks):
    """Test listing tasks filtered by assignee"""
    # Add tasks
    for task in sample_tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # Filter by assignee
    response = client.post(
        "/mcp/query",
        json={"action": "list_tasks", "params": {"assigned_to": "alice"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    # All returned tasks should be assigned to alice
    for task in data["data"]:
        assert task["assigned_to"] == "alice"


def test_update_task(client):
    """Test updating a task"""
    # Add task
    add_response = client.post(
        "/mcp/query",
        json={
            "action": "add_task",
            "params": {"title": "Original Title", "status": "pending"}
        }
    )
    task_id = add_response.json()["data"]["id"]
    
    # Update task
    response = client.post(
        "/mcp/query",
        json={
            "action": "update_task",
            "params": {
                "task_id": task_id,
                "title": "Updated Title",
                "status": "in_progress",
                "priority": "high"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["id"] == task_id
    assert data["data"]["title"] == "Updated Title"
    assert data["data"]["status"] == "in_progress"
    assert data["data"]["priority"] == "high"


def test_update_task_partial(client):
    """Test updating only some fields of a task"""
    # Add task
    add_response = client.post(
        "/mcp/query",
        json={
            "action": "add_task",
            "params": {
                "title": "Test Task",
                "description": "Original description",
                "status": "pending"
            }
        }
    )
    task_id = add_response.json()["data"]["id"]
    
    # Update only status
    response = client.post(
        "/mcp/query",
        json={
            "action": "update_task",
            "params": {
                "task_id": task_id,
                "status": "completed"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["status"] == "completed"
    # Other fields should remain unchanged
    assert data["data"]["title"] == "Test Task"
    assert data["data"]["description"] == "Original description"


def test_update_task_not_found(client):
    """Test updating a task that doesn't exist"""
    response = client.post(
        "/mcp/query",
        json={
            "action": "update_task",
            "params": {"task_id": 99999, "title": "Updated"}
        }
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_update_task_missing_id(client):
    """Test updating a task without task_id"""
    response = client.post(
        "/mcp/query",
        json={"action": "update_task", "params": {"title": "Updated"}}
    )
    
    assert response.status_code == 400
    assert "task_id is required" in response.json()["detail"].lower()


def test_delete_task(client):
    """Test deleting a task"""
    # Add task
    add_response = client.post(
        "/mcp/query",
        json={"action": "add_task", "params": {"title": "Task to Delete"}}
    )
    task_id = add_response.json()["data"]["id"]
    
    # Delete task
    response = client.post(
        "/mcp/query",
        json={"action": "delete_task", "params": {"task_id": task_id}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["task_id"] == task_id
    assert data["data"]["deleted"] is True
    
    # Verify task is deleted
    list_response = client.post(
        "/mcp/query",
        json={"action": "list_tasks", "params": {}}
    )
    tasks = list_response.json()["data"]
    assert not any(t["id"] == task_id for t in tasks)


def test_delete_task_not_found(client):
    """Test deleting a task that doesn't exist"""
    response = client.post(
        "/mcp/query",
        json={"action": "delete_task", "params": {"task_id": 99999}}
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_delete_task_missing_id(client):
    """Test deleting a task without task_id"""
    response = client.post(
        "/mcp/query",
        json={"action": "delete_task", "params": {}}
    )
    
    assert response.status_code == 400
    assert "task_id is required" in response.json()["detail"].lower()


def test_search_tasks(client):
    """Test searching tasks by query string"""
    # Add tasks with different content
    tasks = [
        {"title": "Python development", "description": "Write Python code"},
        {"title": "JavaScript project", "description": "Build web app"},
        {"title": "Code review", "description": "Review Python PR"},
    ]
    
    for task in tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # Search for "Python"
    response = client.post(
        "/mcp/query",
        json={"action": "search_tasks", "params": {"query": "Python"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    # Should find 2 tasks containing "Python"
    assert len(data["data"]) == 2
    
    # Verify all results contain the search term
    for task in data["data"]:
        assert "python" in task["title"].lower() or "python" in task["description"].lower()


def test_search_tasks_case_insensitive(client):
    """Test that task search is case-insensitive"""
    # Add task
    client.post(
        "/mcp/query",
        json={"action": "add_task", "params": {"title": "Python DEVELOPMENT"}}
    )
    
    # Search with lowercase
    response = client.post(
        "/mcp/query",
        json={"action": "search_tasks", "params": {"query": "python"}}
    )
    
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_search_tasks_no_results(client):
    """Test searching tasks with no matching results"""
    # Add tasks
    client.post(
        "/mcp/query",
        json={"action": "add_task", "params": {"title": "Test Task"}}
    )
    
    # Search for non-existent term
    response = client.post(
        "/mcp/query",
        json={"action": "search_tasks", "params": {"query": "nonexistent"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"] == []


def test_search_tasks_empty_query(client, sample_tasks):
    """Test searching with empty query returns all tasks"""
    # Add tasks
    for task in sample_tasks:
        client.post("/mcp/query", json={"action": "add_task", "params": task})
    
    # Search with empty query
    response = client.post(
        "/mcp/query",
        json={"action": "search_tasks", "params": {"query": ""}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]) == len(sample_tasks)
