"""
Test cases for error handling and edge cases
"""

import pytest


def test_invalid_action(client):
    """Test handling of invalid/unknown action"""
    response = client.post(
        "/mcp/query",
        json={"action": "invalid_action", "params": {}}
    )
    
    assert response.status_code == 400
    assert "unknown action" in response.json()["detail"].lower()


def test_missing_action(client):
    """Test handling of missing action field"""
    response = client.post(
        "/mcp/query",
        json={"params": {}}
    )
    
    # FastAPI will return 422 for validation error
    assert response.status_code == 422


def test_invalid_json(client):
    """Test handling of invalid JSON payload"""
    response = client.post(
        "/mcp/query",
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422


def test_missing_required_params_add_user(client):
    """Test error when required params are missing for add_user"""
    response = client.post(
        "/mcp/query",
        json={"action": "add_user", "params": {}}
    )
    
    assert response.status_code == 400
    assert "username is required" in response.json()["detail"].lower()


def test_missing_required_params_add_task(client):
    """Test error when required params are missing for add_task"""
    response = client.post(
        "/mcp/query",
        json={"action": "add_task", "params": {}}
    )
    
    assert response.status_code == 400
    assert "title is required" in response.json()["detail"].lower()


def test_missing_required_params_update_task(client):
    """Test error when required params are missing for update_task"""
    response = client.post(
        "/mcp/query",
        json={"action": "update_task", "params": {"title": "New Title"}}
    )
    
    assert response.status_code == 400
    assert "task_id is required" in response.json()["detail"].lower()


def test_missing_required_params_delete_task(client):
    """Test error when required params are missing for delete_task"""
    response = client.post(
        "/mcp/query",
        json={"action": "delete_task", "params": {}}
    )
    
    assert response.status_code == 400
    assert "task_id is required" in response.json()["detail"].lower()


def test_missing_required_params_update_config(client):
    """Test error when required params are missing for update_config"""
    response = client.post(
        "/mcp/query",
        json={"action": "update_config", "params": {"value": "test"}}
    )
    
    assert response.status_code == 400
    assert "key is required" in response.json()["detail"].lower()


def test_resource_not_found_user(client):
    """Test error when user resource is not found"""
    response = client.post(
        "/mcp/query",
        json={"action": "remove_user", "params": {"username": "nonexistent"}}
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_resource_not_found_task(client):
    """Test error when task resource is not found"""
    response = client.post(
        "/mcp/query",
        json={"action": "update_task", "params": {"task_id": 99999, "title": "Test"}}
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_duplicate_user(client):
    """Test error when adding duplicate user"""
    # Add user
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


def test_empty_params(client):
    """Test actions with empty params"""
    # Some actions work with empty params
    response = client.post(
        "/mcp/query",
        json={"action": "list_users", "params": {}}
    )
    assert response.status_code == 200
    
    response = client.post(
        "/mcp/query",
        json={"action": "list_tasks", "params": {}}
    )
    assert response.status_code == 200
    
    response = client.post(
        "/mcp/query",
        json={"action": "get_config", "params": {}}
    )
    assert response.status_code == 200


def test_null_params(client):
    """Test action with null params (should default to empty dict)"""
    response = client.post(
        "/mcp/query",
        json={"action": "list_users"}  # params omitted
    )
    
    assert response.status_code == 200


def test_extra_params_ignored(client):
    """Test that extra/unknown params are ignored gracefully"""
    response = client.post(
        "/mcp/query",
        json={
            "action": "add_user",
            "params": {
                "username": "testuser",
                "unknown_param": "should_be_ignored"
            }
        }
    )
    
    # Should succeed, ignoring unknown param
    assert response.status_code == 200


def test_invalid_filter_entity(client):
    """Test invalid entity filter in state endpoint"""
    response = client.get("/mcp/state?entity=invalid_entity")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "invalid entity" in data["message"].lower()


def test_negative_limit(client):
    """Test state endpoint with negative limit"""
    # SQLAlchemy should handle this gracefully
    response = client.get("/mcp/state?entity=users&limit=-1")
    
    # Should still work (backend handles invalid limits)
    assert response.status_code == 200


def test_negative_offset(client):
    """Test state endpoint with negative offset"""
    response = client.get("/mcp/state?entity=users&offset=-1")
    
    # Should still work (backend handles invalid offsets)
    assert response.status_code == 200


def test_very_large_limit(client):
    """Test state endpoint with very large limit"""
    response = client.get("/mcp/state?entity=users&limit=999999")
    
    # Should work but return only available data
    assert response.status_code == 200


def test_string_for_numeric_param(client):
    """Test passing string where number is expected"""
    # FastAPI should handle type conversion or validation
    response = client.get("/mcp/state?entity=users&limit=abc")
    
    # Should return validation error
    assert response.status_code == 422


def test_malformed_query_string(client):
    """Test malformed query parameters"""
    response = client.get("/mcp/state?entity")
    
    # Should handle gracefully
    assert response.status_code in [200, 422]


def test_response_format_consistency(client):
    """Test that all successful responses follow QueryResponse format"""
    # Test various endpoints
    endpoints_to_test = [
        ("/mcp/state", "get", None),
        ("/mcp/query", "post", {"action": "list_users", "params": {}}),
        ("/mcp/logs", "get", None),
        ("/mcp/reset", "post", None),
    ]
    
    for endpoint, method, body in endpoints_to_test:
        if method == "get":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, json=body)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check QueryResponse format
        assert "success" in data
        assert "data" in data
        assert "timestamp" in data
        assert isinstance(data["success"], bool)


def test_concurrent_operations(client):
    """Test that concurrent operations don't cause issues"""
    # Add multiple users in sequence (simulating concurrent operations)
    for i in range(10):
        response = client.post(
            "/mcp/query",
            json={"action": "add_user", "params": {"username": f"user{i}"}}
        )
        assert response.status_code == 200
    
    # Verify all users were added
    response = client.post(
        "/mcp/query",
        json={"action": "list_users", "params": {}}
    )
    assert len(response.json()["data"]) == 10
