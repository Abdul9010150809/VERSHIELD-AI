#!/bin/bash
# VeriShield AI - Feature Test Suite
# Tests all implemented features to verify they're working

echo "🧪 VeriShield AI - Feature Test Suite"
echo "======================================"
echo ""

BASE_URL="http://localhost:8000"
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -n "Testing $name... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi
    
    if [ "$response" == "200" ] || [ "$response" == "201" ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED (HTTP $response)${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Check if backend is running
echo "Checking if backend is running..."
if ! curl -s "$BASE_URL/" > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend is not running at $BASE_URL${NC}"
    echo "Please start the services first:"
    echo "  ./start.sh"
    exit 1
fi

echo -e "${GREEN}✅ Backend is running${NC}"
echo ""

# Test Root Endpoint
echo "📌 Testing Core Endpoints"
echo "------------------------"
test_endpoint "Root endpoint" "GET" "/"
test_endpoint "Metrics endpoint" "GET" "/api/metrics"
echo ""

# Test PII Redaction
echo "🔒 Testing PII Redaction"
echo "------------------------"
test_endpoint "PII Detection" "POST" "/api/pii/detect" \
    '{"text": "My email is john.doe@example.com and my phone is 555-123-4567"}'
test_endpoint "PII Redaction" "POST" "/api/pii/redact" \
    '{"text": "Contact me at john@example.com", "strategy": "mask"}'
test_endpoint "PII Summary" "POST" "/api/pii/summary" \
    '{"text": "SSN: 123-45-6789, Card: 4532-1234-5678-9010"}'
echo ""

# Test Content Safety
echo "🛡️  Testing Content Safety"
echo "------------------------"
test_endpoint "Text Safety Analysis" "POST" "/api/safety/analyze-text" \
    '{"text": "This is a test message for safety analysis"}'
echo ""

# Test Semantic Cache
echo "💾 Testing Semantic Cache"
echo "------------------------"
test_endpoint "Cache Stats" "GET" "/api/cache/stats"
test_endpoint "Cache Query" "POST" "/api/cache/query" \
    '{"query": "What is machine learning?"}'
echo ""

# Test Vector RAG
echo "🔍 Testing Vector RAG"
echo "------------------------"
test_endpoint "Vector Search" "POST" "/api/rag/search" \
    '{"query": "artificial intelligence", "top_k": 3}'
echo ""

# Test FinOps
echo "💰 Testing FinOps Tracking"
echo "------------------------"
test_endpoint "FinOps Dashboard" "GET" "/api/finops/dashboard"
test_endpoint "FinOps Stats" "GET" "/api/finops/stats"
echo ""

# Test Sentiment Analysis
echo "😊 Testing Sentiment Analysis"
echo "------------------------"
test_endpoint "Sentiment Analysis" "POST" "/api/sentiment/analyze" \
    '{"text": "I love this product! It works great!"}'
test_endpoint "Comprehensive Analysis" "POST" "/api/sentiment/comprehensive" \
    '{"text": "The service was excellent and the team was very helpful."}'
echo ""

# Test Compliance (without auth for basic test)
echo "📋 Testing Compliance Auditing"
echo "------------------------"
# Note: These may require authentication in production
echo "⚠️  Compliance endpoints require authentication (skipping for basic test)"
echo ""

# Summary
echo ""
echo "======================================"
echo "📊 Test Summary"
echo "======================================"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "✨ VeriShield AI is working correctly!"
    echo ""
    echo "Next steps:"
    echo "1. Configure Azure services in .env.local for advanced features"
    echo "2. Visit http://localhost:3000 to use the frontend"
    echo "3. View API docs at http://localhost:8000/docs"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed${NC}"
    echo ""
    echo "This is normal if:"
    echo "- Azure service credentials are not configured"
    echo "- You're running with minimal configuration"
    echo ""
    echo "Basic features (cache, FinOps, compliance) should work with just OpenAI key."
    echo "Advanced features require Azure service credentials in .env.local"
    exit 1
fi
