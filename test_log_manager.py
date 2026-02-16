"""
Test cases for LogManager - Structured logging with configurable retention
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_manager import LogManager


def test_log_structure():
    """Test that logs have correct structure with all required fields"""
    print("\n📝 Testing log structure...")
    
    log_mgr = LogManager(max_logs=100)
    
    # Create a log entry
    entry = log_mgr.log(
        action="test_action",
        payload={"key": "value"},
        status="success"
    )
    
    # Verify structure
    assert "timestamp" in entry, "Missing timestamp"
    assert "action" in entry, "Missing action"
    assert "payload" in entry, "Missing payload"
    assert "status" in entry, "Missing status"
    
    # Verify values
    assert entry["action"] == "test_action", f"Unexpected action: {entry['action']}"
    assert entry["payload"] == {"key": "value"}, f"Unexpected payload: {entry['payload']}"
    assert entry["status"] == "success", f"Unexpected status: {entry['status']}"
    
    # Verify timestamp format (ISO 8601)
    try:
        datetime.fromisoformat(entry["timestamp"])
    except ValueError:
        assert False, f"Invalid timestamp format: {entry['timestamp']}"
    
    print("   ✅ Log structure is correct")
    print(f"   Example entry: {entry}")


def test_retention_limit():
    """Test that retention limit is enforced"""
    print("\n🗂️  Testing retention limit enforcement...")
    
    max_logs = 50
    log_mgr = LogManager(max_logs=max_logs)
    
    # Add more logs than the limit
    num_logs = 100
    for i in range(num_logs):
        log_mgr.log(
            action=f"action_{i}",
            payload={"index": i},
            status="success"
        )
    
    # Check that only max_logs are retained
    count = log_mgr.get_log_count()
    assert count == max_logs, f"Expected {max_logs} logs, got {count}"
    
    # Verify that the oldest logs were removed (should start from index 50)
    logs = log_mgr.get_logs()
    first_log = logs[0]
    last_log = logs[-1]
    
    assert first_log["action"] == "action_50", f"Expected action_50, got {first_log['action']}"
    assert last_log["action"] == "action_99", f"Expected action_99, got {last_log['action']}"
    
    print(f"   ✅ Retention limit enforced: {count}/{max_logs} logs")
    print(f"   First log: {first_log['action']}")
    print(f"   Last log: {last_log['action']}")


def test_log_retrieval():
    """Test log retrieval with limit and offset"""
    print("\n📤 Testing log retrieval...")
    
    log_mgr = LogManager(max_logs=100)
    
    # Add 10 logs
    for i in range(10):
        log_mgr.log(
            action=f"action_{i}",
            payload={"index": i},
            status="success"
        )
    
    # Test getting all logs
    all_logs = log_mgr.get_logs()
    assert len(all_logs) == 10, f"Expected 10 logs, got {len(all_logs)}"
    
    # Test getting limited logs (last 5)
    limited_logs = log_mgr.get_logs(limit=5)
    assert len(limited_logs) == 5, f"Expected 5 logs, got {len(limited_logs)}"
    assert limited_logs[-1]["action"] == "action_9", "Should get most recent logs"
    assert limited_logs[0]["action"] == "action_5", "Should start from action_5"
    
    # Test with offset
    offset_logs = log_mgr.get_logs(limit=3, offset=2)
    assert len(offset_logs) == 3, f"Expected 3 logs, got {len(offset_logs)}"
    assert offset_logs[-1]["action"] == "action_7", "Should skip last 2 logs"
    
    print("   ✅ Log retrieval working correctly")
    print(f"   All logs: {len(all_logs)}")
    print(f"   Limited logs (5): {[log['action'] for log in limited_logs]}")
    print(f"   Offset logs (3, skip 2): {[log['action'] for log in offset_logs]}")


def test_log_filtering():
    """Test filtering logs by action and status"""
    print("\n🔍 Testing log filtering...")
    
    log_mgr = LogManager(max_logs=100)
    
    # Add logs with different actions and statuses
    log_mgr.log(action="add_user", payload={"user": "alice"}, status="success")
    log_mgr.log(action="add_task", payload={"task": "test"}, status="success")
    log_mgr.log(action="add_user", payload={"user": "bob"}, status="error")
    log_mgr.log(action="delete_task", payload={"task_id": 1}, status="success")
    log_mgr.log(action="add_user", payload={"user": "charlie"}, status="success")
    
    # Test filtering by action
    user_logs = log_mgr.get_logs_by_action("add_user")
    assert len(user_logs) == 3, f"Expected 3 add_user logs, got {len(user_logs)}"
    
    # Test filtering by status
    error_logs = log_mgr.get_logs_by_status("error")
    assert len(error_logs) == 1, f"Expected 1 error log, got {len(error_logs)}"
    assert error_logs[0]["action"] == "add_user", "Error log should be add_user"
    
    success_logs = log_mgr.get_logs_by_status("success")
    assert len(success_logs) == 4, f"Expected 4 success logs, got {len(success_logs)}"
    
    print("   ✅ Log filtering working correctly")
    print(f"   add_user logs: {len(user_logs)}")
    print(f"   error logs: {len(error_logs)}")
    print(f"   success logs: {len(success_logs)}")


def test_default_payload_and_status():
    """Test that payload and status have sensible defaults"""
    print("\n⚙️  Testing default values...")
    
    log_mgr = LogManager(max_logs=100)
    
    # Log with minimal parameters
    entry = log_mgr.log(action="test_action")
    
    assert entry["payload"] == {}, "Default payload should be empty dict"
    assert entry["status"] == "success", "Default status should be success"
    
    print("   ✅ Default values working correctly")
    print(f"   Default payload: {entry['payload']}")
    print(f"   Default status: {entry['status']}")


def test_configurable_retention_from_env():
    """Test that retention can be configured via environment variable"""
    print("\n🔧 Testing environment variable configuration...")
    
    # Set environment variable
    os.environ["MCP_LOG_RETENTION"] = "25"
    
    log_mgr = LogManager()
    
    # Add 50 logs
    for i in range(50):
        log_mgr.log(action=f"action_{i}", payload={"index": i})
    
    # Should only keep 25
    count = log_mgr.get_log_count()
    assert count == 25, f"Expected 25 logs from env config, got {count}"
    
    # Clean up
    del os.environ["MCP_LOG_RETENTION"]
    
    print("   ✅ Environment variable configuration working")
    print(f"   Logs retained: {count}")


def run_all_tests():
    """Run all test cases"""
    print("=" * 60)
    print("Running LogManager Tests")
    print("=" * 60)
    
    try:
        test_log_structure()
        test_retention_limit()
        test_log_retrieval()
        test_log_filtering()
        test_default_payload_and_status()
        test_configurable_retention_from_env()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    
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
