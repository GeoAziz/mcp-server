# MCP Server - Model Context Protocol

A persistent backend service that reduces AI agent context window bloat by centralizing memory, tools, and logic.

## 🎯 Problem It Solves

**Before (Tool-in-Prompt):**
- Tool schemas repeated in every LLM call
- Memory/state re-sent constantly
- Context window fills up fast
- Poor multi-agent support

**After (MCP Server):**
- Tools live on external server
- Memory persists across sessions
- Lean prompts (10x token reduction)
- Scalable multi-agent architecture

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python mcp_server.py
```

Server runs at: `http://localhost:8000`

**Optional Environment Variables:**
```bash
# Enable API key authentication (recommended for production)
export MCP_API_KEY="your-secret-key"

# Configure CORS allowed origins (default: *)
export MCP_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Configure rate limit (default: 100/minute)
export MCP_RATE_LIMIT="200/minute"

# Configure log retention limit (default: 1000)
export MCP_LOG_RETENTION="5000"

python mcp_server.py
```

### 3. Test with Client

```bash
python mcp_client_example.py
```

## 📚 API Overview

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/mcp/query` | POST | Main action endpoint |
| `/mcp/state` | GET | Get memory snapshot (supports filtering & pagination) |
| `/mcp/logs` | GET | View structured action logs with configurable retention |
| `/mcp/reset` | POST | Reset all memory |

### Available Actions

**User Management:**
- `list_users` - Get all users
- `add_user` - Add new user
- `remove_user` - Remove user
- `get_user` - Get user details

**Task Management:**
- `list_tasks` - List all tasks (with filters)
- `add_task` - Create new task
- `update_task` - Update task
- `delete_task` - Delete task
- `search_tasks` - Search by query

**Configuration:**
- `get_config` - Get config values
- `update_config` - Update config

**Utilities:**
- `calculate` - Perform calculations
- `summarize_data` - Get data summary

## 💡 Usage Examples

### Python Client

```python
from mcp_client_example import MCPClient

client = MCPClient()

# Add user
client.add_user("alice")

# Create task
task = client.add_task(
    title="Build feature X",
    priority="high",
    assigned_to="alice"
)

# List tasks for user
alice_tasks = client.list_tasks(assigned_to="alice")

# Get summary
summary = client.get_summary()
```

### Direct HTTP (curl)

```bash
# Query endpoint
curl -X POST http://localhost:8000/mcp/query \
  -H "Content-Type: application/json" \
  -d '{
    "action": "list_users",
    "params": {}
  }'

# Add task
curl -X POST http://localhost:8000/mcp/query \
  -H "Content-Type: application/json" \
  -d '{
    "action": "add_task",
    "params": {
      "title": "My task",
      "priority": "high"
    }
  }'

# Get state
curl http://localhost:8000/mcp/state

# Get filtered state (tasks only, first 10)
curl http://localhost:8000/mcp/state?entity=tasks&limit=10

# Get pending tasks
curl http://localhost:8000/mcp/state?entity=tasks&status=pending
```

#### State Endpoint Query Parameters

The `/mcp/state` endpoint supports optional query parameters for filtering and pagination:

- `entity`: Filter by entity type (`users` | `tasks` | `config` | `logs`)
- `limit`: Maximum number of items to return
- `offset`: Number of items to skip (for pagination)
- `status`: Filter tasks by status (only applies when `entity=tasks`)

Examples:
```bash
# Get only tasks
curl http://localhost:8000/mcp/state?entity=tasks

# Get first 5 pending tasks
curl http://localhost:8000/mcp/state?entity=tasks&status=pending&limit=5

# Get users with pagination (skip first 10, return next 20)
curl http://localhost:8000/mcp/state?entity=users&offset=10&limit=20
```

### From AI Agent Prompt

Instead of defining tools in your LLM prompt, just give it the endpoint:

```python
# Old way (bloated prompt):
prompt = """
You have access to these tools:
[...massive tool schemas...]
[...memory state...]
"""

# New way (lean prompt):
prompt = """
You can query the MCP server at http://localhost:8000/mcp/query

Available actions: list_users, add_task, list_tasks, etc.

Example:
POST /mcp/query
{
  "action": "list_users",
  "params": {}
}
"""
```

## 🔧 VS Code Integration

### Option 1: Use with Copilot/GitHub Copilot Chat

Your AI assistant can call the MCP server directly from generated code:

```python
import requests

def get_user_tasks(username):
    response = requests.post(
        "http://localhost:8000/mcp/query",
        json={
            "action": "list_tasks",
            "params": {"assigned_to": username}
        }
    )
    return response.json()["data"]
```

### Option 2: Add as VS Code Task

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start MCP Server",
      "type": "shell",
      "command": "python",
      "args": ["mcp_server.py"],
      "isBackground": true,
      "problemMatcher": []
    }
  ]
}
```

Run with: `Terminal > Run Task > Start MCP Server`

### Option 3: Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "MCP Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/mcp_server.py",
      "console": "integratedTerminal"
    }
  ]
}
```

Debug with breakpoints: `F5`

## 📊 Monitoring & Logs

### Structured Logging

All actions are logged with structured JSON format including:
- **timestamp**: ISO 8601 timestamp of the action
- **action**: The action that was performed
- **payload**: Action parameters and result (truncated to 200 chars)
- **status**: `success` or `error`

View recent actions:

```bash
curl http://localhost:8000/mcp/logs?limit=10
```

Example log entry:
```json
{
  "timestamp": "2026-02-16T15:14:57.661938",
  "action": "add_user",
  "payload": {
    "params": {"username": "alice"},
    "result": "{'username': 'alice', 'added': True}"
  },
  "status": "success"
}
```

### Log Retention

Logs are automatically trimmed to maintain the configured retention limit (default: 1000 entries).
Configure via environment variable:

```bash
export MCP_LOG_RETENTION="5000"  # Keep last 5000 log entries
```

### Accessing Logs

Via `/mcp/logs` endpoint:
```bash
# Get last 10 logs
curl http://localhost:8000/mcp/logs?limit=10
```

Via `/mcp/state` endpoint:
```bash
# Get logs with pagination
curl "http://localhost:8000/mcp/state?entity=logs&limit=20&offset=10"
```

Check server health:

```bash
curl http://localhost:8000/
```

## 🔄 Adding Custom Tools

Add new actions to `mcp_server.py`:

```python
# 1. Add handler function
async def handle_my_custom_tool(params: Dict[str, Any]) -> Any:
    # Your logic here
    result = params.get("input") * 2
    return {"result": result}

# 2. Register in handlers dict
handlers = {
    # ... existing handlers ...
    "my_custom_tool": handle_my_custom_tool,
}
```

Then call it:

```python
client.query("my_custom_tool", {"input": 42})
```

## 🗄️ Database Integration

For production, replace in-memory storage with a database:

### SQLite Example

```python
import sqlite3

class DatabaseMemory:
    def __init__(self, db_path="mcp.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.init_tables()
    
    def init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT,
                priority TEXT,
                assigned_to TEXT,
                created_at TEXT
            )
        """)
        self.conn.commit()
    
    def add_task(self, task):
        self.conn.execute(
            "INSERT INTO tasks (title, priority, assigned_to, created_at) VALUES (?, ?, ?, ?)",
            (task["title"], task["priority"], task["assigned_to"], task["created_at"])
        )
        self.conn.commit()
```

### PostgreSQL Example

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="mcp_db",
    user="user",
    password="password"
)
```

## 🚀 Production Deployment

### Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py .

EXPOSE 8000
CMD ["python", "mcp_server.py"]
```

Build and run:

```bash
docker build -t mcp-server .
docker run -p 8000:8000 mcp-server
```

### Systemd (Linux)

Create `/etc/systemd/system/mcp-server.service`:

```ini
[Unit]
Description=MCP Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/mcp
ExecStart=/usr/bin/python3 /path/to/mcp/mcp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
```

## 🔐 Security

### API Key Authentication

API key authentication is built-in and can be enabled by setting an environment variable:

```bash
export MCP_API_KEY="your-secret-key-here"
python mcp_server.py
```

Then include the API key in requests:

```bash
curl http://localhost:8000/mcp/state \
  -H "X-API-Key: your-secret-key-here"
```

If `MCP_API_KEY` is not set, authentication is disabled (useful for development).

### CORS Configuration

CORS is enabled by default with wildcard origins for development. For production, restrict to specific domains:

```bash
# Allow specific origins (comma-separated)
export MCP_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
python mcp_server.py
```

The CORS middleware supports:
- Configurable allowed origins
- Credentials support
- Standard HTTP methods (GET, POST, PUT, DELETE, OPTIONS)
- All headers allowed

### Rate Limiting

Rate limiting is automatically enabled to protect against abuse:

```bash
# Configure rate limit (default: 100/minute)
export MCP_RATE_LIMIT="200/minute"
python mcp_server.py
```

Supported formats:
- `100/minute` - 100 requests per minute
- `10/second` - 10 requests per second
- `1000/hour` - 1000 requests per hour

When rate limit is exceeded, the API returns:
- Status: `429 Too Many Requests`
- Response: `{"error":"Rate limit exceeded: 100 per 1 minute"}`

Rate limiting applies to all endpoints and is enforced per IP address.

## 📈 Performance Tips

1. **Use connection pooling** for database connections
2. **Add caching** for frequently accessed data (Redis)
3. **Configure rate limiting** based on your traffic patterns (see Security section)
4. **Use async handlers** for I/O operations
5. **Add pagination** for large result sets
6. **Set appropriate CORS origins** to reduce unauthorized requests

## 🧪 Testing

```bash
# Install pytest
pip install pytest pytest-asyncio httpx

# Run tests
pytest test_mcp_server.py
```

## 📝 License

MIT

## 🤝 Contributing

1. Fork the repo
2. Create feature branch
3. Add your enhancements
4. Submit pull request

---

**Built for AI agents to reduce context window bloat** 🚀
