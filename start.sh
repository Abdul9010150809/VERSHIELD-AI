#!/bin/bash
# Start VeriShield AI Platform - Enhanced startup script

set -e  # Exit on first error

echo "🚀 Starting VeriShield AI Platform..."
echo ""

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "⚠️  .env.local not found. Creating from template..."
    if [ -f .env.template ]; then
        cp .env.template .env.local
    else
        # Create minimal .env.local
        cat > .env.local << 'EOF'
# Local Development Environment
DATABASE_URL=postgresql://verishield_user:verishield_pass@db:5432/verishield
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=sk-proj-test-key-local-dev-mode
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars-12345
ENABLE_SEMANTIC_CACHE=true
ENABLE_FINOPS_TRACKING=true
ENABLE_COMPLIANCE_AUDIT=true
EOF
    fi
    echo "📝 Created .env.local - Please edit and add your OPENAI_API_KEY"
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    echo ""
    echo "On Linux:"
    echo "  sudo systemctl start docker"
    echo ""
    echo "On macOS:"
    echo "  open /Applications/Docker.app"
    echo ""
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "✅ VeriShield AI is starting up!"
echo ""
echo "📊 Services:"
echo "   - Frontend:       http://localhost:3000"
echo "   - Backend API:    http://localhost:8000"
echo "   - API Docs:       http://localhost:8000/docs"
echo "   - PostgreSQL:     localhost:5432"
echo "   - Redis:          localhost:6379"
echo ""
echo "🛠️  Optional Management Tools:"
echo "   docker-compose --profile tools up -d"
echo "   - PGAdmin:        http://localhost:5050"
echo "   - Redis Commander: http://localhost:8081"
echo ""
echo "📋 View logs:       docker-compose logs -f"
echo "🛑 Stop services:   docker-compose down"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
RETRY_COUNT=0
MAX_RETRIES=30

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    elif curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        sleep 1
    fi
done

if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "⚠️  Backend is still starting... This is normal for first run."
    echo "    Check logs with: docker-compose logs backend"
fi

echo ""
echo "🎉 Ready to use VeriShield AI!"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Try the API at http://localhost:8000/docs"
echo "  3. Check logs: docker-compose logs -f"
echo ""
