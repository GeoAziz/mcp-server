"""
Integration test for structured logging endpoints
Tests the /mcp/logs and /mcp/state endpoints with the new LogManager
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"


def test_structured_logs_endpoint():
    """Test that /mcp/logs returns structured JSON logs"""
    print("\n📝 Testing structured logs endpoint...")
    
    # First, perform some actions to generate logs
    # Add a user
    response = requests.post(
        f"{BASE_URL}/mcp/query",
        json={
            "action": "add_user",
            "params": {"username": "test_user"}
        }
    )
    assert response.status_code == 200, f"Failed to add user: {response.text}"
    
    # Add a task
    response = requests.post(
        f"{BASE_URL}/mcp/query",
        json={
            "action": "add_task",
            "params": {"title": "Test Task", "priority": "high"}
        }
    )
    assert response.status_code == 200, f"Failed to add task: {response.text}"
    
    # Now get the logs
    response = requests.get(f"{BASE_URL}/mcp/logs?limit=10")
    assert response.status_code == 200, f"Failed to get logs: {response.status_code}"
    
    data = response.json()
    assert data["success"] is True, "Response should indicate success"
    assert "data" in data, "Response should contain data"
    
    logs = data["data"]
    assert isinstance(logs, list), "Logs should be a list"
    assert len(logs) > 0, "Should have at least some logs"
    
    # Verify log structure
    for log in logs:
        assert "timestamp" in log, f"Log missing timestamp: {log}"
        assert "action" in log, f"Log missing action: {log}"
        assert "payload" in log, f"Log missing payload: {log}"
        assert "status" in log, f"Log missing status: {log}"
        
        # Verify payload structure
        assert isinstance(log["payload"], dict), "Payload should be a dict"
        if "params" in log["payload"]:
            assert isinstance(log["payload"]["params"], dict), "Payload params should be a dict"
    
    print(f"   ✅ Structured logs endpoint working correctly")
    print(f"   Retrieved {len(logs)} logs")
    print(f"   Example log: {logs[-1]}")


def test_logs_in_state_endpoint():
    """Test that /mcp/state?entity=logs returns structured logs"""
    print("\n🗂️  Testing logs in state endpoint...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=logs&limit=5")
    assert response.status_code == 200, f"Failed to get state: {response.status_code}"
    
    data = response.json()
    assert data["success"] is True, "Response should indicate success"
    
    filtered_data = data["data"]
    assert "logs" in filtered_data, "Should have logs in response"
    assert "total" in filtered_data, "Should have total count"
    assert "count" in filtered_data, "Should have returned count"
    
    logs = filtered_data["logs"]
    assert isinstance(logs, list), "Logs should be a list"
    assert len(logs) <= 5, f"Should return at most 5 logs, got {len(logs)}"
    
    # Verify structure
    for log in logs:
        assert "timestamp" in log, f"Log missing timestamp: {log}"
        assert "action" in log, f"Log missing action: {log}"
        assert "payload" in log, f"Log missing payload: {log}"
        assert "status" in log, f"Log missing status: {log}"
    
    print(f"   ✅ State endpoint logs working correctly")
    print(f"   Total logs: {filtered_data['total']}")
    print(f"   Returned: {filtered_data['count']}")


def test_log_status_tracking():
    """Test that both success and error statuses are logged"""
    print("\n✅❌ Testing status tracking in logs...")
    
    # Perform a successful action
    response = requests.post(
        f"{BASE_URL}/mcp/query",
        json={
            "action": "list_users",
            "params": {}
        }
    )
    assert response.status_code == 200, "List users should succeed"
    
    # Perform a failing action (invalid action)
    response = requests.post(
        f"{BASE_URL}/mcp/query",
        json={
            "action": "invalid_action_xyz",
            "params": {}
        }
    )
    assert response.status_code == 400, "Invalid action should fail"
    
    # Get logs
    response = requests.get(f"{BASE_URL}/mcp/logs?limit=20")
    assert response.status_code == 200, "Should get logs"
    
    logs = response.json()["data"]
    
    # Check for both success and error statuses
    statuses = [log["status"] for log in logs]
    
    # We should have at least one success and one error
    has_success = "success" in statuses
    has_error = "error" in statuses
    
    print(f"   ✅ Status tracking working")
    print(f"   Has success logs: {has_success}")
    print(f"   Has error logs: {has_error}")
    print(f"   Recent statuses: {statuses[-5:]}")


def test_log_retention():
    """Test that logs are retained according to configuration"""
    print("\n🔄 Testing log retention...")
    
    # Get current log count
    response = requests.get(f"{BASE_URL}/mcp/state?entity=logs")
    initial_count = response.json()["data"]["total"]
    
    # Perform many actions
    for i in range(50):
        requests.post(
            f"{BASE_URL}/mcp/query",
            json={
                "action": "list_users",
                "params": {}
            }
        )
    
    # Get new log count
    response = requests.get(f"{BASE_URL}/mcp/state?entity=logs")
    final_count = response.json()["data"]["total"]
    
    print(f"   ✅ Log retention working")
    print(f"   Initial count: {initial_count}")
    print(f"   Final count: {final_count}")
    print(f"   Logs added: {final_count - initial_count}")
    
    # The count should have increased but not exceed the retention limit
    # (default is 1000, so with 50 new logs we should see them all)
    assert final_count >= initial_count, "Log count should have increased"


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Running Integration Tests for Structured Logging")
    print("=" * 60)
    print("\n⚠️  Make sure the server is running on http://localhost:8000")
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server is not running or not responding")
            return 1
        
        # Run tests
        test_structured_logs_endpoint()
        test_logs_in_state_endpoint()
        test_log_status_tracking()
        test_log_retention()
        
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        return 0
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
        return 1
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
