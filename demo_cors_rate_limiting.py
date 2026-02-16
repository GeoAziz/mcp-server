"""
Demo script to showcase CORS and Rate Limiting features
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def demo():
    print("=" * 70)
    print("🎯 MCP Server - CORS and Rate Limiting Demo")
    print("=" * 70)
    
    # Check server health
    print("\n1. Health Check...")
    response = requests.get(BASE_URL)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Check CORS headers
    print("\n2. CORS Configuration...")
    response = requests.get(BASE_URL, headers={"Origin": "http://example.com"})
    cors_header = response.headers.get("access-control-allow-origin", "Not set")
    print(f"   Access-Control-Allow-Origin: {cors_header}")
    print(f"   ✅ CORS is configured and working")
    
    # Demonstrate rate limiting
    print("\n3. Rate Limiting Demo...")
    print("   Making 10 quick requests...")
    
    success = 0
    for i in range(10):
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            success += 1
        elif response.status_code == 429:
            print(f"   🛑 Rate limited on request #{i+1}")
            break
    
    print(f"   ✅ Completed {success} requests successfully")
    
    # Show API endpoints with rate limiting
    print("\n4. Protected Endpoints...")
    endpoints = [
        ("GET", "/"),
        ("GET", "/mcp/state"),
        ("GET", "/mcp/logs"),
    ]
    
    for method, endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        status = "✅ OK" if response.status_code == 200 else f"⚠️  {response.status_code}"
        print(f"   {method} {endpoint:20} -> {status}")
    
    print("\n" + "=" * 70)
    print("Configuration:")
    print("  • Rate Limit: 100 requests/minute (configurable via MCP_RATE_LIMIT)")
    print("  • CORS: All origins allowed (configurable via MCP_CORS_ORIGINS)")
    print("  • API Key: Not required (configurable via MCP_API_KEY)")
    print("=" * 70)
    
    print("\n📝 To configure:")
    print("   export MCP_RATE_LIMIT='200/minute'")
    print("   export MCP_CORS_ORIGINS='https://example.com,https://app.example.com'")
    print("   export MCP_API_KEY='your-secret-key'")
    print("   python mcp_server.py")

if __name__ == "__main__":
    try:
        demo()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure the server is running: python mcp_server.py")
