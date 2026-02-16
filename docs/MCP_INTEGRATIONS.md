# MCP Integrations (GitHub, Figma, Playwright)

This server exposes MCP-style actions for common heavy integrations. Use `/api/v1/query` and keep tool schemas out of prompts.

## Environment Variables

```bash
# Optional, but recommended for GitHub rate limits
export MCP_GITHUB_TOKEN="your-github-token"

# Required for Figma actions
export MCP_FIGMA_TOKEN="your-figma-token"
```

## GitHub Actions

- `github_search_repositories` (params: query, sort?, order?, per_page?, page?)
- `github_search_issues` (params: query, sort?, order?, per_page?, page?)
- `github_get_repository` (params: owner, repo)
- `github_list_issues` (params: owner, repo, state?, per_page?, page?)
- `github_list_pulls` (params: owner, repo, state?, per_page?, page?)

Example:

```bash
python mcp_cli.py query github_search_repositories \
  --params '{"query": "language:python fastapi", "per_page": 5}'
```

## Figma Actions

- `figma_get_file` (params: file_key)
- `figma_get_nodes` (params: file_key, node_ids)
- `figma_get_components` (params: file_key)
- `figma_get_styles` (params: file_key)

Example:

```bash
python mcp_cli.py query figma_get_nodes \
  --params '{"file_key": "FILE_KEY", "node_ids": ["1:2", "3:4"]}'
```

## Playwright Actions

**Install browsers once:**

```bash
python -m playwright install
```

- `playwright_get_title` (params: url)
- `playwright_get_text` (params: url, max_chars?)
- `playwright_screenshot` (params: url, full_page?, wait_ms?, viewport_width?, viewport_height?)

Example:

```bash
python mcp_cli.py query playwright_screenshot \
  --params '{"url": "https://example.com", "full_page": true}'
```
