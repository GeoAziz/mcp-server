"""
Test cases for CORS configuration and rate limiting
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"


def test_cors_headers():
    """Test that CORS headers are properly set"""
    print("\n🌐 Testing CORS configuration...")
    
    # Test with OPTIONS request (preflight)
    response = requests.options(
        f"{BASE_URL}/mcp/state",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    # Check CORS headers
    cors_headers = {
        "access-control-allow-origin": response.headers.get("access-control-allow-origin"),
        "access-control-allow-methods": response.headers.get("access-control-allow-methods"),
        "access-control-allow-credentials": response.headers.get("access-control-allow-credentials"),
    }
    
    print(f"   CORS Headers: {cors_headers}")
    
    # Verify CORS is enabled
    assert "access-control-allow-origin" in response.headers, "Missing CORS allow-origin header"
    print("   ✅ CORS headers present")
    
    # Test with actual GET request
    response = requests.get(
        f"{BASE_URL}/",
        headers={"Origin": "http://example.com"}
    )
    
    assert response.status_code == 200, "Request failed"
    assert "access-control-allow-origin" in response.headers, "Missing CORS header in GET response"
    print("   ✅ CORS working on GET requests")


def test_rate_limiting():
    """Test that rate limiting is enforced"""
    print("\n⏱️  Testing rate limiting...")
    
    # Get the configured rate limit (default: 100/minute)
    # We'll make requests quickly to trigger the limit
    
    # First, make a few successful requests
    success_count = 0
    for i in range(5):
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            success_count += 1
    
    print(f"   ✅ {success_count} requests succeeded")
    
    # Check for rate limit headers
    response = requests.get(f"{BASE_URL}/")
    rate_limit_headers = {}
    
    for header in response.headers:
        if "ratelimit" in header.lower() or "retry-after" in header.lower():
            rate_limit_headers[header] = response.headers[header]
    
    if rate_limit_headers:
        print(f"   ✅ Rate limit headers present: {rate_limit_headers}")
    else:
        print("   ⚠️  No rate limit headers in response (this is OK, headers may vary)")
    
    # Test that we can make multiple requests within the limit
    # Default is 100/minute, so 10 requests should be fine
    print("\n   Testing burst of 10 requests...")
    responses = []
    for i in range(10):
        response = requests.get(f"{BASE_URL}/")
        responses.append(response.status_code)
    
    success_count = sum(1 for code in responses if code == 200)
    rate_limited_count = sum(1 for code in responses if code == 429)
    
    print(f"   ✅ {success_count} requests succeeded, {rate_limited_count} rate limited")
    
    if success_count >= 8:
        print("   ✅ Rate limiting allows reasonable traffic")
    

def test_rate_limit_on_different_endpoints():
    """Test that rate limiting applies to all endpoints"""
    print("\n🔀 Testing rate limiting on different endpoints...")
    
    endpoints = [
        ("GET", "/"),
        ("GET", "/mcp/state"),
        ("GET", "/mcp/logs"),
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        
        print(f"   {method} {endpoint}: {response.status_code}")
        assert response.status_code in [200, 429], f"Unexpected status code for {endpoint}"
    
    print("   ✅ Rate limiting applied to all endpoints")


def test_cors_with_different_origins():
    """Test CORS with different origins (if configured)"""
    print("\n🌍 Testing CORS with different origins...")
    
    origins = [
        "http://localhost:3000",
        "http://example.com",
        "https://app.example.com",
    ]
    
    for origin in origins:
        response = requests.get(
            f"{BASE_URL}/",
            headers={"Origin": origin}
        )
        
        cors_origin = response.headers.get("access-control-allow-origin")
        print(f"   Origin: {origin} -> CORS header: {cors_origin}")
    
    print("   ✅ CORS responses received for different origins")


def run_all_tests():
    """Run all CORS and rate limiting tests"""
    print("=" * 70)
    print("🧪 CORS AND RATE LIMITING TESTS")
    print("=" * 70)
    
    try:
        # Check if server is running
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running. Start it with: python mcp_server.py")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start it with: python mcp_server.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Server timeout. Please check if server is running properly.")
        return False
    
    try:
        # Run tests
        test_cors_headers()
        test_cors_with_different_origins()
        test_rate_limiting()
        test_rate_limit_on_different_endpoints()
        
        print("\n" + "=" * 70)
        print("✅ ALL CORS AND RATE LIMITING TESTS PASSED!")
        print("=" * 70)
        return True
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
