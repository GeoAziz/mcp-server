"""
MCP Server - Entry Point
Imports and starts the application from the app module
"""

from app.main import app

# Export app for uvicorn
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8000, reload=True)
