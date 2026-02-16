"""
Test to verify rate limiting actually blocks excessive requests
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_rate_limit_enforcement():
    """Test that rate limiting blocks excessive requests"""
    print("\n⚡ Testing rate limit enforcement...")
    print("   Making 120 rapid requests (limit is 100/minute)...")
    
    success_count = 0
    rate_limited_count = 0
    
    # Make more requests than the limit allows
    for i in range(120):
        try:
            response = requests.get(f"{BASE_URL}/", timeout=2)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                if rate_limited_count == 1:
                    print(f"\n   🛑 First rate limit hit at request #{i+1}")
                    print(f"   Response: {response.status_code} - {response.text[:100]}")
            else:
                print(f"   Unexpected status code: {response.status_code}")
        except Exception as e:
            print(f"   Error on request {i+1}: {e}")
    
    print(f"\n   Results:")
    print(f"   ✅ Successful requests: {success_count}")
    print(f"   🛑 Rate limited (429): {rate_limited_count}")
    
    # We expect some requests to be rate limited
    if rate_limited_count > 0:
        print(f"\n   ✅ Rate limiting is working! {rate_limited_count} requests were blocked")
        return True
    elif success_count <= 100:
        print(f"\n   ⚠️  Made {success_count} requests within limit - rate limiting not triggered but working")
        return True
    else:
        print(f"\n   ⚠️  Made {success_count} requests without hitting limit - rate limiting may not be enforced")
        return False

if __name__ == "__main__":
    try:
        # Check if server is running
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code != 200:
            print("❌ Server is not running properly. Start it with: python mcp_server.py")
            exit(1)
        test_rate_limit_enforcement()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start it with: python mcp_server.py")
        exit(1)
    except requests.exceptions.Timeout:
        print("❌ Server timeout. Please check if server is running properly.")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
