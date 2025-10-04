#!/bin/bash
# Quick test script for tile serving

set -e

echo "======================================"
echo "Tile Serving Test Suite"
echo "======================================"
echo ""

API_URL="${API_URL:-http://localhost:8000}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testing $name... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $status)"
        return 1
    fi
}

# Check if API is running
echo "Checking API availability..."
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}Error: API not running at $API_URL${NC}"
    echo "Start the API with: cd apps/api && make dev"
    exit 1
fi
echo -e "${GREEN}✓ API is running${NC}"
echo ""

# Test suite
echo "Running tile serving tests..."
echo ""

PASSED=0
FAILED=0

# Test 1: DZI metadata
if test_endpoint "DZI metadata" "$API_URL/tiles/andromeda/info.dzi"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 2: Level 0 tile
if test_endpoint "Level 0 tile" "$API_URL/tiles/andromeda/0/0_0.jpg"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 3: Level 1 tile
if test_endpoint "Level 1 tile" "$API_URL/tiles/andromeda/1/0_0.jpg"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 4: Level 2 tile
if test_endpoint "Level 2 tile" "$API_URL/tiles/andromeda/2/0_0.jpg"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 5: Thumbnail
if test_endpoint "Thumbnail" "$API_URL/tiles/andromeda/thumbnail.jpg"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Test 6: Check cache headers
echo -n "Testing cache headers... "
cache_header=$(curl -s -I "$API_URL/tiles/andromeda/0/0_0.jpg" | grep -i "cache-control")
if echo "$cache_header" | grep -q "max-age=31536000"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Got: $cache_header"
    ((FAILED++))
fi

# Test 7: WebP support (if available)
echo -n "Testing WebP support... "
webp_response=$(curl -s -I -H "Accept: image/webp,image/*" "$API_URL/tiles/andromeda/0/0_0.jpg")
content_type=$(echo "$webp_response" | grep -i "content-type")
if echo "$content_type" | grep -q "webp"; then
    echo -e "${GREEN}✓ PASS${NC} (WebP served)"
    ((PASSED++))
elif echo "$content_type" | grep -q "jpeg"; then
    echo -e "${YELLOW}⚠ SKIP${NC} (WebP not available, JPEG served)"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Got: $content_type"
    ((FAILED++))
fi

echo ""
echo "======================================"
echo "Results"
echo "======================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "Failed: ${RED}$FAILED${NC}"
else
    echo -e "Failed: $FAILED"
fi
echo ""

# Overall result
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed ✗${NC}"
    exit 1
fi

