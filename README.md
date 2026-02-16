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
| `/mcp/logs` | GET | View action logs |
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

View recent actions:

```bash
curl http://localhost:8000/mcp/logs?limit=10
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

### Add API Key Authentication

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "your-secret-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Use in endpoint
@app.post("/mcp/query")
async def query(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    # ... existing code ...
```

### Restrict CORS in Production

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 📈 Performance Tips

1. **Use connection pooling** for database connections
2. **Add caching** for frequently accessed data (Redis)
3. **Implement rate limiting** to prevent abuse
4. **Use async handlers** for I/O operations
5. **Add pagination** for large result sets

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
