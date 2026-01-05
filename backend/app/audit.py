from azure.cosmos import CosmosClient, PartitionKey
import os
from datetime import datetime
from typing import Dict, Any
from .database import tenant_id
from dotenv import load_dotenv

load_dotenv()

class AuditLogger:
    """Immutable audit logging using Azure Cosmos DB."""

    def __init__(self):
        self.endpoint = os.getenv("COSMOS_ENDPOINT")
        self.key = os.getenv("COSMOS_KEY")
        self.database_name = "verishield-audit"
        self.container_name = "audit-logs"

        if self.endpoint and self.key:
            self.client = CosmosClient(self.endpoint, self.key)
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.container_name)

    async def log_detection_event(self, detection_data: Dict[str, Any]):
        """Log a detection event immutably."""
        if not hasattr(self, 'container'):
            return  # Cosmos DB not configured

        tenant = tenant_id.get()

        audit_entry = {
            "id": f"{tenant}_{datetime.utcnow().isoformat()}_{detection_data.get('transaction_id', 'unknown')}",
            "tenant_id": tenant,
            "event_type": "detection",
            "timestamp": datetime.utcnow().isoformat(),
            "data": detection_data,
            "anonymized": True,  # Flag indicating PII has been removed
            "partition_key": tenant
        }

        try:
            self.container.create_item(audit_entry)
        except Exception as e:
            print(f"Audit logging failed: {e}")
            # In production, implement retry logic and alerting

    async def log_auth_event(self, user_id: str, action: str, ip_address: str):
        """Log authentication events."""
        if not hasattr(self, 'container'):
            return

        tenant = tenant_id.get()

        audit_entry = {
            "id": f"{tenant}_{datetime.utcnow().isoformat()}_{user_id}_{action}",
            "tenant_id": tenant,
            "event_type": "auth",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "ip_address": ip_address,
            "partition_key": tenant
        }

        try:
            self.container.create_item(audit_entry)
        except Exception as e:
            print(f"Auth audit logging failed: {e}")

    async def query_audit_logs(self, tenant_id: str, start_date: str, end_date: str) -> list:
        """Query audit logs for compliance (admin only)."""
        if not hasattr(self, 'container'):
            return []

        query = f"""
        SELECT * FROM c
        WHERE c.tenant_id = @tenant_id
        AND c.timestamp >= @start_date
        AND c.timestamp <= @end_date
        ORDER BY c.timestamp DESC
        """

        parameters = [
            {"name": "@tenant_id", "value": tenant_id},
            {"name": "@start_date", "value": start_date},
            {"name": "@end_date", "value": end_date}
        ]

        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            print(f"Audit query failed: {e}")
            return []

# Global audit logger instance
audit_logger = AuditLogger()