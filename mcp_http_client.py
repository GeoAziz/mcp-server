"""
Minimal HTTP client wrapper for MCP Server v1 endpoints.
"""

from typing import Any, Dict, List, Optional

import requests


class MCPHttpClient:
    """Lightweight HTTP client for MCP Server."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {"X-API-Key": self.api_key} if self.api_key else {}

    def query(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/query"
        payload = {"action": action, "params": params or {}}
        response = self.session.post(url, json=payload, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def state(
        self,
        entity: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/state"
        params: Dict[str, Any] = {}
        if entity:
            params["entity"] = entity
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if status:
            params["status"] = status
        response = self.session.get(url, params=params, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def logs(self, limit: int = 10, offset: Optional[int] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/logs"
        params: Dict[str, Any] = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        response = self.session.get(url, params=params, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    client = MCPHttpClient()
    print(client.query("list_users"))
