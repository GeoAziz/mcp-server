"""
External integrations for MCP Server (GitHub, Figma, Playwright).
"""

import base64
import os
from typing import Any, Dict, Optional

import requests
from sqlalchemy.orm import Session


GITHUB_API_BASE = "https://api.github.com"
FIGMA_API_BASE = "https://api.figma.com/v1"


def _github_headers() -> Dict[str, str]:
    token = os.getenv("MCP_GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _figma_headers() -> Dict[str, str]:
    token = os.getenv("MCP_FIGMA_TOKEN")
    if not token:
        raise ValueError("MCP_FIGMA_TOKEN is required for Figma actions")
    return {"X-Figma-Token": token}


def _require_url(url: Optional[str]) -> str:
    if not url:
        raise ValueError("url is required")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("url must start with http:// or https://")
    return url


def _request_json(method: str, url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    clean_params = {k: v for k, v in (params or {}).items() if v is not None}
    response = requests.request(method, url, headers=headers, params=clean_params, timeout=30)
    if not response.ok:
        raise ValueError(f"Request failed ({response.status_code}): {response.text}")
    return response.json()


# =====================
# GitHub Actions
# =====================

async def github_search_repositories(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    query = params.get("query")
    if not query:
        raise ValueError("query is required")
    url = f"{GITHUB_API_BASE}/search/repositories"
    search_params = {
        "q": query,
        "sort": params.get("sort"),
        "order": params.get("order"),
        "per_page": params.get("per_page", 10),
        "page": params.get("page", 1),
    }
    data = _request_json("GET", url, _github_headers(), params=search_params)
    return {"total": data.get("total_count"), "items": data.get("items", [])}


async def github_search_issues(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    query = params.get("query")
    if not query:
        raise ValueError("query is required")
    url = f"{GITHUB_API_BASE}/search/issues"
    search_params = {
        "q": query,
        "sort": params.get("sort"),
        "order": params.get("order"),
        "per_page": params.get("per_page", 10),
        "page": params.get("page", 1),
    }
    data = _request_json("GET", url, _github_headers(), params=search_params)
    return {"total": data.get("total_count"), "items": data.get("items", [])}


async def github_get_repository(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    owner = params.get("owner")
    repo = params.get("repo")
    if not owner or not repo:
        raise ValueError("owner and repo are required")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    return _request_json("GET", url, _github_headers())


async def github_list_issues(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    owner = params.get("owner")
    repo = params.get("repo")
    if not owner or not repo:
        raise ValueError("owner and repo are required")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
    list_params = {
        "state": params.get("state", "open"),
        "per_page": params.get("per_page", 10),
        "page": params.get("page", 1),
    }
    data = _request_json("GET", url, _github_headers(), params=list_params)
    return {"items": data}


async def github_list_pulls(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    owner = params.get("owner")
    repo = params.get("repo")
    if not owner or not repo:
        raise ValueError("owner and repo are required")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"
    list_params = {
        "state": params.get("state", "open"),
        "per_page": params.get("per_page", 10),
        "page": params.get("page", 1),
    }
    data = _request_json("GET", url, _github_headers(), params=list_params)
    return {"items": data}


# =====================
# Figma Actions
# =====================

async def figma_get_file(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    file_key = params.get("file_key")
    if not file_key:
        raise ValueError("file_key is required")
    url = f"{FIGMA_API_BASE}/files/{file_key}"
    return _request_json("GET", url, _figma_headers())


async def figma_get_nodes(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    file_key = params.get("file_key")
    node_ids = params.get("node_ids")
    if not file_key or not node_ids:
        raise ValueError("file_key and node_ids are required")
    if isinstance(node_ids, list):
        node_ids = ",".join(node_ids)
    url = f"{FIGMA_API_BASE}/files/{file_key}/nodes"
    return _request_json("GET", url, _figma_headers(), params={"ids": node_ids})


async def figma_get_components(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    file_key = params.get("file_key")
    if not file_key:
        raise ValueError("file_key is required")
    url = f"{FIGMA_API_BASE}/files/{file_key}/components"
    return _request_json("GET", url, _figma_headers())


async def figma_get_styles(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    file_key = params.get("file_key")
    if not file_key:
        raise ValueError("file_key is required")
    url = f"{FIGMA_API_BASE}/files/{file_key}/styles"
    return _request_json("GET", url, _figma_headers())


# =====================
# Playwright Actions
# =====================

async def playwright_get_title(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    url = _require_url(params.get("url"))
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        title = await page.title()
        await browser.close()

    return {"title": title, "url": url}


async def playwright_get_text(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    url = _require_url(params.get("url"))
    max_chars = params.get("max_chars", 4000)
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        content = await page.evaluate("() => document.body.innerText || ''")
        await browser.close()

    return {"text": content[:max_chars], "truncated": len(content) > max_chars, "url": url}


async def playwright_screenshot(params: Dict[str, Any], db: Session) -> Dict[str, Any]:
    url = _require_url(params.get("url"))
    full_page = bool(params.get("full_page", False))
    wait_ms = params.get("wait_ms", 0)
    viewport_width = params.get("viewport_width", 1280)
    viewport_height = params.get("viewport_height", 720)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": viewport_width, "height": viewport_height})
        await page.goto(url, wait_until="domcontentloaded")
        if wait_ms:
            await page.wait_for_timeout(wait_ms)
        image_bytes = await page.screenshot(full_page=full_page)
        await browser.close()

    encoded = base64.b64encode(image_bytes).decode("ascii")
    return {
        "content_type": "image/png",
        "screenshot_base64": encoded,
        "url": url,
    }
