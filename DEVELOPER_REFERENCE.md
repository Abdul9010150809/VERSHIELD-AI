# VeriShield AI - Developer Quick Reference

## Quick Commands

### Start/Stop Services
```bash
./start.sh                          # Start everything
docker-compose up -d                # Start in background
docker-compose down                 # Stop everything
docker-compose restart backend      # Restart specific service
```

### View Logs
```bash
docker-compose logs -f              # Follow all logs
docker-compose logs -f backend      # Follow backend only
docker-compose logs --tail 50       # Last 50 lines
docker-compose logs backend > logs.txt  # Save to file
```

### Service Status
```bash
docker-compose ps                   # List services
./verify-deployment.sh              # Full health check
curl http://localhost:8000/health   # API health
```

### Database Access
```bash
docker-compose exec db psql -U verishield_user -d verishield
# Then use psql commands like: \dt (list tables), SELECT * FROM ...;
```

### Redis Access
```bash
docker-compose exec redis redis-cli
# Then use Redis commands like: KEYS *, GET key, FLUSHDB, etc.
```

---

## API Testing

### Using curl
```bash
# GET request
curl http://localhost:8000/api/metrics

# POST request
curl -X POST http://localhost:8000/api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en"}'

# With response formatting
curl -s http://localhost:8000/api/metrics | python3 -m json.tool
```

### Using Swagger UI
1. Open: http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters
4. Click "Execute"

### Using Python
```python
import requests

# GET
response = requests.get('http://localhost:8000/api/metrics')
print(response.json())

# POST
response = requests.post('http://localhost:8000/api/sentiment/analyze', json={
    'text': 'This is great!',
    'language': 'en'
})
print(response.json())
```

---

## File Structure Reference

```
VERSHIELD-AI/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py       # Main application
│   │   ├── services/     # Business logic
│   │   └── models/       # Data models
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile
├── frontend/             # Next.js frontend
│   ├── app/             # Next.js app directory
│   ├── components/      # React components
│   ├── package.json     # Node dependencies
│   └── Dockerfile
├── agents/              # AI agents (Vision, Acoustic, PII)
├── infrastructure/      # Terraform, Kubernetes configs
├── .env.local          # Local environment (create from .env.template)
├── docker-compose.yml  # Container orchestration
└── start.sh           # Startup script
```

---

## Common Development Tasks

### Add a New API Endpoint
1. Create handler in `backend/app/main.py`:
```python
@app.post("/api/my-feature")
async def my_feature(request: Dict[str, Any]):
    # Implementation
    return {"result": "data"}
```
2. Test at: http://localhost:8000/docs
3. Logs available: `docker-compose logs backend`

### Modify Environment Variables
1. Edit `.env.local`
2. Restart backend: `docker-compose restart backend`
3. Verify changes: `docker-compose exec backend env | grep VARIABLE`

### Access Database
```bash
# Connect
docker-compose exec db psql -U verishield_user -d verishield

# View tables
\dt

# Query data
SELECT * FROM table_name LIMIT 10;

# Exit
\q
```

### Clear Cache
```bash
docker-compose exec redis redis-cli FLUSHDB
```

### View Cost Tracking
```bash
curl http://localhost:8000/api/finops/stats | python3 -m json.tool
```

### Check Compliance Logs
```bash
curl http://localhost:8000/api/compliance/audit-trail | python3 -m json.tool
```

---

## Environment Variables Quick Guide

| Variable | Required | Purpose |
|----------|----------|---------|
| OPENAI_API_KEY | Yes | OpenAI API access |
| DATABASE_URL | Auto | PostgreSQL connection |
| REDIS_URL | Auto | Redis connection |
| ENABLE_SEMANTIC_CACHE | No | Cache responses (true/false) |
| ENABLE_FINOPS_TRACKING | No | Cost tracking (true/false) |
| ENABLE_COMPLIANCE_AUDIT | No | Audit logging (true/false) |
| ENABLE_PII_REDACTION | No | PII detection (requires Azure) |
| ENABLE_CONTENT_SAFETY | No | Content moderation (requires Azure) |

---

## Performance Tips

### Speed Up Development
```bash
# Only rebuild changed service
docker-compose build backend
docker-compose up -d backend

# Instead of full rebuild
```

### Monitor Resource Usage
```bash
docker stats  # Real-time CPU/Memory usage
```

### Optimize Docker Build
```bash
# Clean up unused layers
docker system prune -a

# Use no-cache for fresh build
docker-compose build --no-cache
```

---

## Debugging Tips

### Enable Debug Logging
In `.env.local`:
```
LOG_LEVEL=DEBUG
DEBUG=true
```
Then restart: `docker-compose restart backend`

### Inspect Service
```bash
# Check environment variables
docker-compose exec backend env

# Check running processes
docker-compose exec backend ps aux

# Check network connectivity
docker-compose exec backend ping redis
```

### Database Queries
```bash
docker-compose exec db psql -U verishield_user -d verishield -c "SELECT COUNT(*) FROM information_schema.tables;"
```

---

## Testing Endpoints by Feature

### Sentiment Analysis
```bash
curl -X POST http://localhost:8000/api/sentiment/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this!", "language": "en"}'
```

### Semantic Cache
```bash
curl http://localhost:8000/api/cache/stats
```

### FinOps Dashboard
```bash
curl http://localhost:8000/api/finops/dashboard
```

### WebSocket (Real-time Updates)
```bash
# Using wscat
npm install -g wscat
wscat -c ws://localhost:8000/ws/dashboard
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Connection refused" | Service not running | Check `docker-compose ps` |
| "Port already in use" | Another service using port | Kill process or use different port |
| "CORS error" | Frontend-API communication issue | Check NEXT_PUBLIC_API_URL in frontend |
| "Module not found" | Python dependency missing | Rebuild: `docker-compose build` |
| "Database error" | PostgreSQL issue | Check: `docker-compose logs db` |

---

## Useful Resources

- **API Docs**: http://localhost:8000/docs (when running)
- **Frontend**: http://localhost:3000
- **README**: Repository root
- **Setup Guide**: LOCAL_DEPLOYMENT.md
- **Troubleshooting**: TROUBLESHOOTING.md
- **Deployment Checklist**: DEPLOYMENT_CHECKLIST.md

---

## Emergency Reset

If everything breaks:
```bash
# Complete system reset
docker-compose down -v
docker system prune -a
./start.sh
```

Then verify: `./verify-deployment.sh`

---

## Getting Help

1. Check the Logs: `docker-compose logs`
2. Run Diagnostics: `./verify-deployment.sh`
3. Check TROUBLESHOOTING.md
4. Review Error Messages
5. Consult DEPLOYMENT_CHECKLIST.md
