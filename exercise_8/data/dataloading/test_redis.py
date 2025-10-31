import redis
import os

def test_redis_connection():
    # Try different possible Redis URLs
    redis_urls = [
        "redis://localhost:6379",
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        "redis://127.0.0.1:6379"
    ]
    
    for url in redis_urls:
        print(f"Testing Redis connection to: {url}")
        try:
            r = redis.from_url(url, decode_responses=True)
            r.ping()
            print(f"✅ Successfully connected to Redis at {url}")
            
            # Test basic operations
            test_key = "test_connection"
            test_value = "redis_access_test"
            r.set(test_key, test_value)
            retrieved_value = r.get(test_key)
            
            if retrieved_value == test_value:
                print(f"✅ Redis read/write test passed with value: {retrieved_value}")
            else:
                print(f"❌ Redis read/write test failed. Expected: {test_value}, Got: {retrieved_value}")
                
            # Clean up test key
            r.delete(test_key)
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Redis at {url}: {e}")
            continue
    
    print("❌ Could not connect to Redis using any of the attempted URLs")
    return False

if __name__ == "__main__":
    print("Testing Redis connectivity...")
    test_redis_connection()
    print("Redis connectivity test complete.")