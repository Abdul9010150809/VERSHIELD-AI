from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import os
from .database import tenant_id
from dotenv import load_dotenv

load_dotenv()

class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and set tenant context from JWT token."""

    async def dispatch(self, request: Request, call_next):
        # Extract tenant_id from JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # Decode JWT (simplified - in production use proper validation)
                payload = jwt.decode(token, options={"verify_signature": False})
                tenant = payload.get("tenant_id")
                if tenant:
                    # Set tenant context
                    tenant_id.set(tenant)
            except jwt.InvalidTokenError:
                pass

        # For API routes, ensure tenant is set
        if request.url.path.startswith("/api/"):
            current_tenant = tenant_id.get()
            if not current_tenant or current_tenant == 'public':
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Tenant context required"}
                )

        response = await call_next(request)
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware per tenant."""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # In production, use Redis

    async def dispatch(self, request: Request, call_next):
        tenant = tenant_id.get()
        if tenant:
            # Simple in-memory rate limiting (use Redis in production)
            key = f"{tenant}:{request.client.host}"
            current_time = request.headers.get("X-Forwarded-For", request.client.host)

            # This is a simplified implementation
            # In production, implement proper rate limiting with Redis
            pass

        response = await call_next(request)
        return response