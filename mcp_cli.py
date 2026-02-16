"""
Simple CLI for starting and querying the MCP server.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

import requests
import uvicorn


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def _parse_json(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in --params: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("--params must be a JSON object")
    return data


def _headers(api_key: Optional[str]) -> Dict[str, str]:
    return {"X-API-Key": api_key} if api_key else {}


def cmd_start(args: argparse.Namespace) -> int:
    uvicorn.run(
        args.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    try:
        params = _parse_json(args.params)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    payload = {"action": args.action, "params": params}
    url = f"{args.base_url.rstrip('/')}/api/v1/query"
    response = requests.post(url, json=payload, headers=_headers(args.api_key), timeout=30)

    if not response.ok:
        print(f"HTTP {response.status_code}: {response.text}", file=sys.stderr)
        return 1

    _print_json(response.json())
    return 0


def cmd_state(args: argparse.Namespace) -> int:
    url = f"{args.base_url.rstrip('/')}/api/v1/state"
    params: Dict[str, Any] = {}
    if args.entity:
        params["entity"] = args.entity
    if args.limit is not None:
        params["limit"] = args.limit
    if args.offset is not None:
        params["offset"] = args.offset
    if args.status:
        params["status"] = args.status

    response = requests.get(url, params=params, headers=_headers(args.api_key), timeout=30)
    if not response.ok:
        print(f"HTTP {response.status_code}: {response.text}", file=sys.stderr)
        return 1

    _print_json(response.json())
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    url = f"{args.base_url.rstrip('/')}/api/v1/logs"
    params = {"limit": args.limit}
    if args.offset is not None:
        params["offset"] = args.offset

    response = requests.get(url, params=params, headers=_headers(args.api_key), timeout=30)
    if not response.ok:
        print(f"HTTP {response.status_code}: {response.text}", file=sys.stderr)
        return 1

    _print_json(response.json())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MCP Server CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start the MCP server")
    start_parser.add_argument("--app", default="app.main:app", help="ASGI app path")
    start_parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    start_parser.add_argument("--port", type=int, default=8000, help="Bind port")
    start_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    start_parser.add_argument("--log-level", default="info", help="Uvicorn log level")
    start_parser.set_defaults(func=cmd_start)

    query_parser = subparsers.add_parser("query", help="Call /api/v1/query")
    query_parser.add_argument("action", help="Action name to execute")
    query_parser.add_argument("--params", help="JSON object for params")
    query_parser.add_argument("--base-url", default="http://localhost:8000", help="Server URL")
    query_parser.add_argument("--api-key", help="X-API-Key value")
    query_parser.set_defaults(func=cmd_query)

    state_parser = subparsers.add_parser("state", help="Call /api/v1/state")
    state_parser.add_argument("--entity", help="users | tasks | config | logs")
    state_parser.add_argument("--limit", type=int, help="Limit results")
    state_parser.add_argument("--offset", type=int, help="Offset results")
    state_parser.add_argument("--status", help="Task status filter")
    state_parser.add_argument("--base-url", default="http://localhost:8000", help="Server URL")
    state_parser.add_argument("--api-key", help="X-API-Key value")
    state_parser.set_defaults(func=cmd_state)

    logs_parser = subparsers.add_parser("logs", help="Call /api/v1/logs")
    logs_parser.add_argument("--limit", type=int, default=10, help="Number of logs")
    logs_parser.add_argument("--offset", type=int, help="Offset logs")
    logs_parser.add_argument("--base-url", default="http://localhost:8000", help="Server URL")
    logs_parser.add_argument("--api-key", help="X-API-Key value")
    logs_parser.set_defaults(func=cmd_logs)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
