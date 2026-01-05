# VeriShield AI SaaS Platform Scaffold Plan

## Overview

Scaffolding a production-ready, multi-tenant enterprise SaaS platform using Microsoft Azure ecosystem.

## Architecture Decisions

### Multi-Tenant Model

- **Shared Database, Isolated Schema**: Each tenant has dedicated schema in PostgreSQL
- **Tenant Context**: Every request includes `tenant_id` for data isolation
- **RLS Policies**: Row-Level Security ensures tenant data separation

### Authentication & Authorization

- **Microsoft Entra ID**: Primary SSO provider for enterprise users
- **Clerk/Auth0**: Middleware for RBAC (Admin, Security Analyst, Auditor)
- **JWT Tokens**: Tenant-scoped with organization claims

### Billing & Subscriptions

- **Stripe Integration**: Webhook-based subscription management
- **Tiers**: Startup ($199/mo), Enterprise ($599/mo), Ultimate ($1299/mo)
- **Usage Tracking**: Per-tenant API call limits and analytics

### Compliance & Audit

- **Azure Cosmos DB**: Immutable audit logs for detection events
- **PII Anonymization**: Automatic data sanitization before storage
- **Retention Policies**: Configurable data retention per compliance requirements

## Detailed File Structure

```
VeriShieldAI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app with tenant middleware
│   │   ├── config.py            # Environment and Azure configurations
│   │   ├── database.py          # PostgreSQL connection with tenant schemas
│   │   ├── auth.py              # Entra ID + Clerk/Auth0 integration
│   │   ├── billing.py           # Stripe webhook handlers
│   │   ├── audit.py             # Cosmos DB audit logging
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base model with tenant_id
│   │   │   ├── user.py          # User model with roles
│   │   │   ├── organization.py  # Tenant organization
│   │   │   ├── subscription.py  # Stripe subscription
│   │   │   ├── detection.py     # Detection events
│   │   │   └── audit_log.py     # Audit entries
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # SSO endpoints
│   │   │   ├── api.py           # Core API with tenant scoping
│   │   │   ├── billing.py       # Subscription management
│   │   │   ├── dashboard.py     # Analytics endpoints
│   │   │   └── admin.py         # Admin-only operations
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── telemetry_agent.py  # Azure Monitor
│   │   │   ├── notification.py     # Alert system
│   │   │   └── rate_limiter.py     # Per-tenant limits
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py        # Tenant context utilities
│   │   │   ├── anonymize.py     # PII stripping
│   │   │   └── validators.py    # Input validation
│   │   ├── middleware.py        # Tenant isolation middleware
│   │   └── dependencies.py      # FastAPI dependencies
│   ├── alembic/                 # Database migrations
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_tenant.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                     # Next.js 14 app directory
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── dashboard/
│   │   │   ├── page.tsx         # Security Command Center
│   │   │   ├── threat-feed.tsx  # Live WebSocket feed
│   │   │   ├── metrics.tsx      # Authenticity charts
│   │   │   └── kill-switch.tsx  # Incident response
│   │   ├── onboarding/
│   │   │   ├── page.tsx         # Multi-step wizard
│   │   │   ├── step1.tsx        # Azure credits connection
│   │   │   ├── step2.tsx        # Team invites
│   │   │   └── step3.tsx        # Integration setup
│   │   ├── api/                 # API routes
│   │   │   ├── auth/[...nextauth].ts
│   │   │   └── websocket/route.ts
│   │   └── (auth)/login/page.tsx
│   ├── components/
│   │   ├── ui/                  # Reusable UI components
│   │   ├── charts/              # Tremor/Recharts components
│   │   ├── forms/               # Form components
│   │   └── layout/              # Layout components
│   ├── lib/
│   │   ├── auth.ts              # NextAuth configuration
│   │   ├── websocket.ts         # WebSocket client
│   │   ├── api.ts               # API client
│   │   └── utils.ts
│   ├── public/
│   ├── tailwind.config.js
│   ├── next.config.js
│   ├── package.json
│   └── tsconfig.json
├── docs/
│   ├── api/
│   │   ├── openapi.yaml         # OpenAPI 3.0 spec
│   │   └── swagger-ui.html      # Swagger documentation
│   └── integrations/
│       ├── zoom.md
│       ├── teams.md
│       └── banking-erp.md
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf              # Azure resources
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── docker-compose.yml       # Local development
│   └── k8s/                     # Kubernetes manifests
├── scripts/
│   ├── setup.sh                 # Development setup
│   ├── deploy.sh                # Production deployment
│   ├── migrate.sh               # Database migrations
│   └── seed.py                  # Test data seeding
├── .env.example
├── docker-compose.yml
├── README.md
└── pyproject.toml               # Python project config
```

## Key Implementation Details

### Backend Multi-Tenancy

- **Schema Isolation**: `CREATE SCHEMA tenant_{tenant_id}`
- **Connection Pooling**: SQLAlchemy with tenant-aware sessions
- **Middleware**: Automatic tenant_id injection from JWT claims

### Authentication Flow

1. User authenticates via Microsoft Entra ID
2. Clerk/Auth0 validates roles and permissions
3. JWT issued with tenant_id and role claims
4. All subsequent requests include tenant context

### Real-Time Features

- **WebSocket Integration**: For live threat feed updates
- **Azure SignalR**: Scalable real-time messaging
- **Event-Driven Architecture**: Azure Event Grid for cross-service communication

### Compliance & Security

- **Immutable Logs**: Cosmos DB with change feed disabled
- **Encryption**: Azure Key Vault for secrets management
- **GDPR Compliance**: Data portability and right to erasure
- **SOC 2**: Audit trails and access controls

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Azure CLI
- Docker & Docker Compose

### Local Development

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# Frontend setup
cd frontend
npm install
npm run dev

# Infrastructure
docker-compose up -d
```

### Environment Variables

```env
# Azure
AZURE_CLIENT_ID=...
AZURE_TENANT_ID=...
AZURE_CLIENT_SECRET=...

# Database
DATABASE_URL=postgresql://...

# Stripe
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

# Clerk/Auth0
CLERK_SECRET_KEY=...
# or
AUTH0_DOMAIN=...
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...

# Cosmos DB
COSMOS_ENDPOINT=...
COSMOS_KEY=...
```

## Next Steps

1. Implement tenant isolation middleware
2. Set up authentication flows
3. Create database schemas and migrations
4. Build core API endpoints
5. Develop frontend dashboard
6. Integrate real-time features
7. Add compliance logging
8. Implement billing system
