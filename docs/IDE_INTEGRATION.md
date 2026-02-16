# IDE Integration (VS Code + Generic HTTP Client)

This guide shows the end-to-end developer experience: start the MCP server, connect from the IDE, and issue tool calls without embedding tool schemas in prompts.

## 1) Start the Server

```bash
python mcp_cli.py start
```

Optional auth (recommended for shared environments):

```bash
export MCP_API_KEY="your-secret-key"
python mcp_cli.py start
```

## 2) Add a VS Code Task (Auto-start)

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start MCP Server",
      "type": "shell",
      "command": "python",
      "args": ["mcp_cli.py", "start"],
      "isBackground": true,
      "problemMatcher": []
    }
  ]
}
```

## 3) Use a Lean Prompt (No Tool Schemas)

Use a short system or project prompt that points to the server:

```text
You can query the MCP server at http://localhost:8000/api/v1/query.
Return only the JSON response body.
Available actions include: list_users, add_user, list_tasks, add_task, update_task, search_tasks, get_config, update_config.
For integration actions (GitHub, Figma, Playwright), see docs/MCP_INTEGRATIONS.md.
```

This keeps tool definitions and state out of the model window.

### Example System Prompt

```text
You are an agent that calls MCP for tools and memory.
Use only POST http://localhost:8000/api/v1/query with JSON.
Return only the JSON response body, no extra text.
```

### Action Mapping (Mental Model)

| Need | MCP action | Params | Example |
| --- | --- | --- | --- |
| List users | `list_users` | `{}` | `{}` |
| Add user | `add_user` | `{"username": "alice"}` | `{"username": "alice"}` |
| List tasks | `list_tasks` | `{"status": "pending"}` | `{"status": "pending"}` |
| Add task | `add_task` | `{"title": "Ship v1"}` | `{"title": "Ship v1"}` |
| Update task | `update_task` | `{"task_id": 1, "status": "completed"}` | `{"task_id": 1, "status": "completed"}` |
| Search tasks | `search_tasks` | `{"query": "auth"}` | `{"query": "auth"}` |
| Read config | `get_config` | `{}` | `{}` |
| Update config | `update_config` | `{"key": "max_tasks", "value": 200}` | `{"key": "max_tasks", "value": 200}` |

## 4) Call the Server From the IDE Terminal

```bash
# List users
python mcp_cli.py query list_users

# Add a user
python mcp_cli.py query add_user --params '{"username": "alice"}'

# Add a task
python mcp_cli.py query add_task --params '{"title": "Ship v1", "priority": "high", "assigned_to": "alice"}'

# Read state
python mcp_cli.py state --entity tasks --limit 5
```

## 5) Minimal HTTP Client Wrapper (Optional)

Use the lightweight wrapper for scripts or IDE snippets:

```python
from mcp_http_client import MCPHttpClient

client = MCPHttpClient()
print(client.query("list_users"))
```

## 6) Generic HTTP Example

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"action": "list_users", "params": {}}'
```

With API key:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"action": "list_users", "params": {}}'
```

## 7) What This Achieves

- Tools and memory live on the server, not in the prompt.
- Clients only send compact action calls.
- Context bloat is reduced while state remains persistent.
