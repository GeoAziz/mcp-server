# Integrations Guide

MCP Server includes fully implemented external integrations for GitHub, Figma, and Playwright. This guide shows how to use each one.

## Overview

| Integration | Status | Description |
|---|---|---|
| **GitHub** | ✅ Complete | Search repositories, search issues, get repo details, list issues/PRs |
| **Figma** | ✅ Complete | Get file metadata, query nodes, retrieve components and styles |
| **Playwright** | ✅ Complete | Get page title, extract text content, capture screenshots |

---

## GitHub Integration

Query GitHub's API without adding tokens to your client code. Perfect for agents that need to search code, find issues, or inspect repositories.

### Prerequisites

```bash
# Optional: GitHub API token (increases rate limits from 60 to 5000 requests/hour)
export MCP_GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

Get token: https://github.com/settings/tokens (create with `public_repo` scope)

### Available Actions

#### Search Repositories

Find public repositories by keyword:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "github_search_repositories",
    "params": {
      "query": "python fastapi",
      "sort": "stars",
      "order": "desc",
      "per_page": 10
    }
  }'
```

**Parameters:**
- `query` (required) - Search term
- `sort` - `stars`, `forks`, `updated` (default: best match)
- `order` - `asc`, `desc` (default: `desc`)
- `per_page` - Results per page (default: 10, max: 100)
- `page` - Page number (default: 1)

#### Search Issues

Search across all public issues:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "github_search_issues",
    "params": {
      "query": "bug authentication fastapi"
    }
  }'
```

**Parameters:**
- `query` (required) - Search term
- `sort`, `order`, `per_page`, `page` - Same as repositories

#### Get Repository Details

Get comprehensive info about a specific repository:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "github_get_repository",
    "params": {
      "owner": "tiangolo",
      "repo": "fastapi"
    }
  }'
```

**Response includes:**
- Stars, forks, watchers
- Description, homepage URL
- Language, license
- Last updated timestamp

#### List Repository Issues

Get open/closed issues for a repository:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "github_list_issues",
    "params": {
      "owner": "tiangolo",
      "repo": "fastapi",
      "state": "open",
      "per_page": 20
    }
  }'
```

**Parameters:**
- `owner`, `repo` (required)
- `state` - `open`, `closed`, `all` (default: `open`)
- `per_page`, `page` - Pagination

#### List Pull Requests

Get pull requests for a repository:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "github_list_pulls",
    "params": {
      "owner": "tiangolo",
      "repo": "fastapi",
      "state": "open"
    }
  }'
```

---

## Figma Integration

Access Figma design files, components, and tokens programmatically. Great for design system agents or design-to-code workflows.

### Prerequisites

```bash
# Required: Figma API token
export MCP_FIGMA_TOKEN="figi_xxxxxxxxxxxxxxxxxxxx"
```

Get token: https://www.figma.com/developers/api#authentication

### Available Actions

#### Get File Metadata

Retrieve complete file structure including pages, components, and styles:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "figma_get_file",
    "params": {
      "file_key": "xyz12345"
    }
  }'
```

**Parameters:**
- `file_key` (required) - From Figma URL: `figma.com/file/{file_key}/...`

**Response includes:**
- All pages and frames
- Component definitions
- Design tokens and variables
- Layer hierarchy

#### Query Specific Nodes

Get detailed info about specific design nodes:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "figma_get_nodes",
    "params": {
      "file_key": "xyz12345",
      "node_ids": ["123:456", "123:789"]
    }
  }'
```

**Parameters:**
- `file_key` (required)
- `node_ids` (required) - Array of node IDs or comma-separated string

**Response includes:**
- Node properties (size, position, colors)
- Typography information
- Component references
- Export settings

#### Get Components

List all component definitions in the file:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "figma_get_components",
    "params": {
      "file_key": "xyz12345"
    }
  }'
```

**Response includes:**
- Component names and IDs
- Descriptions
- Component sets
- Variant information

#### Get Design Tokens/Styles

Extract all design tokens and styles from the file:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "figma_get_styles",
    "params": {
      "file_key": "xyz12345"
    }
  }'
```

**Response includes:**
- Color styles
- Typography styles
- Effect styles
- Grid styles

---

## Playwright Integration

Automate web page interactions. Perfect for agents that need to extract content, verify UI states, or generate screenshots for documentation.

### Prerequisites

```bash
# Playwright is included in requirements.txt
pip install -r requirements.txt
```

### Available Actions

#### Get Page Title

Extract the title of a web page:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "playwright_get_title",
    "params": {
      "url": "https://github.com/tiangolo/fastapi"
    }
  }'
```

**Response:**
```json
{
  "title": "tiangolo/fastapi: Modern, fast web framework...",
  "url": "https://github.com/tiangolo/fastapi"
}
```

#### Extract Page Text

Get all visible text content from a page:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "playwright_get_text",
    "params": {
      "url": "https://example.com",
      "max_chars": 8000
    }
  }'
```

**Parameters:**
- `url` (required) - Must start with `http://` or `https://`
- `max_chars` - Truncate text to this length (default: 4000)

**Response includes:**
- `text` - Extracted content (plain text)
- `truncated` - Whether content was truncated
- `url` - Page URL

#### Capture Screenshot

Take a screenshot of a page:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "playwright_screenshot",
    "params": {
      "url": "https://example.com",
      "full_page": true,
      "viewport_width": 1920,
      "viewport_height": 1080,
      "wait_ms": 1000
    }
  }'
```

**Parameters:**
- `url` (required) - Page to screenshot
- `full_page` - Capture entire page (default: `false` = viewport only)
- `viewport_width` - Browser width (default: 1280)
- `viewport_height` - Browser height (default: 720)
- `wait_ms` - Wait time before screenshot in milliseconds (default: 0)

**Response includes:**
- `screenshot_base64` - PNG image encoded as base64 string
- `content_type` - Always `image/png`
- `url` - Page URL

**Decoding screenshot:**
```python
import base64
from PIL import Image
from io import BytesIO

# From API response
screenshot_b64 = response["data"]["screenshot_base64"]

# Decode and save
image_bytes = base64.b64decode(screenshot_b64)
image = Image.open(BytesIO(image_bytes))
image.save("screenshot.png")
```

---

## Rate Limits & Quotas

### GitHub API

| Limit | Unauthenticated | Authenticated |
|-------|-----------------|---------------|
| Requests/hour | 60 | 5,000 |
| Search results | Limited | Full |

**Recommendation:** Always set `MCP_GITHUB_TOKEN` in production.

### Figma API

| Limit | Value |
|-------|-------|
| Requests/minute | 300 |
| Concurrent requests | 5 |

**Note:** Rate limits are per token, not per IP.

### Playwright

| Limit | Value |
|-------|-------|
| Timeout | 30 seconds per request |
| Memory | ~100MB per browser instance |
| Concurrent instances | Limited by system resources |

**Optimization:** Reuse page contexts when possible. Each action launches/closes a browser (can be optimized in future versions).

---

## Error Handling

All integrations use consistent error handling:

```bash
# Example: Missing required parameter
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "github_search_repositories",
    "params": {}
  }'

# Response (400 Bad Request)
{
  "detail": "query is required"
}
```

**Common errors:**
- Missing required API token → "MCP_*_TOKEN is required"
- Invalid parameter → "[param_name] is required" or "[param_name] must be..."
- External API error → "Request failed (status_code): ..."
- Network timeout → "Request failed (timeout)"

---

## Usage Examples

### Agent: GitHub Issue Analyzer

```python
# Find issues related to authentication
action = "github_search_issues"
params = {
    "query": "authentication bug",
    "sort": "updated"
}

# Response contains relevant issues
# Agent can then list specific issues
action = "github_list_issues"
params = {
    "owner": "username",
    "repo": "projectname",
    "state": "open"
}
```

### Agent: Design System Inspector

```python
# Get all design tokens from Figma
action = "figma_get_styles"
params = {
    "file_key": "xyz12345"
}

# Extract components for code generation
action = "figma_get_components"
params = {
    "file_key": "xyz12345"
}

# Get specific component details
action = "figma_get_nodes"
params = {
    "file_key": "xyz12345",
    "node_ids": ["123:456"]
}
```

### Agent: Web Content Extractor

```python
# Get page text for analysis
action = "playwright_get_text"
params = {
    "url": "https://example.com/blog/article",
    "max_chars": 10000
}

# Screenshot for visual verification
action = "playwright_screenshot"
params = {
    "url": "https://example.com",
    "full_page": true
}
```

---

## Troubleshooting

### GitHub: "Requires authentication"

```bash
# Ensure token is set
export MCP_GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Verify it's being read
python -c "import os; print(os.getenv('MCP_GITHUB_TOKEN'))"
```

### Figma: "Request failed (401)"

```bash
# Token is invalid or expired
# Get new token from: https://www.figma.com/developers/api#authentication
export MCP_FIGMA_TOKEN="figi_xxxxxxxxxxxxxxxxxxxx"
```

### Playwright: "Browser launch failed"

```bash
# Install Playwright browsers (should auto-install, but can force)
python -m playwright install chromium

# Check if running in container - may need extra dependencies
apt-get install -y libglib2.0-0 libplayer-ui-glib2.0 ...  # See Playwright docs
```

### Timeouts

If requests timeout:

```bash
# Increase server timeout
python -m uvicorn app.main:app --timeout-keep-alive 60

# Playwright has 30s timeout - consider breaking tasks into smaller requests
```

---

**Last Updated:** March 2026  
**Status:** All integrations production-ready
