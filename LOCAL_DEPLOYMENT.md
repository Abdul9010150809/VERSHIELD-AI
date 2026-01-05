# VeriShield AI - Local Deployment Guide

## System Requirements

### Minimum Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 10GB for Docker images and data

### API Keys Required

- **OpenAI API Key**: Required for basic functionality (<https://platform.openai.com/api-keys>)
- **Optional**: Azure credentials for advanced features

---

## Quick Start (5 minutes)

### Step 1: Clone & Navigate

```bash
git clone https://github.com/Abdul9010150809/VERSHIELD-AI.git
cd VERSHIELD-AI
```

### Step 2: Set Permissions

```bash
chmod +x start.sh verify-deployment.sh
```

### Step 3: Verify System

```bash
./verify-deployment.sh
```

### Step 4: Configure Environment

Edit `.env.local` and set your OpenAI API key:

```bash
nano .env.local
# Change: OPENAI_API_KEY=sk-proj-test-key-local-dev-mode
# To:     OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 5: Start Services

```bash
./start.sh
```

Wait 10-15 seconds for services to start up completely.

---

## Service Access Points

### Frontend

- **URL**: <http://localhost:3000>
- **Purpose**: Web interface for threat analysis and FinOps dashboard
- **Tech**: Next.js 14

### Backend API

- **URL**: <http://localhost:8000>
- **Purpose**: REST API endpoints for all features
- **Tech**: FastAPI

### Interactive API Documentation

- **URL**: <http://localhost:8000/docs>
- **Purpose**: Swagger UI with interactive endpoint testing
- **Tech**: OpenAPI/Swagger

### Optional Management Tools

```bash
# Start additional management UIs (PGAdmin, Redis Commander)
docker-compose --profile tools up -d

# PGAdmin: http://localhost:5050
# Credentials: admin@verishield.ai / admin

# Redis Commander: http://localhost:8081
```

---

## Testing Features

### 1. Test API Connectivity

```bash
curl http://localhost:8000/

# Expected response:
# {"message": "Welcome to VeriShield AI..."}
```

### 2. Test Sentiment Analysis

```bash
curl -X POST http://localhost:8000/api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is great news!", "language": "en"}'
```

### 3. Test Semantic Cache

```bash
curl -X GET http://localhost:8000/api/cache/stats
```

### 4. Test FinOps Dashboard

```bash
curl http://localhost:8000/api/finops/stats
```

### 5. Test Metrics Endpoint

```bash
curl http://localhost:8000/api/metrics
```

---

## Monitoring & Troubleshooting

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

### Check Service Status

```bash
docker-compose ps

# Expected output:
# NAME       STATUS      PORTS
# backend    running     0.0.0.0:8000->8000/tcp
# frontend   running     0.0.0.0:3000->3000/tcp
# db         running     0.0.0.0:5432->5432/tcp
# redis      running     0.0.0.0:6379->6379/tcp
```

### Common Issues & Solutions

#### Issue: "docker-compose: command not found"

```bash
# Install Docker Compose
sudo apt-get install docker-compose
# or on macOS:
brew install docker-compose
```

#### Issue: Port 3000/8000 already in use

```bash
# List process using port
sudo lsof -i :3000
sudo lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### Issue: "Database connection refused"

```bash
# Wait longer for PostgreSQL to start (up to 30 seconds)
# Check database logs
docker-compose logs db

# Restart database service
docker-compose restart db
```

#### Issue: "Redis connection refused"

```bash
# Restart Redis
docker-compose restart redis

# Test Redis connectivity
docker-compose exec redis redis-cli ping
```

#### Issue: "Out of memory" or crashes

```bash
# Increase Docker memory limit (Docker Desktop)
# or restart with explicit resource limits

docker-compose down
docker system prune -a  # Clean up unused images
docker-compose up -d
```

---

## Environment Variables

### Required for All Features

```
OPENAI_API_KEY=your_key_here
```

### Feature Toggles (false by default)

```
ENABLE_PII_REDACTION=false      # Requires Azure Language Service
ENABLE_CONTENT_SAFETY=false     # Requires Azure Content Safety
ENABLE_SEMANTIC_CACHE=true      # Uses local Redis
ENABLE_VECTOR_RAG=false         # Requires Azure Search
ENABLE_FINOPS_TRACKING=true     # Uses local Redis
ENABLE_COMPLIANCE_AUDIT=true    # Uses local Redis
ENABLE_ENTRA_AUTH=false         # Requires Azure Entra ID
```

### Optional Azure Services

```
AZURE_LANGUAGE_ENDPOINT=        # For PII redaction
AZURE_LANGUAGE_KEY=             
AZURE_CONTENT_SAFETY_ENDPOINT=  # For content moderation
AZURE_CONTENT_SAFETY_KEY=       
AZURE_SEARCH_ENDPOINT=          # For vector RAG
AZURE_SEARCH_KEY=               
AZURE_SPEECH_KEY=               # For audio analysis
AZURE_SPEECH_REGION=            
```

---

## Stopping Services

### Stop All Services

```bash
docker-compose down
```

### Stop with Volume Cleanup

```bash
docker-compose down -v
```

### Stop Specific Service

```bash
docker-compose stop backend
docker-compose stop frontend
```

---

## Database & Persistence

### Database

- **Type**: PostgreSQL 15
- **Host**: localhost:5432 (from host machine)
- **Credentials**:
  - User: `verishield_user`
  - Password: `verishield_pass`
  - Database: `verishield`
- **Data Persistence**: Volume mounted at `postgres_data/`

### Cache

- **Type**: Redis 7
- **Host**: localhost:6379 (from host machine)
- **Data Persistence**: Volume mounted at `redis_data/`

### Reset Data

```bash
# Remove all data volumes (DESTRUCTIVE)
docker-compose down -v

# Restart services - database will reinitialize
docker-compose up -d
```

---

## Performance Tuning

### Increase Resources for Development

Edit `docker-compose.yml`:

```yaml
backend:
  # Add resource limits
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

### Enable Debug Logging

In `.env.local`:

```
LOG_LEVEL=DEBUG
DEBUG=true
```

---

## Production Deployment

For production deployment to Azure:

- See `docs/AZURE_ENTERPRISE_ARCHITECTURE.md`
- Review `infrastructure/terraform/` for IaC setup
- See `IMPLEMENTATION_SUMMARY.md` for architecture details

---

## Support & Debugging

### Check System Health

```bash
./verify-deployment.sh
```

### View Docker Container Logs

```bash
docker-compose logs --tail 50 backend
docker-compose logs --tail 50 frontend
```

### Test Database Connection

```bash
docker-compose exec db psql -U verishield_user -d verishield -c "SELECT 1"
```

### Test API with curl

```bash
# Health check
curl -v http://localhost:8000/

# With JSON response
curl -s http://localhost:8000/ | python3 -m json.tool
```

---

## Next Steps

1. ✅ Run `./verify-deployment.sh` to ensure readiness
2. ✅ Update `.env.local` with API keys
3. ✅ Run `./start.sh` to start all services
4. ✅ Access <http://localhost:3000> to see the web interface
5. ✅ Check <http://localhost:8000/docs> for API testing

For feature-specific setup, see:

- `SETUP_GUIDE.md` - Detailed component setup
- `LAUNCH_CHECKLIST.md` - Pre-launch verification
- `IMPLEMENTATION_SUMMARY.md` - Architecture overview
