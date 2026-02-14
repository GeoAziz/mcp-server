# 🚀 MCP Server Quick Start Guide

## What You Got

A complete MCP (Model Context Protocol) server implementation that solves the context window bloat problem when AI agents repeatedly call tools.

## Files Included

```
mcp_server.py              - Main FastAPI server (persistent backend)
mcp_client_example.py      - Python client with usage examples
context_comparison.py      - Demo showing 90%+ token reduction
requirements.txt           - Python dependencies
setup.py                   - Automated setup script
README.md                  - Full documentation
```

## 5-Minute Setup

### Step 1: Install

```bash
python setup.py
```

This installs dependencies and shows you the context savings demo.

### Step 2: Start Server

```bash
python mcp_server.py
```

Server runs at `http://localhost:8000`

### Step 3: Test It

In another terminal:

```bash
python mcp_client_example.py
```

You'll see it create users, tasks, search, and more - all with minimal context usage.

## Integration Patterns

### Pattern 1: Direct AI Agent Integration

**Instead of this (bloated):**
```python
# AI agent prompt with tools embedded
prompt = """
You have these tools: [massive schemas...]
Memory state: [all data...]
User query: {query}
"""
```

**Do this (lean):**
```python
# AI agent prompt referencing MCP
prompt = """
Query the MCP server at http://localhost:8000/mcp/query

Available actions: list_users, add_task, list_tasks, etc.

User query: {query}
"""

# Agent generates code like:
import requests
result = requests.post(
    "http://localhost:8000/mcp/query",
    json={"action": "list_tasks", "params": {"assigned_to": "alice"}}
)
```

**Result:** 90% reduction in prompt tokens, persistent memory across sessions.

### Pattern 2: VS Code Copilot Integration

Your AI assistant in VS Code can generate code that calls MCP:

```python
# Copilot generates this instead of inline logic:
from mcp_client_example import MCPClient

client = MCPClient()
tasks = client.list_tasks(assigned_to="alice")
```

### Pattern 3: Multi-Agent System

Multiple agents share the same memory:

```python
# Agent 1: Task creator
client.add_task(title="Build feature", assigned_to="bob")

# Agent 2: Task monitor (sees Agent 1's work)
tasks = client.list_tasks()  # Sees the task Agent 1 created

# Agent 3: Reporter
summary = client.get_summary()  # Gets stats on all tasks
```

## VS Code Setup

### Auto-start MCP on VS Code Launch

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start MCP Server",
      "type": "shell",
      "command": "python mcp_server.py",
      "isBackground": true,
      "runOptions": {
        "runOn": "folderOpen"
      }
    }
  ]
}
```

### Debug with Breakpoints

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug MCP Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/mcp_server.py",
      "console": "integratedTerminal"
    }
  ]
}
```

Press F5 to debug with breakpoints!

## Common Use Cases

### 1. Task Management Agent

```python
client = MCPClient()

# Agent creates tasks from emails/messages
client.add_task(
    title="Fix bug in auth",
    priority="high",
    assigned_to="alice"
)

# Check user's workload
alice_tasks = client.list_tasks(assigned_to="alice")
print(f"Alice has {len(alice_tasks)} tasks")
```

### 2. Project Dashboard Agent

```python
# Get overview without bloating context
summary = client.get_summary()

print(f"Tasks: {summary['summary']['total_tasks']}")
print(f"Pending: {summary['summary']['tasks_by_status']['pending']}")
```

### 3. Search & Analysis Agent

```python
# Search across all data
results = client.search_tasks("authentication")

# Agent can process results without re-fetching state
for task in results:
    print(f"Found: {task['title']}")
```

## Extending the Server

### Add a Custom Tool

Edit `mcp_server.py`:

```python
# 1. Define handler
async def handle_send_notification(params: Dict[str, Any]) -> Dict[str, Any]:
    user = params.get("user")
    message = params.get("message")
    
    # Your logic here
    print(f"Notifying {user}: {message}")
    
    return {"sent": True, "user": user}

# 2. Register in handlers dict
handlers = {
    # ... existing handlers ...
    "send_notification": handle_send_notification,
}
```

Now use it:

```python
client.query("send_notification", {
    "user": "alice",
    "message": "Your task is due soon"
})
```

## Production Checklist

- [ ] Replace in-memory storage with database (SQLite/PostgreSQL)
- [ ] Add API key authentication
- [ ] Restrict CORS to specific domains
- [ ] Set up logging to file/service
- [ ] Deploy with Docker/systemd
- [ ] Add rate limiting
- [ ] Set up monitoring (health checks)
- [ ] Configure backups

See README.md for detailed production setup.

## Monitoring

### Check Server Health

```bash
curl http://localhost:8000/
```

### View Recent Actions

```bash
curl http://localhost:8000/mcp/logs?limit=10
```

### Get Complete State

```bash
curl http://localhost:8000/mcp/state
```

## Troubleshooting

**Server won't start:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
python mcp_server.py --port 8001
```

**Can't connect from client:**
```bash
# Check server is running
curl http://localhost:8000/

# Check firewall (if remote)
telnet localhost 8000
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## Key Benefits Recap

✅ **90%+ context reduction** - Lean prompts, happy tokens
✅ **Persistent memory** - State survives across sessions  
✅ **Cost savings** - Fewer tokens = lower API costs
✅ **Multi-agent ready** - Shared memory, no conflicts
✅ **Easy debugging** - Server logs everything
✅ **Scalable** - Add DB, deploy anywhere

## Next Steps

1. ✅ Run `python setup.py` if you haven't
2. ✅ Start server: `python mcp_server.py`
3. ✅ Test client: `python mcp_client_example.py`
4. ✅ Add your own tools to `mcp_server.py`
5. ✅ Integrate with your AI agent/Copilot workflows

---

**Questions?** Check README.md for full docs.

**Want to see the savings?** Run `python context_comparison.py`

🚀 **Happy building with minimal context bloat!**
