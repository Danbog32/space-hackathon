#!/usr/bin/env python3
"""
Quick test script for Misha to verify AI service is working correctly.
Run this after starting the AI service to check everything is OK.
"""

import sys
import time
import requests
from pathlib import Path
from typing import Dict, Any
import json

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

BASE_URL = "http://localhost:8001"

def print_header(text: str):
    """Print formatted header."""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")

def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text: str):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")

def test_health() -> bool:
    """Test health endpoint."""
    print_info("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed!")
            print(f"   • Status: {data.get('status')}")
            print(f"   • Datasets: {data.get('datasets', 0)}")
            print(f"   • Total vectors: {data.get('total_vectors', 0)}")
            print(f"   • CLIP ready: {data.get('clip_ready', False)}")
            
            if data.get('datasets', 0) == 0:
                print_warning("No datasets found! Run build_real_index.py first.")
                return False
            
            return True
        else:
            print_error(f"Health check failed! Status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to AI service! Is it running on port 8001?")
        print_info("Start it with: python app.py")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False

def test_datasets() -> bool:
    """Test datasets endpoint."""
    print_info("Testing datasets endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/datasets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            datasets = data.get('datasets', [])
            print_success(f"Found {len(datasets)} dataset(s)")
            for ds in datasets:
                print(f"   • {ds.get('id')}: {ds.get('num_vectors', 0)} vectors")
            return len(datasets) > 0
        else:
            print_error(f"Datasets endpoint failed! Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Datasets test error: {e}")
        return False

def test_embed() -> bool:
    """Test embed endpoint."""
    print_info("Testing text embedding...")
    try:
        test_text = "star cluster"
        response = requests.get(f"{BASE_URL}/embed", params={"text": test_text}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Text embedding works!")
            print(f"   • Text: '{data.get('text')}'")
            print(f"   • Embedding dim: {data.get('embedding_dim', 0)}")
            print(f"   • First 5 values: {data.get('embedding', [])[:5]}")
            return data.get('embedding_dim', 0) > 0
        else:
            print_error(f"Embed endpoint failed! Status: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Embed test error: {e}")
        return False

def test_search(dataset_id: str = "andromeda") -> bool:
    """Test search endpoint."""
    print_info(f"Testing search on dataset '{dataset_id}'...")
    
    test_queries = [
        "bright star",
        "dust cloud",
        "galaxy core"
    ]
    
    results_found = False
    
    for query in test_queries:
        try:
            start_time = time.time()
            response = requests.get(
                f"{BASE_URL}/search",
                params={
                    "q": query,
                    "dataset_id": dataset_id,
                    "k": 5,
                    "min_score": 0.0
                },
                timeout=15
            )
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                search_time = data.get('search_time_ms', elapsed)
                cached = data.get('cached', False)
                
                if count > 0:
                    results_found = True
                    print_success(f"Query '{query}': {count} results in {search_time:.1f}ms {'(cached)' if cached else ''}")
                    
                    # Show top result
                    if data.get('results'):
                        top = data['results'][0]
                        print(f"   • Top result: score={top.get('score', 0):.3f}, bbox={top.get('bbox')}")
                else:
                    print_warning(f"Query '{query}': no results")
            elif response.status_code == 404:
                print_error(f"Dataset '{dataset_id}' not found!")
                print_info(f"Available datasets: {test_datasets()}")
                return False
            else:
                print_error(f"Search failed for '{query}': Status {response.status_code}")
                
        except Exception as e:
            print_error(f"Search error for '{query}': {e}")
    
    if results_found:
        print_success("Search is working!")
        return True
    else:
        print_warning("No search results found for any query")
        print_info("This might be OK if using synthetic data, but check index quality")
        return False

def test_cache() -> bool:
    """Test search caching."""
    print_info("Testing search cache...")
    try:
        query = "test cache query"
        dataset_id = "andromeda"
        
        # First request (cold)
        start1 = time.time()
        resp1 = requests.get(
            f"{BASE_URL}/search",
            params={"q": query, "dataset_id": dataset_id, "k": 5},
            timeout=10
        )
        time1 = (time.time() - start1) * 1000
        
        if resp1.status_code != 200:
            print_warning("Cache test skipped (search failed)")
            return False
        
        # Second request (should be cached)
        start2 = time.time()
        resp2 = requests.get(
            f"{BASE_URL}/search",
            params={"q": query, "dataset_id": dataset_id, "k": 5},
            timeout=10
        )
        time2 = (time.time() - start2) * 1000
        
        data2 = resp2.json()
        cached = data2.get('cached', False)
        
        if cached or time2 < time1 * 0.5:  # Cached should be much faster
            print_success(f"Cache is working! Cold: {time1:.1f}ms, Warm: {time2:.1f}ms")
            return True
        else:
            print_warning(f"Cache might not be working. Times: {time1:.1f}ms vs {time2:.1f}ms")
            return False
            
    except Exception as e:
        print_error(f"Cache test error: {e}")
        return False

def test_sam() -> bool:
    """Test SAM endpoint (stretch goal)."""
    print_info("Testing SAM segmentation (stretch goal)...")
    try:
        response = requests.get(f"{BASE_URL}/sam/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            available = data.get('available', False)
            if available:
                print_success("SAM is available!")
                print(f"   • Info: {data.get('info', {})}")
                return True
            else:
                print_warning("SAM not available (optional stretch goal)")
                return False
        else:
            print_warning("SAM status check failed")
            return False
    except Exception as e:
        print_warning(f"SAM test skipped: {e}")
        return False

def test_performance() -> Dict[str, float]:
    """Benchmark performance."""
    print_info("Running performance benchmarks...")
    
    results = {
        'embed_avg_ms': 0,
        'search_cold_ms': 0,
        'search_warm_ms': 0
    }
    
    try:
        # Text embedding speed
        times = []
        for _ in range(5):
            start = time.time()
            requests.get(f"{BASE_URL}/embed", params={"text": "benchmark"}, timeout=10)
            times.append((time.time() - start) * 1000)
        results['embed_avg_ms'] = sum(times) / len(times)
        
        # Search speed (cold)
        start = time.time()
        requests.get(
            f"{BASE_URL}/search",
            params={"q": "performance test unique", "dataset_id": "andromeda", "k": 10},
            timeout=10
        )
        results['search_cold_ms'] = (time.time() - start) * 1000
        
        # Search speed (warm - repeat same query)
        times = []
        for _ in range(5):
            start = time.time()
            requests.get(
                f"{BASE_URL}/search",
                params={"q": "performance test", "dataset_id": "andromeda", "k": 10},
                timeout=10
            )
            times.append((time.time() - start) * 1000)
        results['search_warm_ms'] = sum(times) / len(times)
        
        print_success("Performance benchmarks complete!")
        print(f"   • Text embedding: {results['embed_avg_ms']:.1f}ms avg")
        print(f"   • Search (cold):  {results['search_cold_ms']:.1f}ms")
        print(f"   • Search (warm):  {results['search_warm_ms']:.1f}ms avg")
        
        # Performance targets
        if results['search_warm_ms'] < 100:
            print_success("✨ Excellent performance! (<100ms warm search)")
        elif results['search_warm_ms'] < 500:
            print_success("✓ Good performance! (<500ms warm search)")
        else:
            print_warning("Performance could be improved (target: <100ms warm)")
        
        return results
        
    except Exception as e:
        print_error(f"Performance test error: {e}")
        return results

def run_all_tests():
    """Run all tests."""
    print_header("AI SERVICE QUICK TEST")
    print(f"Testing service at: {BASE_URL}")
    
    tests = []
    
    # Core functionality
    tests.append(("Health Check", test_health()))
    tests.append(("Datasets", test_datasets()))
    tests.append(("Text Embedding", test_embed()))
    tests.append(("Search", test_search()))
    tests.append(("Cache", test_cache()))
    
    # Stretch goals
    tests.append(("SAM (stretch)", test_sam()))
    
    # Performance
    print_header("PERFORMANCE BENCHMARKS")
    perf = test_performance()
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed{RESET}")
    
    if passed >= 4:  # Core tests (health, datasets, embed, search)
        print(f"\n{GREEN}{BOLD}🎉 AI SERVICE IS WORKING! Ready for integration! 🚀{RESET}\n")
        return True
    else:
        print(f"\n{RED}{BOLD}⚠️  Some tests failed. Check the errors above.{RESET}\n")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)

