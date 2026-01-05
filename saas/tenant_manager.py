import asyncio
import os
from contextvars import ContextVar
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Global tenant context variable
tenant_id: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)

class TenantManager:
    """
    Lightweight middleware for tenant isolation in multi-tenant SaaS.
    Every AI request must be tagged with a tenant_id representing the company using VeriShield.
    """

    def __init__(self):
        self.default_tenant = os.getenv("DEFAULT_TENANT_ID", "verishield")

    def set_tenant(self, tenant: str) -> None:
        """Set the current tenant context."""
        tenant_id.set(tenant)

    def get_tenant(self) -> Optional[str]:
        """Get the current tenant from context."""
        return tenant_id.get()

    def clear_tenant(self) -> None:
        """Clear the tenant context."""
        tenant_id.set(None)

    async def validate_tenant_access(self, tenant: str, resource: str) -> bool:
        """
        Validate if the tenant has access to a specific resource.
        This is a placeholder for more complex permission logic.
        """
        # In production, this would check against a database
        # For now, allow access if tenant is not None
        return tenant is not None

    def get_tenant_schema(self, tenant: Optional[str] = None) -> str:
        """Get the database schema name for a tenant."""
        tenant = tenant or self.get_tenant()
        if not tenant or tenant == self.default_tenant:
            return "public"
        return f"tenant_{tenant}"

    async def log_tenant_activity(self, tenant: str, action: str, details: dict = None) -> None:
        """Log tenant activity for auditing."""
        # Placeholder for audit logging
        # In production, this would write to Cosmos DB or similar
        print(f"Tenant {tenant}: {action} - {details or {}}")

# Global tenant manager instance
tenant_manager = TenantManager()

async def with_tenant_context(tenant: str):
    """
    Context manager for tenant operations.
    Usage:
        async with with_tenant_context("company_xyz"):
            # All operations here will have tenant context
            pass
    """
    token = tenant_id.set(tenant)
    try:
        yield
    finally:
        tenant_id.reset(token)