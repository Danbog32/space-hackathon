#!/usr/bin/env python3
"""
Test script for the AI microservice.
Tests all major functionality to ensure everything works correctly.
"""

import requests
import json
import time
import base64
from pathlib import Path
from PIL import Image
import numpy as np

# Configuration
AI_SERVICE_URL = "http://localhost:8001"
TEST_IMAGE_SIZE = (256, 256)

def create_test_image():
    """Create a simple test image for segmentation."""
    # Create a simple test image with a circle
    img = Image.new('RGB', TEST_IMAGE_SIZE, color='white')
    pixels = np.array(img)
    
    # Draw a circle
    center = (TEST_IMAGE_SIZE[0] // 2, TEST_IMAGE_SIZE[1] // 2)
    radius = 50
    y, x = np.ogrid[:TEST_IMAGE_SIZE[1], :TEST_IMAGE_SIZE[0]]
    mask = (x - center[0])**2 + (y - center[1])**2 <= radius**2
    pixels[mask] = [255, 0, 0]  # Red circle
    
    return Image.fromarray(pixels)

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{AI_SERVICE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_datasets():
    """Test datasets endpoint."""
    print("\n📁 Testing datasets endpoint...")
    try:
        response = requests.get(f"{AI_SERVICE_URL}/datasets")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Datasets retrieved: {len(data.get('datasets', []))} datasets")
            return True
        else:
            print(f"❌ Datasets request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Datasets error: {e}")
        return False

def test_search():
    """Test search functionality."""
    print("\n🔍 Testing search functionality...")
    try:
        # Test basic search
        response = requests.get(f"{AI_SERVICE_URL}/search?q=star&k=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search completed: {data.get('count', 0)} results")
            print(f"   Query: {data.get('query')}")
            print(f"   Search time: {data.get('search_time_ms', 0)}ms")
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def test_embedding():
    """Test text embedding."""
    print("\n🧠 Testing text embedding...")
    try:
        response = requests.get(f"{AI_SERVICE_URL}/embed?text=galaxy%20spiral")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Embedding generated: {data.get('embedding_dim', 0)} dimensions")
            return True
        else:
            print(f"❌ Embedding failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return False

def test_sam_status():
    """Test SAM status."""
    print("\n🎯 Testing SAM status...")
    try:
        response = requests.get(f"{AI_SERVICE_URL}/sam/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('available'):
                print(f"✅ SAM available: {data.get('info', {}).get('model_type', 'unknown')}")
                return True
            else:
                print(f"⚠️  SAM not available: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ SAM status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SAM status error: {e}")
        return False

def test_segmentation():
    """Test SAM segmentation."""
    print("\n🎯 Testing SAM segmentation...")
    try:
        # Create test image
        test_img = create_test_image()
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        test_img.save(buffer, format='PNG')
        img_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Test segmentation
        payload = {
            "image_data": img_b64,
            "points": [[128, 128]],  # Center point
            "labels": [1],  # Foreground
            "bbox": [50, 50, 200, 200]  # Bounding box
        }
        
        response = requests.post(f"{AI_SERVICE_URL}/segment", json=payload)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Segmentation completed successfully")
                return True
            else:
                print(f"❌ Segmentation failed: {data}")
                return False
        else:
            print(f"❌ Segmentation request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Segmentation error: {e}")
        return False

def test_model_info():
    """Test model information endpoint."""
    print("\n📊 Testing model information...")
    try:
        response = requests.get(f"{AI_SERVICE_URL}/models/info")
        if response.status_code == 200:
            data = response.json()
            clip_info = data.get('clip', {})
            sam_info = data.get('sam')
            datasets = data.get('datasets', [])
            
            print(f"✅ Model info retrieved:")
            print(f"   CLIP: {clip_info.get('model_name', 'unknown')} on {clip_info.get('device', 'unknown')}")
            print(f"   SAM: {'Available' if sam_info else 'Not available'}")
            print(f"   Datasets: {len(datasets)} available")
            return True
        else:
            print(f"❌ Model info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model info error: {e}")
        return False

def test_cache():
    """Test search cache functionality."""
    print("\n💾 Testing search cache...")
    try:
        # First search (should be cached)
        start_time = time.time()
        response1 = requests.get(f"{AI_SERVICE_URL}/search?q=cache_test&k=3")
        time1 = time.time() - start_time
        
        # Second search (should hit cache)
        start_time = time.time()
        response2 = requests.get(f"{AI_SERVICE_URL}/search?q=cache_test&k=3")
        time2 = time.time() - start_time
        
        if response1.status_code == 200 and response2.status_code == 200:
            data1 = response1.json()
            data2 = response2.json()
            
            print(f"✅ Cache test completed:")
            print(f"   First search: {time1*1000:.1f}ms")
            print(f"   Second search: {time2*1000:.1f}ms")
            print(f"   Cached: {data2.get('cached', False)}")
            return True
        else:
            print(f"❌ Cache test failed")
            return False
    except Exception as e:
        print(f"❌ Cache test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting AI Service Tests")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Datasets", test_datasets),
        ("Search", test_search),
        ("Embedding", test_embedding),
        ("SAM Status", test_sam_status),
        ("Segmentation", test_segmentation),
        ("Model Info", test_model_info),
        ("Cache", test_cache),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI service is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit(main())
