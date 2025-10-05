#!/usr/bin/env python3
"""
Test the AI service endpoints.
"""

import requests
import time
import json

def test_service():
    """Test all AI service endpoints."""
    base_url = "http://localhost:8001"
    
    print("🧪 Testing AI Service...")
    print("=" * 50)
    
    # Test health
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test datasets
    try:
        response = requests.get(f"{base_url}/datasets", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Datasets: {len(data.get('datasets', []))} available")
        else:
            print(f"❌ Datasets failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Datasets error: {e}")
    
    # Test search
    try:
        response = requests.get(f"{base_url}/search?q=star%20cluster&k=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search: {data.get('count', 0)} results for 'star cluster'")
            print(f"   Query: {data.get('query')}")
            print(f"   Search time: {data.get('search_time_ms', 0)}ms")
        else:
            print(f"❌ Search failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    # Test embedding
    try:
        response = requests.get(f"{base_url}/embed?text=galaxy", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Embedding: {data.get('embedding_dim', 0)} dimensions")
        else:
            print(f"❌ Embedding failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Embedding error: {e}")
    
    # Test model info
    try:
        response = requests.get(f"{base_url}/models/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model Info: {data.get('clip', {}).get('model_name', 'unknown')}")
        else:
            print(f"❌ Model info failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Model info error: {e}")
    
    print("=" * 50)
    print("🎉 AI Service testing completed!")
    return True

if __name__ == "__main__":
    test_service()
