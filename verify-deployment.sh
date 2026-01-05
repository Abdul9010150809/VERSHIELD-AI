#!/bin/bash
# VeriShield AI Local Deployment Verification Script

echo "======================================"
echo "VeriShield AI - Deployment Verification"
echo "======================================"
echo ""

# Check prerequisites
echo "1. Checking Prerequisites..."
echo "   - Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "     ❌ Docker is not installed"
    exit 1
fi
echo "     ✅ Docker found: $(docker --version)"

echo "   - Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "     ❌ Docker Compose is not installed"
    exit 1
fi
echo "     ✅ Docker Compose found: $(docker-compose --version)"

echo "   - Checking .env.local..."
if [ ! -f .env.local ]; then
    echo "     ❌ .env.local not found"
    exit 1
fi
echo "     ✅ .env.local exists"

echo ""
echo "2. Checking Python Environment..."
if ! python3 -c "import fastapi, uvicorn, redis, pydantic" 2>/dev/null; then
    echo "   ⚠️  Some Python dependencies may be missing locally"
    echo "      (They will be installed in Docker containers)"
fi

echo ""
echo "3. Checking Git Status..."
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "   ⚠️  Not a git repository"
else
    echo "   ✅ Git repository found"
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    echo "      Current branch: $BRANCH"
fi

echo ""
echo "4. Environment Configuration Check..."
OPENAI_KEY=$(grep "OPENAI_API_KEY" .env.local | cut -d '=' -f 2)
if [ -z "$OPENAI_KEY" ] || [ "$OPENAI_KEY" = "sk-proj-test-key-local-dev-mode" ]; then
    echo "   ⚠️  OPENAI_API_KEY is using default/test value"
    echo "      Update .env.local with a real OpenAI API key for full functionality"
else
    echo "   ✅ OPENAI_API_KEY is configured"
fi

echo ""
echo "======================================"
echo "✅ System is ready for deployment!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Update .env.local with your API keys if needed"
echo "  2. Run: chmod +x start.sh"
echo "  3. Run: ./start.sh"
echo ""
echo "Access points:"
echo "  - Frontend:  http://localhost:3000"
echo "  - Backend:   http://localhost:8000"
echo "  - API Docs:  http://localhost:8000/docs"
echo ""
