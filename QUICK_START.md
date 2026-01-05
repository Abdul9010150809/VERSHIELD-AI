# 🚀 VeriShield AI - Quick Start (5 minutes)

## Step 1: Prerequisites Check
```bash
docker --version        # Should show Docker 20.10+
docker-compose --version # Should show Docker Compose 2.0+
```

If not installed, install Docker Desktop: https://www.docker.com/products/docker-desktop

## Step 2: Get API Key
- Go to https://platform.openai.com/api-keys
- Create new API key
- Copy the key (you'll need it in Step 4)

## Step 3: Verify System Ready
```bash
cd VERSHIELD-AI
./verify-deployment.sh
```

Expected output: ✅ All checks pass

## Step 4: Configure API Key
```bash
nano .env.local
```

Find this line:
```
OPENAI_API_KEY=sk-proj-test-key-local-dev-mode
```

Replace with:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

Save and exit (Ctrl+X, Y, Enter for nano)

## Step 5: Deploy!
```bash
./start.sh
```

Wait for: ✅ "Backend is ready!" (takes 10-30 seconds on first run)

## Step 6: Access Services

Open these in your browser:

| Service | URL |
|---------|-----|
| Web Interface | http://localhost:3000 |
| API Documentation | http://localhost:8000/docs |
| FinOps Dashboard | http://localhost:3000/dashboard/finops |

## ✅ Success!

You should see:
- ✅ Frontend loads at http://localhost:3000
- ✅ API responds at http://localhost:8000/docs
- ✅ All dashboards are interactive

---

## Need Help?

### Check if services are running
```bash
docker-compose ps
```

### View logs if something fails
```bash
docker-compose logs -f backend
```

### Full troubleshooting
See `TROUBLESHOOTING.md`

---

## Next Steps

1. **Explore API**: Visit http://localhost:8000/docs to test endpoints
2. **Check Dashboard**: Open http://localhost:3000/dashboard/finops
3. **Read Docs**: Open `LOCAL_DEPLOYMENT.md` for detailed information
4. **Enable Features**: See `DEVELOPER_REFERENCE.md` to enable optional features

---

## Common Commands

```bash
# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart backend
docker-compose restart backend

# Check service status
docker-compose ps

# Database access
docker-compose exec db psql -U verishield_user -d verishield

# Redis access
docker-compose exec redis redis-cli
```

---

**Enjoy using VeriShield AI! 🎉**
