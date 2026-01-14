# test/test_cache.py
"""
Test the response cache module.
"""
import sys
sys.path.insert(0, r"e:\finance-ai")

import time
from src.cache.response_cache import ResponseCache, get_cache, cached_query, cache_response


def test_cache():
    """Test cache basic operations."""
    print("\n" + "="*60)
    print("CACHE MODULE TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Initialize cache
    print("\n📦 Test 1: Cache Initialization")
    cache = get_cache()
    stats = cache.stats()
    print(f"   Initialized: size={stats['size']}, max={stats['max_size']}")
    results.append(("Initialization", stats['max_size'] == 100))
    
    # Test 2: Store and retrieve
    print("\n💾 Test 2: Store and Retrieve")
    cache_response("What is the revenue?", "Revenue is $90.7 billion", None, "test-session")
    result = cached_query("What is the revenue?", "test-session")
    passed = result is not None and "90.7 billion" in result[0]
    print(f"   Stored and retrieved: {'PASS' if passed else 'FAIL'}")
    results.append(("Store/Retrieve", passed))
    
    # Test 3: Cache hit tracking
    print("\n📊 Test 3: Hit Tracking")
    stats = cache.stats()
    passed = stats['hits'] >= 1
    print(f"   Hits: {stats['hits']}, Misses: {stats['misses']}")
    results.append(("Hit Tracking", passed))
    
    # Test 4: Case insensitivity
    print("\n🔤 Test 4: Case Insensitivity")
    result = cached_query("WHAT IS THE REVENUE?", "test-session")
    passed = result is not None
    print(f"   Same key for different case: {'PASS' if passed else 'FAIL'}")
    results.append(("Case Insensitive", passed))
    
    # Test 5: Different sessions
    print("\n🔒 Test 5: Session Isolation")
    result = cached_query("What is the revenue?", "different-session")
    passed = result is None  # Should NOT find it (different session)
    print(f"   Isolated by session: {'PASS' if passed else 'FAIL'}")
    results.append(("Session Isolation", passed))
    
    # Test 6: Clear cache
    print("\n🧹 Test 6: Clear Cache")
    cache.clear()
    stats = cache.stats()
    passed = stats['size'] == 0 and stats['hits'] == 0
    print(f"   Cleared: size={stats['size']}")
    results.append(("Clear", passed))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} | {name}")
    
    print(f"\n🏁 TOTAL: {passed_count}/{total} tests passed")
    
    return passed_count == total


if __name__ == "__main__":
    success = test_cache()
    exit(0 if success else 1)
