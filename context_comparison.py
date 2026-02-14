"""
Context Window Comparison: Tool-in-Prompt vs MCP Server

This file demonstrates the dramatic reduction in context window usage
when using MCP server instead of embedding tools in the prompt.
"""

# ============================================================================
# OLD WAY: Tool-in-Prompt (HIGH CONTEXT USAGE)
# ============================================================================

OLD_PROMPT_TEMPLATE = """
You are an AI assistant with access to the following tools:

TOOL: list_users
Description: Get all users in the system
Schema:
{
  "name": "list_users",
  "description": "Returns a list of all registered users",
  "parameters": {
    "type": "object",
    "properties": {},
    "required": []
  },
  "returns": {
    "type": "array",
    "items": {"type": "string"}
  }
}

TOOL: add_user
Description: Add a new user to the system
Schema:
{
  "name": "add_user",
  "description": "Creates a new user account",
  "parameters": {
    "type": "object",
    "properties": {
      "username": {
        "type": "string",
        "description": "The username for the new user"
      },
      "role": {
        "type": "string",
        "description": "User role (admin, user, guest)",
        "default": "user"
      }
    },
    "required": ["username"]
  },
  "returns": {
    "type": "object",
    "properties": {
      "username": {"type": "string"},
      "added": {"type": "boolean"}
    }
  }
}

TOOL: list_tasks
Description: List all tasks in the system
Schema:
{
  "name": "list_tasks",
  "description": "Returns tasks with optional filters",
  "parameters": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "description": "Filter by status (pending, in_progress, completed)",
        "optional": true
      },
      "assigned_to": {
        "type": "string",
        "description": "Filter by assigned user",
        "optional": true
      },
      "priority": {
        "type": "string",
        "description": "Filter by priority (low, medium, high)",
        "optional": true
      }
    },
    "required": []
  },
  "returns": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "status": {"type": "string"},
        "priority": {"type": "string"},
        "assigned_to": {"type": "string"},
        "created_at": {"type": "string"}
      }
    }
  }
}

TOOL: add_task
Description: Create a new task
Schema:
{
  "name": "add_task",
  "description": "Creates a new task in the system",
  "parameters": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "description": "Task title (required)"
      },
      "description": {
        "type": "string",
        "description": "Detailed task description",
        "optional": true
      },
      "priority": {
        "type": "string",
        "description": "Priority level (low, medium, high)",
        "default": "medium"
      },
      "assigned_to": {
        "type": "string",
        "description": "Username to assign task to",
        "optional": true
      }
    },
    "required": ["title"]
  },
  "returns": {
    "type": "object",
    "properties": {
      "id": {"type": "integer"},
      "title": {"type": "string"},
      "status": {"type": "string"},
      "created_at": {"type": "string"}
    }
  }
}

TOOL: update_task
Description: Update an existing task
Schema:
{
  "name": "update_task",
  "description": "Updates task properties",
  "parameters": {
    "type": "object",
    "properties": {
      "task_id": {
        "type": "integer",
        "description": "ID of task to update (required)"
      },
      "title": {"type": "string", "optional": true},
      "description": {"type": "string", "optional": true},
      "status": {"type": "string", "optional": true},
      "priority": {"type": "string", "optional": true},
      "assigned_to": {"type": "string", "optional": true}
    },
    "required": ["task_id"]
  },
  "returns": {
    "type": "object",
    "properties": {
      "id": {"type": "integer"},
      "updated": {"type": "boolean"}
    }
  }
}

CURRENT MEMORY STATE:
Users: ["alice", "bob", "charlie", "david", "eve"]
Tasks: [
  {
    "id": 1,
    "title": "Build authentication system",
    "description": "Implement JWT-based auth",
    "status": "in_progress",
    "priority": "high",
    "assigned_to": "alice",
    "created_at": "2025-02-01T10:00:00"
  },
  {
    "id": 2,
    "title": "Design database schema",
    "description": "Create ER diagrams and tables",
    "status": "completed",
    "priority": "high",
    "assigned_to": "bob",
    "created_at": "2025-02-01T11:00:00"
  },
  {
    "id": 3,
    "title": "Write API documentation",
    "description": "Document all endpoints",
    "status": "pending",
    "priority": "medium",
    "assigned_to": "charlie",
    "created_at": "2025-02-02T09:00:00"
  },
  {
    "id": 4,
    "title": "Setup CI/CD pipeline",
    "description": "Configure GitHub Actions",
    "status": "in_progress",
    "priority": "high",
    "assigned_to": "david",
    "created_at": "2025-02-02T14:00:00"
  },
  {
    "id": 5,
    "title": "Implement logging system",
    "description": "Add structured logging",
    "status": "pending",
    "priority": "low",
    "assigned_to": "eve",
    "created_at": "2025-02-03T08:00:00"
  }
]

Configuration:
{
  "max_tasks": 100,
  "default_priority": "medium",
  "allowed_statuses": ["pending", "in_progress", "completed"],
  "task_prefix": "TASK-"
}

USER QUERY: List all high priority tasks assigned to alice
"""

# Token count estimate: ~1,800 tokens (just for the tool definitions and state!)


# ============================================================================
# NEW WAY: MCP Server (LOW CONTEXT USAGE)
# ============================================================================

NEW_PROMPT_TEMPLATE = """
You have access to an MCP server at http://localhost:8000/mcp/query

To use it, make HTTP POST requests with this format:
{
  "action": "action_name",
  "params": {
    // action-specific parameters
  }
}

Available actions:
- list_users, add_user, remove_user
- list_tasks, add_task, update_task, delete_task, search_tasks
- get_config, update_config
- calculate, summarize_data

Example:
POST /mcp/query
{
  "action": "list_tasks",
  "params": {"priority": "high", "assigned_to": "alice"}
}

USER QUERY: List all high priority tasks assigned to alice
"""

# Token count estimate: ~150 tokens (90% reduction!)


# ============================================================================
# COMPARISON METRICS
# ============================================================================

def calculate_token_estimate(text: str) -> int:
    """Rough token estimate (1 token ≈ 4 characters)"""
    return len(text) // 4

old_tokens = calculate_token_estimate(OLD_PROMPT_TEMPLATE)
new_tokens = calculate_token_estimate(NEW_PROMPT_TEMPLATE)
reduction = ((old_tokens - new_tokens) / old_tokens) * 100

print("=" * 70)
print("CONTEXT WINDOW COMPARISON: Tool-in-Prompt vs MCP Server")
print("=" * 70)
print()
print(f"📊 OLD WAY (Tool-in-Prompt):")
print(f"   Estimated tokens: {old_tokens:,}")
print(f"   Characters: {len(OLD_PROMPT_TEMPLATE):,}")
print()
print(f"✅ NEW WAY (MCP Server):")
print(f"   Estimated tokens: {new_tokens:,}")
print(f"   Characters: {len(NEW_PROMPT_TEMPLATE):,}")
print()
print(f"💰 SAVINGS:")
print(f"   Token reduction: {old_tokens - new_tokens:,} tokens ({reduction:.1f}%)")
print(f"   Context saved: {len(OLD_PROMPT_TEMPLATE) - len(NEW_PROMPT_TEMPLATE):,} characters")
print()
print("=" * 70)
print()

# ============================================================================
# MULTI-TURN CONVERSATION COMPARISON
# ============================================================================

print("🔄 MULTI-TURN CONVERSATION IMPACT:")
print("=" * 70)
print()

turns = 10  # Number of conversation turns

old_cumulative = old_tokens * turns
new_cumulative = new_tokens * turns

# MCP only needs to send the tool schema once at the start
# Then each turn is just the lean prompt
mcp_first_turn = new_tokens + 200  # +200 for initial connection info
mcp_subsequent_turns = 50  # Just the action call
mcp_total = mcp_first_turn + (mcp_subsequent_turns * (turns - 1))

print(f"After {turns} conversation turns:")
print()
print(f"📈 OLD WAY (Repeated schemas):")
print(f"   Total tokens: {old_cumulative:,}")
print(f"   Per turn: {old_tokens:,}")
print()
print(f"✅ NEW WAY (MCP Server):")
print(f"   Total tokens: {mcp_total:,}")
print(f"   First turn: {mcp_first_turn:,}")
print(f"   Subsequent turns: ~{mcp_subsequent_turns} each")
print()
print(f"💰 TOTAL SAVINGS:")
print(f"   Tokens saved: {old_cumulative - mcp_total:,}")
print(f"   Reduction: {((old_cumulative - mcp_total) / old_cumulative) * 100:.1f}%")
print()
print("=" * 70)
print()

# ============================================================================
# REAL-WORLD SCENARIO
# ============================================================================

print("🌍 REAL-WORLD SCENARIO:")
print("=" * 70)
print()
print("Scenario: AI agent helping with project management over 50 turns")
print()

turns = 50
avg_tools_per_turn = 2  # Agent calls 2 tools per interaction

# Old way: Every tool call includes full context
old_total = old_tokens * turns * avg_tools_per_turn

# New way: Just API calls
new_total = mcp_first_turn + (mcp_subsequent_turns * turns * avg_tools_per_turn)

print(f"📊 Metrics:")
print(f"   Conversation turns: {turns}")
print(f"   Avg tool calls per turn: {avg_tools_per_turn}")
print()
print(f"OLD WAY:")
print(f"   Total tokens: {old_total:,}")
print(f"   Cost impact: High (repeated schemas)")
print()
print(f"NEW WAY (MCP):")
print(f"   Total tokens: {new_total:,}")
print(f"   Cost impact: Minimal (lean queries)")
print()
print(f"💰 SAVINGS:")
print(f"   Tokens saved: {old_total - new_total:,}")
print(f"   Reduction: {((old_total - new_total) / old_total) * 100:.1f}%")
print()

# Cost calculation (approximate)
cost_per_1k_tokens = 0.003  # $3 per 1M tokens = $0.003 per 1k
old_cost = (old_total / 1000) * cost_per_1k_tokens
new_cost = (new_total / 1000) * cost_per_1k_tokens

print(f"💵 ESTIMATED COST SAVINGS:")
print(f"   Old approach: ${old_cost:.2f}")
print(f"   MCP approach: ${new_cost:.2f}")
print(f"   Savings: ${old_cost - new_cost:.2f} ({((old_cost - new_cost) / old_cost) * 100:.1f}% cheaper)")
print()
print("=" * 70)
print()

# ============================================================================
# KEY BENEFITS SUMMARY
# ============================================================================

print("🎯 KEY BENEFITS OF MCP SERVER:")
print("=" * 70)
print()
print("1. ✅ Context Window Efficiency")
print("   - 90%+ reduction in prompt size")
print("   - Scales linearly, not exponentially")
print()
print("2. ✅ Persistent Memory")
print("   - State survives across sessions")
print("   - No need to re-send data every turn")
print()
print("3. ✅ Cost Savings")
print("   - Fewer tokens = lower API costs")
print("   - Especially impactful for long conversations")
print()
print("4. ✅ Maintainability")
print("   - Tools defined once on server")
print("   - Easy to update without changing prompts")
print()
print("5. ✅ Multi-Agent Support")
print("   - Multiple agents can share same memory")
print("   - Centralized state management")
print()
print("6. ✅ Debugging")
print("   - Server logs all actions")
print("   - Easy to trace agent behavior")
print()
print("=" * 70)
