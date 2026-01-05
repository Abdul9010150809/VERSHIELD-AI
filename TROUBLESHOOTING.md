# VeriShield AI - Troubleshooting Guide

## Common Issues & Solutions

### 1. Docker Issues

#### "docker: command not found"
**Solution**: Install Docker
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y docker.io docker-compose

# macOS (with Homebrew)
brew install docker docker-compose

# Or download Docker Desktop from https://www.docker.com/products/docker-desktop
```

#### "docker-compose: command not found"
**Solution**: Install Docker Compose
```bash
# Latest version
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Permission denied for Docker
**Solution**: Add user to docker group
```bash
sudo usermod -aG docker $USER
newgrp docker
# Log out and back in for changes to take effect
```

---

### 2. Port Conflicts

#### "Bind for 0.0.0.0:3000 failed: port is already allocated"

Find what's using the port:
```bash
# Linux/macOS
lsof -i :3000
lsof -i :8000

# Windows (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess
```

Kill the process:
```bash
# Linux/macOS
kill -9 <PID>

# Windows
Stop-Process -Id <PID> -Force
```

Or use different ports in docker-compose.yml:
```yaml
backend:
  ports:
    - "8001:8000"  # Changed from 8000
frontend:
  ports:
    - "3001:3000"  # Changed from 3000
```

---

### 3. Database Issues

#### "Database connection refused"

**Check if PostgreSQL container is running**:
```bash
docker-compose ps db
```

**Restart database**:
```bash
docker-compose restart db
# Wait 15 seconds
docker-compose logs db
```

**Reset database completely**:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d db
# Wait for initialization
```

#### "PSQL: syntax error in init-db.sql"

Check if the script exists:
```bash
ls -la scripts/init-db.sql
```

If missing, create a minimal one:
```bash
mkdir -p scripts
touch scripts/init-db.sql
```

---

### 4. Backend (FastAPI) Issues

#### "Backend is not responding" or "Connection refused on port 8000"

**Check logs**:
```bash
docker-compose logs backend
```

**Common errors in logs**:

1. **ModuleNotFoundError**
   ```
   Solution: Rebuild backend image
   docker-compose build --no-cache backend
   docker-compose up -d backend
   ```

2. **ImportError or Missing Dependencies**
   ```
   Solution: Check requirements.txt and rebuild
   docker build --no-cache -t verishield-backend ./backend
   ```

3. **Connection to Redis refused**
   ```
   Solution: Ensure Redis is running
   docker-compose restart redis
   docker-compose logs redis
   ```

**Restart backend service**:
```bash
docker-compose restart backend
docker-compose logs -f backend  # Watch logs
```

#### API returns 500 errors

**Check backend logs**:
```bash
docker-compose logs backend | grep ERROR
```

**Common causes**:
- Missing environment variables in `.env.local`
- Azure service endpoints not configured (when features are enabled)
- Database connection issues
- Redis connection issues

**Solution**:
1. Check `.env.local` has all required variables
2. Verify services are enabled only if configured
3. Restart all services: `docker-compose restart`

---

### 5. Frontend (Next.js) Issues

#### "Frontend not loading" or "Connection refused on port 3000"

**Check logs**:
```bash
docker-compose logs frontend
```

**Common errors**:

1. **"npm: command not found"**
   ```
   Solution: Frontend Dockerfile may have issues. Try:
   docker-compose build --no-cache frontend
   docker-compose up -d frontend
   ```

2. **"Port 3000 already allocated"**
   ```
   Solution: See Port Conflicts section above
   ```

3. **"Cannot GET /" or blank page**
   ```
   Solution: Next.js build failed. Check logs:
   docker-compose logs frontend | grep -i error
   
   Restart with rebuild:
   docker-compose build --no-cache frontend
   docker-compose up -d frontend
   ```

**Access frontend directly**:
```bash
# In browser
http://localhost:3000

# Via curl
curl http://localhost:3000
```

---

### 6. Environment Variables

#### "OPENAI_API_KEY not set"

**Solution**: Add to `.env.local`
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

**Reload environment**:
```bash
docker-compose down
# Edit .env.local
docker-compose up -d
```

#### "Missing Azure credentials"

If features are disabled (ENABLE_* =false), Azure credentials are optional.

To enable a feature:
1. Set the feature flag: `ENABLE_FEATURE_NAME=true`
2. Add required credentials to `.env.local`
3. Restart: `docker-compose restart backend`

---

### 7. Performance Issues

#### "Services running but very slow"

**Check resource usage**:
```bash
docker stats
```

**Solutions**:
1. **Increase Docker memory**:
   - Docker Desktop: Settings → Resources → Memory (increase to 4GB or more)

2. **Clean up old images/containers**:
   ```bash
   docker system prune -a
   ```

3. **Disable unnecessary features**:
   ```
   ENABLE_PII_REDACTION=false
   ENABLE_VECTOR_RAG=false
   # Keep only ENABLE_SEMANTIC_CACHE=true and ENABLE_FINOPS_TRACKING=true
   ```

#### "Redis running out of memory"

**Check Redis memory**:
```bash
docker-compose exec redis redis-cli info memory
```

**Clear cache**:
```bash
docker-compose exec redis redis-cli FLUSHALL
```

---

### 8. Network Issues

#### Services can't reach each other

**Verify network**:
```bash
docker-compose ps
docker network ls
docker network inspect verishield_verishield-network
```

**Rebuild network**:
```bash
docker-compose down
docker network rm verishield_verishield-network
docker-compose up -d
```

---

### 9. File Permission Issues

#### "Permission denied" when accessing volumes

**Solution**:
```bash
# Rebuild containers to fix ownership
docker-compose down
sudo chown -R $(id -u):$(id -g) ./backend ./frontend
docker-compose up -d
```

---

### 10. Complete System Reset

#### "Everything is broken, start fresh"

```bash
# Stop all services
docker-compose down -v

# Remove all related images
docker rmi verishield-backend verishield-frontend

# Clean up Docker system
docker system prune -a

# Rebuild everything
docker-compose build --no-cache

# Start fresh
./start.sh
```

---

## Diagnostic Commands

### Quick Health Check
```bash
echo "=== Docker ==="
docker --version && docker-compose --version

echo "=== Services ==="
docker-compose ps

echo "=== Logs (last 20 lines) ==="
docker-compose logs --tail 20

echo "=== Network ==="
docker network ls
```

### Full Diagnostic Report
```bash
#!/bin/bash
echo "=== VeriShield AI Diagnostics ==="
echo ""
echo "Docker Status:"
docker --version
docker-compose --version
docker info | head -10
echo ""
echo "Service Status:"
docker-compose ps
echo ""
echo "Recent Logs:"
docker-compose logs --tail 30
echo ""
echo "Network:"
docker network inspect verishield_verishield-network | grep -E "Name|Containers"
echo ""
echo "Volumes:"
docker volume ls
```

---

## Getting Help

### Before Contacting Support

1. Run diagnostics:
   ```bash
   ./verify-deployment.sh
   docker-compose logs > logs.txt
   ```

2. Check error logs for specific errors

3. Verify `.env.local` is configured

4. Try a complete reset (see section 10)

### Useful Information to Provide

- Output of: `docker-compose ps`
- Output of: `docker-compose logs --tail 50`
- Your `.env.local` (without API keys)
- OS and Docker version
- Any error messages you see

---

## Performance Baseline

Expected performance on local machine:
- Frontend load: < 2 seconds
- API response: < 500ms
- Database queries: < 100ms
- Cache hits: < 10ms

If significantly slower, check:
- Docker resource allocation
- System disk space (at least 5GB free)
- RAM availability (minimum 4GB)
- CPU usage from other applications
