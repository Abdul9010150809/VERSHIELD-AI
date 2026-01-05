# 🚀 VeriShield AI - Local Deployment Guide

## Prerequisites (Install Once)

### 1. Docker Desktop
Download and install from: https://www.docker.com/products/docker-desktop

Verify installation:
```bash
docker --version        # Docker 20.10+
docker-compose --version # Docker Compose 2.0+
```

### 2. OpenAI API Key
Get from: https://platform.openai.com/api-keys (required for backend)

---

## 5-Step Local Deployment

### Step 1: Navigate to Project
```bash
cd /path/to/VERSHIELD-AI
```

### Step 2: Verify System Ready
```bash
chmod +x verify-deployment.sh
./verify-deployment.sh
```

Expected output: ✅ All checks pass

### Step 3: Configure Environment
```bash
nano .env.local
```

Update the line:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

Save (Ctrl+X, Y, Enter for nano)

### Step 4: Start Services
```bash
chmod +x start.sh
./start.sh
```

Wait for output: **"Backend is ready!"** (takes 10-30 seconds on first run)

### Step 5: Access Services

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Verify Deployment

### Check All Services Running
```bash
docker-compose ps
```

Expected status: **Up** for all containers

```
NAME       STATUS      PORTS
backend    Up          0.0.0.0:8000->8000/tcp
frontend   Up          0.0.0.0:3000->3000/tcp
db         Up          0.0.0.0:5432->5432/tcp
redis      Up          0.0.0.0:6379->6379/tcp
```

### Test API Health
```bash
curl http://localhost:8000/health
```

### Open Frontend in Browser
```bash
# macOS
open http://localhost:3000

# Linux
xdg-open http://localhost:3000

# Windows
start http://localhost:3000
```

---

## Quick API Tests

### 1. Health Check
```bash
curl http://localhost:8000/health | python3 -m json.tool
```

### 2. Get Metrics
```bash
curl http://localhost:8000/api/metrics | python3 -m json.tool
```

### 3. Sentiment Analysis
```bash
curl -X POST http://localhost:8000/api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is amazing!", "language": "en"}'
```

### 4. Cache Stats
```bash
curl http://localhost:8000/api/cache/stats | python3 -m json.tool
```

### 5. FinOps Dashboard
```bash
curl http://localhost:8000/api/finops/stats | python3 -m json.tool
```

---

## Service Details

### Backend (FastAPI) - Port 8000
- REST API endpoints
- Interactive documentation: http://localhost:8000/docs
- WebSocket for real-time updates
- Health check: http://localhost:8000/health

### Frontend (Next.js) - Port 3000
- Web interface
- Dashboards
- Real-time monitoring
- Auto-reload on code changes

### Database (PostgreSQL) - Port 5432
- verishield database
- User: verishield_user
- Data persists in `postgres_data/` volume

### Cache (Redis) - Port 6379
- Semantic caching
- FinOps tracking
- Session storage
- Data persists in `redis_data/` volume

---

## Common Commands

### View Live Logs
```bash
docker-compose logs -f              # All services
docker-compose logs -f backend      # Backend only
docker-compose logs -f frontend     # Frontend only
```

### Stop Services (Data Preserved)
```bash
docker-compose down
```

### Stop & Remove Data
```bash
docker-compose down -v
docker system prune -a
```

### Restart Services
```bash
docker-compose restart              # All
docker-compose restart backend      # Backend only
```

### Access Database
```bash
docker-compose exec db psql -U verishield_user -d verishield
```

### Access Redis
```bash
docker-compose exec redis redis-cli
```

---

## Troubleshooting

### Docker not found
Install Docker Desktop: https://www.docker.com/products/docker-desktop

### Port already in use
```bash
# Find what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Backend not starting
```bash
# Check logs
docker-compose logs backend

# Rebuild
docker-compose build --no-cache backend
```

### Frontend not loading
```bash
# Check logs
docker-compose logs frontend

# Restart
docker-compose restart frontend
```

### API returns errors
1. Check `.env.local` has valid `OPENAI_API_KEY`
2. View backend logs: `docker-compose logs backend`
3. Verify Redis: `docker-compose logs redis`
4. Check database: `docker-compose logs db`

---

## Success Indicators

✅ All containers show `Up` in `docker-compose ps`
✅ Frontend loads at http://localhost:3000
✅ API responds at http://localhost:8000/docs
✅ Health check shows `"status": "healthy"`
✅ No error messages in logs

---

## Next Steps

1. **Explore API**: Visit http://localhost:8000/docs
2. **View Dashboard**: Open http://localhost:3000
3. **Test Endpoints**: Use curl examples above
4. **Enable Features**: Edit `.env.local` to enable optional features
5. **Read Docs**: See `LOCAL_DEPLOYMENT.md` for detailed setup

---

## Documentation

- **Quick Start**: `QUICK_START.md`
- **Detailed Setup**: `LOCAL_DEPLOYMENT.md`
- **Troubleshooting**: `TROUBLESHOOTING.md`
- **Deployment Checklist**: `DEPLOYMENT_CHECKLIST.md`
- **Developer Reference**: `DEVELOPER_REFERENCE.md`

---

**🎉 Ready to deploy!**

Once Docker is running, just run:
```bash
./start.sh
```

Then open: http://localhost:3000
