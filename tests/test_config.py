"""
Test cases for configuration management operations
"""

import pytest


def test_get_config_all(client):
    """Test getting all configuration values"""
    response = client.post(
        "/mcp/query",
        json={"action": "get_config", "params": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert isinstance(data["data"], dict)


def test_get_config_specific_key(client):
    """Test getting a specific configuration value"""
    # First, set a config value
    client.post(
        "/mcp/query",
        json={
            "action": "update_config",
            "params": {"key": "test_key", "value": "test_value"}
        }
    )
    
    # Get specific config
    response = client.post(
        "/mcp/query",
        json={"action": "get_config", "params": {"key": "test_key"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["test_key"] == "test_value"


def test_get_config_nonexistent_key(client):
    """Test getting a configuration key that doesn't exist"""
    response = client.post(
        "/mcp/query",
        json={"action": "get_config", "params": {"key": "nonexistent_key"}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["nonexistent_key"] is None


def test_update_config_new_key(client):
    """Test updating (creating) a new configuration key"""
    response = client.post(
        "/mcp/query",
        json={
            "action": "update_config",
            "params": {"key": "new_key", "value": "new_value"}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["new_key"] == "new_value"
    assert data["data"]["updated"] is True
    
    # Verify it was saved
    get_response = client.post(
        "/mcp/query",
        json={"action": "get_config", "params": {"key": "new_key"}}
    )
    assert get_response.json()["data"]["new_key"] == "new_value"


def test_update_config_existing_key(client):
    """Test updating an existing configuration key"""
    # Create initial config
    client.post(
        "/mcp/query",
        json={
            "action": "update_config",
            "params": {"key": "test_key", "value": "initial_value"}
        }
    )
    
    # Update the same key
    response = client.post(
        "/mcp/query",
        json={
            "action": "update_config",
            "params": {"key": "test_key", "value": "updated_value"}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["test_key"] == "updated_value"
    assert data["data"]["updated"] is True
    
    # Verify it was updated
    get_response = client.post(
        "/mcp/query",
        json={"action": "get_config", "params": {"key": "test_key"}}
    )
    assert get_response.json()["data"]["test_key"] == "updated_value"


def test_update_config_missing_key(client):
    """Test updating config without providing key"""
    response = client.post(
        "/mcp/query",
        json={"action": "update_config", "params": {"value": "some_value"}}
    )
    
    assert response.status_code == 400
    assert "key is required" in response.json()["detail"].lower()


def test_update_config_various_types(client):
    """Test updating config with various data types"""
    test_values = [
        ("string_key", "string_value"),
        ("number_key", 42),
        ("boolean_key", True),
        ("list_key", [1, 2, 3]),
        ("dict_key", {"nested": "value"}),
    ]
    
    for key, value in test_values:
        response = client.post(
            "/mcp/query",
            json={
                "action": "update_config",
                "params": {"key": key, "value": value}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"][key] == value


def test_update_config_null_value(client):
    """Test updating config with null value"""
    response = client.post(
        "/mcp/query",
        json={
            "action": "update_config",
            "params": {"key": "null_key", "value": None}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["data"]["null_key"] is None
    assert data["data"]["updated"] is True


def test_get_all_config_after_updates(client):
    """Test getting all config after multiple updates"""
    # Update multiple config values
    configs = {
        "key1": "value1",
        "key2": 100,
        "key3": True,
    }
    
    for key, value in configs.items():
        client.post(
            "/mcp/query",
            json={
                "action": "update_config",
                "params": {"key": key, "value": value}
            }
        )
    
    # Get all config
    response = client.post(
        "/mcp/query",
        json={"action": "get_config", "params": {}}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    # Check that all our config values are present
    for key, value in configs.items():
        assert key in data["data"]
        assert data["data"][key] == value
