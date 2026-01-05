# VeriShield AI - Local Development Guide

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Azure services configured (see `.env` file)

### Option 1: Using Startup Scripts (Recommended)

#### Terminal 1 - Backend

```bash
chmod +x start-backend.sh
./start-backend.sh
```

The backend will start on **<http://localhost:8000>**

- API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/>

#### Terminal 2 - Frontend

```bash
chmod +x start-frontend.sh  
./start-frontend.sh
```

The frontend will start on **<http://localhost:3000>**

### Option 2: Manual Setup

#### Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

### Option 3: Using Docker Compose

```bash
docker-compose up
```

This will start:

- PostgreSQL database on port 5432
- Redis on port 6379
- Backend API on port 8000
- Frontend on port 3000

## Environment Variables

Make sure your `.env` file is configured with your Azure credentials:

```env
AZURE_VISION_ENDPOINT=your_endpoint
AZURE_VISION_KEY=your_key
AZURE_SPEECH_KEY=your_key
AZURE_SPEECH_REGION=eastus
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## Testing the API

Once both servers are running:

1. **Backend API Docs**: Visit <http://localhost:8000/docs>
2. **Frontend Dashboard**: Visit <http://localhost:3000>
3. **API Health Check**:

   ```bash
   curl http://localhost:8000/
   ```

## Troubleshooting

### Backend Issues

- **Module not found**: Run `pip install -r backend/requirements.txt`
- **Port 8000 in use**: Change port with `--port 8001`
- **Azure errors**: Check `.env` file has valid Azure credentials

### Frontend Issues

- **Module not found**: Run `npm install` in frontend directory
- **Port 3000 in use**: Next.js will automatically use next available port
- **TypeScript errors**: Run `TypeScript: Restart TS Server` in VS Code

## Development

- Backend auto-reloads on file changes (via `--reload`)
- Frontend auto-reloads on file changes (via Next.js Fast Refresh)
- API documentation auto-generated at `/docs` endpoint
