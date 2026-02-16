"""
MCP Client Example
Shows how AI agents/scripts interact with the MCP server
"""

import requests
from typing import Dict, Any, List
import json

class MCPClient:
    """Client for interacting with MCP Server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def query(self, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a query to the MCP server
        
        Args:
            action: The action to perform
            params: Parameters for the action
            
        Returns:
            Response data from server
        """
        url = f"{self.base_url}/api/v1/query"
        payload = {
            "action": action,
            "params": params or {}
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("data")
    
    def get_state(self, entity: str = None, limit: int = None, offset: int = None, status: str = None) -> Dict[str, Any]:
        """
        Get server memory snapshot with optional filtering
        
        Args:
            entity: Filter by entity type (users | tasks | config | logs)
            limit: Maximum number of items to return
            offset: Number of items to skip for pagination
            status: Filter tasks by status (only applies when entity=tasks)
        
        Returns:
            Filtered or complete memory snapshot
        """
        params = {}
        if entity:
            params["entity"] = entity
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if status:
            params["status"] = status
        
        url = f"{self.base_url}/api/v1/state"
        if params:
            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query_string}"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("data")
    
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent server logs"""
        response = self.session.get(f"{self.base_url}/api/v1/logs?limit={limit}")
        response.raise_for_status()
        return response.json().get("data")
    
    # Convenience methods for common actions
    
    def list_users(self) -> List[str]:
        """Get all users"""
        return self.query("list_users")
    
    def add_user(self, username: str) -> Dict[str, Any]:
        """Add a new user"""
        return self.query("add_user", {"username": username})
    
    def list_tasks(self, status: str = None, assigned_to: str = None) -> List[Dict[str, Any]]:
        """List tasks with optional filters"""
        params = {}
        if status:
            params["status"] = status
        if assigned_to:
            params["assigned_to"] = assigned_to
        return self.query("list_tasks", params)
    
    def add_task(self, title: str, **kwargs) -> Dict[str, Any]:
        """Add a new task"""
        params = {"title": title, **kwargs}
        return self.query("add_task", params)
    
    def update_task(self, task_id: int, **kwargs) -> Dict[str, Any]:
        """Update an existing task"""
        params = {"task_id": task_id, **kwargs}
        return self.query("update_task", params)
    
    def search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Search tasks by query"""
        return self.query("search_tasks", {"query": query})
    
    def get_summary(self) -> Dict[str, Any]:
        """Get data summary"""
        return self.query("summarize_data")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def main():
    """Example usage demonstrating MCP client"""
    
    # Initialize client
    client = MCPClient()
    
    print("=" * 60)
    print("MCP Client Example - AI Agent Interaction Demo")
    print("=" * 60)
    
    # Example 1: Add users
    print("\n1️⃣ Adding users...")
    client.add_user("alice")
    client.add_user("bob")
    client.add_user("charlie")
    users = client.list_users()
    print(f"   Users: {users}")
    
    # Example 2: Create tasks
    print("\n2️⃣ Creating tasks...")
    task1 = client.add_task(
        title="Build MCP integration",
        description="Integrate MCP server with AI agent",
        priority="high",
        assigned_to="alice"
    )
    print(f"   Task created: {task1['title']} (ID: {task1['id']})")
    
    task2 = client.add_task(
        title="Write documentation",
        description="Document MCP API endpoints",
        priority="medium",
        assigned_to="bob"
    )
    print(f"   Task created: {task2['title']} (ID: {task2['id']})")
    
    task3 = client.add_task(
        title="Test MCP server",
        description="Run integration tests",
        priority="high",
        assigned_to="alice"
    )
    print(f"   Task created: {task3['title']} (ID: {task3['id']})")
    
    # Example 3: List tasks by status
    print("\n3️⃣ Listing all tasks...")
    all_tasks = client.list_tasks()
    for task in all_tasks:
        print(f"   [{task['id']}] {task['title']} - {task['priority']} priority - assigned to {task['assigned_to']}")
    
    # Example 4: Update a task
    print("\n4️⃣ Updating task status...")
    updated = client.update_task(task1['id'], status="in_progress")
    print(f"   Task {updated['id']} status: {updated['status']}")
    
    # Example 5: Search tasks
    print("\n5️⃣ Searching tasks...")
    results = client.search_tasks("MCP")
    print(f"   Found {len(results)} tasks matching 'MCP':")
    for task in results:
        print(f"   - {task['title']}")
    
    # Example 6: Get tasks for specific user
    print("\n6️⃣ Getting tasks for Alice...")
    alice_tasks = client.list_tasks(assigned_to="alice")
    print(f"   Alice has {len(alice_tasks)} tasks:")
    for task in alice_tasks:
        print(f"   - {task['title']} [{task['status']}]")
    
    # Example 7: Get summary
    print("\n7️⃣ Getting data summary...")
    summary = client.get_summary()
    print(f"   Summary: {json.dumps(summary, indent=2)}")
    
    # Example 8: Get filtered state (new feature)
    print("\n8️⃣ Getting filtered state (tasks only, limit 5)...")
    filtered_state = client.get_state(entity="tasks", limit=5)
    print(f"   Retrieved {filtered_state['count']} of {filtered_state['total']} tasks")
    
    # Example 9: Get filtered state with status filter
    print("\n9️⃣ Getting pending tasks (filtered state)...")
    pending_state = client.get_state(entity="tasks", status="pending")
    print(f"   Found {pending_state['count']} pending tasks")
    
    # Example 10: Get complete state
    print("\n🔟 Getting complete server state...")
    state = client.get_state()
    print(f"   Total users: {state['stats']['total_users']}")
    print(f"   Total tasks: {state['stats']['total_tasks']}")
    print(f"   Total logs: {state['stats']['total_logs']}")
    
    # Example 11: View recent logs
    print("\n1️⃣1️⃣ Viewing recent logs...")
    logs = client.get_logs(limit=5)
    print(f"   Last {len(logs)} actions:")
    for log in logs[-5:]:
        print(f"   [{log['timestamp']}] {log['action']}")
    
    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to MCP server")
        print("   Make sure the server is running: python mcp_server.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
