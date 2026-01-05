# VeriShield AI - Deployment Checklist ✅

## Pre-Deployment Checklist

### System Prerequisites

- [ ] Docker installed (version 20.10+)
- [ ] Docker Compose installed (version 2.0+)
- [ ] At least 8GB RAM available
- [ ] At least 10GB free disk space
- [ ] Git installed

### API Keys & Credentials

- [ ] OpenAI API key obtained (required)
- [ ] Anthropic API key (optional)
- [ ] Azure credentials (optional, only if using advanced features)

### Configuration

- [ ] `.env.local` file created
- [ ] `OPENAI_API_KEY` set in `.env.local`
- [ ] Feature flags configured (PII redaction, content safety, etc.)
- [ ] All other required environment variables set

---

## Deployment Steps

### 1. Verify System Readiness

```bash
chmod +x verify-deployment.sh
./verify-deployment.sh
```

Expected output: ✅ All checks pass

### 2. Verify Configuration

```bash
cat .env.local | grep OPENAI_API_KEY
```

Expected: `OPENAI_API_KEY=sk-...` (not the default test key)

### 3. Start Services

```bash
chmod +x start.sh
./start.sh
```

Expected output:

- Docker containers start
- "Backend is ready!" message after 10-30 seconds
- "Ready to use VeriShield AI!" confirmation

### 4. Verify Services Running

```bash
docker-compose ps
```

Expected status for all services: `Up`

Services should be:

- [ ] backend (port 8000)
- [ ] frontend (port 3000)
- [ ] db (port 5432)
- [ ] redis (port 6379)

---

## Post-Deployment Verification

### API Health Check

```bash
curl http://localhost:8000/health
```

Expected: JSON response with `"status": "healthy"`

### Frontend Access

```bash
curl http://localhost:3000
```

Expected: HTML response (page loads successfully)

### API Documentation

```bash
curl http://localhost:8000/docs
```

Expected: Swagger UI available

### Test Sample Endpoints

#### 1. Metrics Endpoint

```bash
curl http://localhost:8000/api/metrics
```

#### 2. Cache Stats

```bash
curl http://localhost:8000/api/cache/stats
```

#### 3. FinOps Stats

```bash
curl http://localhost:8000/api/finops/stats
```

#### 4. Sentiment Analysis

```bash
curl -X POST http://localhost:8000/api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is great!", "language": "en"}'
```

---

## Feature Enablement Checklist

### Semantic Caching (Enabled by Default)

- [ ] Redis running
- [ ] Cache stats returning data
- [ ] No "Connection refused" errors for Redis

### FinOps Tracking (Enabled by Default)

- [ ] Redis running
- [ ] FinOps stats endpoint returning data
- [ ] Cost calculations showing

### Compliance Auditing (Enabled by Default)

- [ ] Database running
- [ ] Audit trail endpoint accessible
- [ ] Events being logged

### PII Redaction (Disabled by Default)

- [ ] If `ENABLE_PII_REDACTION=true`:
  - [ ] Azure Language Service endpoint configured
  - [ ] Azure Language API key configured
  - [ ] PII detection endpoint responds
  - [ ] No 503 "service disabled" errors

### Content Safety (Disabled by Default)

- [ ] If `ENABLE_CONTENT_SAFETY=true`:
  - [ ] Azure Content Safety endpoint configured
  - [ ] Azure Content Safety key configured
  - [ ] Content analysis endpoints respond
  - [ ] No 503 "service disabled" errors

### Vector RAG (Disabled by Default)

- [ ] If `ENABLE_VECTOR_RAG=true`:
  - [ ] Azure Search endpoint configured
  - [ ] Azure Search key configured
  - [ ] RAG search endpoints respond
  - [ ] No 503 "service disabled" errors

### Entra ID Authentication (Disabled by Default)

- [ ] If `ENABLE_ENTRA_AUTH=true`:
  - [ ] Azure Tenant ID configured
  - [ ] Azure Client ID configured
  - [ ] Azure Client Secret configured
  - [ ] Protected endpoints require authentication

---

## Troubleshooting During Deployment

### Issue: Services fail to start

- [ ] Check Docker is running: `docker ps`
- [ ] Check logs: `docker-compose logs`
- [ ] Check ports are available: See TROUBLESHOOTING.md
- [ ] Rebuild: `docker-compose build --no-cache`

### Issue: API returns 500 errors

- [ ] Check backend logs: `docker-compose logs backend`
- [ ] Verify .env.local: `cat .env.local`
- [ ] Check Redis is running: `docker-compose logs redis`
- [ ] Check database is running: `docker-compose logs db`

### Issue: Frontend not loading

- [ ] Check frontend logs: `docker-compose logs frontend`
- [ ] Verify port 3000: `lsof -i :3000`
- [ ] Restart frontend: `docker-compose restart frontend`
- [ ] Check build: `docker-compose build frontend`

### Issue: Very slow or hanging

- [ ] Check resource usage: `docker stats`
- [ ] Increase Docker memory allocation
- [ ] Check disk space: `df -h`
- [ ] Stop and restart: `docker-compose down && docker-compose up -d`

---

## Documentation Links

- **Quick Start**: See README.md
- **Detailed Setup**: See LOCAL_DEPLOYMENT.md
- **Troubleshooting**: See TROUBLESHOOTING.md
- **Implementation Details**: See IMPLEMENTATION_SUMMARY.md
- **Architecture**: See docs/AZURE_ENTERPRISE_ARCHITECTURE.md

---

## Performance Baseline

After successful deployment, you should see:

| Metric | Expected | Location |
|--------|----------|----------|
| Frontend Load Time | < 2 seconds | Browser |
| API Response Time | < 500ms | <http://localhost:8000/docs> |
| Health Check | Healthy | `curl http://localhost:8000/health` |
| Cache Hit Rate | > 80% | `curl http://localhost:8000/api/cache/stats` |
| Database Response | < 100ms | Logs |

---

## Success Criteria

Your deployment is successful when:

✅ All containers show `Up` status  
✅ Frontend loads at <http://localhost:3000>  
✅ API responds at <http://localhost:8000>  
✅ Health check shows "healthy"  
✅ Sample API calls return data  
✅ No error messages in logs  
✅ Features you enabled are working  

---

## Maintenance Tasks

### Daily

- [ ] Check service health: `./verify-deployment.sh`
- [ ] Monitor logs for errors: `docker-compose logs`

### Weekly

- [ ] Review cost tracking: `curl http://localhost:8000/api/finops/stats`
- [ ] Check database size: `docker-compose exec db psql -U verishield_user -d verishield -c "SELECT pg_size_pretty(pg_database_size('verishield'));"`
- [ ] Clear old cache: `docker-compose exec redis redis-cli FLUSHDB`

### Monthly

- [ ] Update Docker images: `docker-compose pull && docker-compose build`
- [ ] Review compliance audit: `curl http://localhost:8000/api/compliance/audit-trail`
- [ ] Backup database: See backup procedures
- [ ] Review and update .env variables

---

## Stopping Services

### Stop All Services (Data Preserved)

```bash
docker-compose down
```

### Stop with Full Cleanup (Data Lost)

```bash
docker-compose down -v
docker system prune -a
```

### Selective Stop

```bash
docker-compose stop backend
docker-compose stop frontend
# Services remain available for restart
```

---

## Restarting After Stop

```bash
# Restart all services
docker-compose up -d

# Restart specific service
docker-compose up -d backend

# Verify they're running
docker-compose ps
./verify-deployment.sh
```

---

## Getting Help

If deployment fails:

1. Check **TROUBLESHOOTING.md** for your specific error
2. Run: `./verify-deployment.sh` and share output
3. Run: `docker-compose logs > logs.txt` and review logs
4. Check your `.env.local` (without sharing API keys)
5. Verify Docker and Docker Compose versions

---

## Sign-Off

Deployment completed on: _______________

Completed by: _______________

Issues encountered: _______________

Notes: _______________
