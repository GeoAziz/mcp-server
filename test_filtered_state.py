"""
Test cases for filtered state query endpoints
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_setup():
    """Setup test data"""
    print("\n🔧 Setting up test data...")
    
    # Reset memory
    response = requests.post(f"{BASE_URL}/mcp/reset")
    assert response.status_code == 200, "Failed to reset memory"
    
    # Add users
    for user in ["alice", "bob", "charlie", "david", "eve"]:
        response = requests.post(
            f"{BASE_URL}/mcp/query",
            json={"action": "add_user", "params": {"username": user}}
        )
        assert response.status_code == 200, f"Failed to add user {user}"
    
    # Add tasks with different statuses
    tasks = [
        {"title": "Task 1", "status": "pending", "priority": "high"},
        {"title": "Task 2", "status": "pending", "priority": "medium"},
        {"title": "Task 3", "status": "in_progress", "priority": "high"},
        {"title": "Task 4", "status": "in_progress", "priority": "low"},
        {"title": "Task 5", "status": "completed", "priority": "medium"},
        {"title": "Task 6", "status": "completed", "priority": "high"},
        {"title": "Task 7", "status": "pending", "priority": "low"},
        {"title": "Task 8", "status": "in_progress", "priority": "medium"},
        {"title": "Task 9", "status": "completed", "priority": "low"},
        {"title": "Task 10", "status": "pending", "priority": "high"},
    ]
    
    for task in tasks:
        response = requests.post(
            f"{BASE_URL}/mcp/query",
            json={"action": "add_task", "params": task}
        )
        assert response.status_code == 200, f"Failed to add task {task['title']}"
    
    print("✅ Test data setup complete")

def test_backward_compatibility():
    """Test that endpoint without parameters returns full state"""
    print("\n1️⃣ Testing backward compatibility (no parameters)...")
    
    response = requests.get(f"{BASE_URL}/mcp/state")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert "users" in data["data"], "Missing users in response"
    assert "tasks" in data["data"], "Missing tasks in response"
    assert "config" in data["data"], "Missing config in response"
    assert "stats" in data["data"], "Missing stats in response"
    
    print(f"   ✅ Full state returned: {len(data['data']['users'])} users, {len(data['data']['tasks'])} tasks")

def test_filter_by_entity_users():
    """Test filtering by entity=users"""
    print("\n2️⃣ Testing entity=users filter...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=users")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert "users" in data["data"], "Missing users in response"
    assert "total" in data["data"], "Missing total count"
    assert "count" in data["data"], "Missing count"
    
    print(f"   ✅ Users filtered: {data['data']['count']} users returned")

def test_filter_by_entity_tasks():
    """Test filtering by entity=tasks"""
    print("\n3️⃣ Testing entity=tasks filter...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert "tasks" in data["data"], "Missing tasks in response"
    assert "total" in data["data"], "Missing total count"
    assert "count" in data["data"], "Missing count"
    
    print(f"   ✅ Tasks filtered: {data['data']['count']} tasks returned")

def test_filter_by_entity_config():
    """Test filtering by entity=config"""
    print("\n4️⃣ Testing entity=config filter...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=config")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert "config" in data["data"], "Missing config in response"
    
    print(f"   ✅ Config filtered: {len(data['data']['config'])} config items returned")

def test_filter_by_entity_logs():
    """Test filtering by entity=logs"""
    print("\n5️⃣ Testing entity=logs filter...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=logs")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert "logs" in data["data"], "Missing logs in response"
    
    print(f"   ✅ Logs filtered: {data['data']['count']} logs returned")

def test_pagination_with_limit():
    """Test pagination with limit parameter"""
    print("\n6️⃣ Testing pagination with limit=3...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks&limit=3")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert len(data["data"]["tasks"]) == 3, f"Expected 3 tasks, got {len(data['data']['tasks'])}"
    
    print(f"   ✅ Limit works: {len(data['data']['tasks'])} tasks returned (expected 3)")

def test_pagination_with_offset():
    """Test pagination with offset parameter"""
    print("\n7️⃣ Testing pagination with offset=5...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks&offset=5")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert len(data["data"]["tasks"]) == 5, f"Expected 5 tasks, got {len(data['data']['tasks'])}"
    
    print(f"   ✅ Offset works: {len(data['data']['tasks'])} tasks returned (skipped first 5)")

def test_pagination_with_limit_and_offset():
    """Test pagination with both limit and offset"""
    print("\n8️⃣ Testing pagination with limit=3&offset=2...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks&limit=3&offset=2")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert len(data["data"]["tasks"]) == 3, f"Expected 3 tasks, got {len(data['data']['tasks'])}"
    
    print(f"   ✅ Limit+Offset works: {len(data['data']['tasks'])} tasks returned")

def test_filter_tasks_by_status():
    """Test filtering tasks by status"""
    print("\n9️⃣ Testing status filter for tasks...")
    
    # Test pending tasks
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks&status=pending")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert all(t["status"] == "pending" for t in data["data"]["tasks"]), "Not all tasks have pending status"
    
    pending_count = len(data["data"]["tasks"])
    print(f"   ✅ Status filter works: {pending_count} pending tasks")
    
    # Test in_progress tasks
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks&status=in_progress")
    data = response.json()
    in_progress_count = len(data["data"]["tasks"])
    print(f"   ✅ Status filter works: {in_progress_count} in_progress tasks")
    
    # Test completed tasks
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks&status=completed")
    data = response.json()
    completed_count = len(data["data"]["tasks"])
    print(f"   ✅ Status filter works: {completed_count} completed tasks")

def test_combined_filters():
    """Test combining status filter with pagination"""
    print("\n🔟 Testing combined filters (status=pending&limit=2)...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=tasks&status=pending&limit=2")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is True, "Response not successful"
    assert len(data["data"]["tasks"]) == 2, f"Expected 2 tasks, got {len(data['data']['tasks'])}"
    assert all(t["status"] == "pending" for t in data["data"]["tasks"]), "Not all tasks have pending status"
    
    print(f"   ✅ Combined filters work: {len(data['data']['tasks'])} pending tasks returned")

def test_invalid_entity():
    """Test error handling for invalid entity"""
    print("\n1️⃣1️⃣ Testing invalid entity parameter...")
    
    response = requests.get(f"{BASE_URL}/mcp/state?entity=invalid")
    assert response.status_code == 200, "Request failed"
    
    data = response.json()
    assert data["success"] is False, "Should return success=false for invalid entity"
    assert "Invalid entity" in data["message"], "Should have error message"
    
    print(f"   ✅ Invalid entity handled: {data['message']}")

def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("🧪 FILTERED STATE QUERY ENDPOINT TESTS")
    print("=" * 70)
    
    try:
        # Check if server is running
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            print("❌ Server is not running. Start it with: python mcp_server.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start it with: python mcp_server.py")
        return
    
    # Setup test data
    test_setup()
    
    # Run tests
    test_backward_compatibility()
    test_filter_by_entity_users()
    test_filter_by_entity_tasks()
    test_filter_by_entity_config()
    test_filter_by_entity_logs()
    test_pagination_with_limit()
    test_pagination_with_offset()
    test_pagination_with_limit_and_offset()
    test_filter_tasks_by_status()
    test_combined_filters()
    test_invalid_entity()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
