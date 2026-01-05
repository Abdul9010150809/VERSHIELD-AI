"""
Automated Compliance Auditing & Logging Service
Comprehensive audit trail for regulatory compliance
"""
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import hashlib

class ComplianceEvent(str, Enum):
    USER_ACCESS = "user_access"
    DATA_ACCESS = "data_access"
    PII_DETECTED = "pii_detected"
    CONTENT_FLAGGED = "content_flagged"
    POLICY_VIOLATION = "policy_violation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_EXPORT = "data_export"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_ALERT = "security_alert"

class ComplianceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceAuditService:
    """
    Automated compliance auditing and logging service
    Supports GDPR, HIPAA, SOC 2, and other regulatory frameworks
    """
    
    def __init__(self, redis_client=None, database=None):
        self.redis_client = redis_client
        self.database = database
        self.audit_logs = []
        
        # Compliance frameworks
        self.frameworks = {
            "GDPR": ["data_access", "pii_detected", "data_export", "user_access"],
            "HIPAA": ["data_access", "pii_detected", "authentication", "authorization"],
            "SOC2": ["security_alert", "configuration_change", "user_access"],
            "PCI_DSS": ["data_access", "content_flagged", "security_alert"]
        }
    
    async def log_event(
        self,
        event_type: ComplianceEvent,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        compliance_level: ComplianceLevel = ComplianceLevel.LOW
    ) -> Dict[str, Any]:
        """
        Log a compliance event
        """
        timestamp = datetime.utcnow()
        
        audit_record = {
            "event_id": self._generate_event_id(timestamp, event_type, user_id),
            "timestamp": timestamp.isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "details": details or {},
            "ip_address": ip_address,
            "compliance_level": compliance_level.value,
            "frameworks_applicable": self._get_applicable_frameworks(event_type)
        }
        
        # Store in memory
        self.audit_logs.append(audit_record)
        
        # Store in Redis (real-time access)
        if self.redis_client:
            await self._store_in_redis(audit_record)
        
        # Store in database (long-term retention)
        if self.database:
            await self._store_in_database(audit_record)
        
        # Check for policy violations
        if compliance_level in [ComplianceLevel.HIGH, ComplianceLevel.CRITICAL]:
            await self._trigger_alert(audit_record)
        
        return audit_record
    
    def _generate_event_id(
        self,
        timestamp: datetime,
        event_type: ComplianceEvent,
        user_id: Optional[str]
    ) -> str:
        """Generate unique event ID"""
        data = f"{timestamp.isoformat()}{event_type.value}{user_id or 'system'}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_applicable_frameworks(
        self,
        event_type: ComplianceEvent
    ) -> List[str]:
        """Determine which compliance frameworks apply"""
        applicable = []
        for framework, events in self.frameworks.items():
            if event_type.value in events:
                applicable.append(framework)
        return applicable
    
    async def _store_in_redis(self, record: Dict[str, Any]):
        """Store audit record in Redis"""
        try:
            # Store individual record
            key = f"audit:{record['event_type']}:{datetime.utcnow().strftime('%Y%m%d')}"
            await self.redis_client.lpush(key, json.dumps(record))
            await self.redis_client.expire(key, 86400 * 90)  # 90 days
            
            # Update counters
            counter_key = f"audit:counters:{datetime.utcnow().strftime('%Y%m%d')}"
            await self.redis_client.hincrby(counter_key, record['event_type'], 1)
            
        except Exception as e:
            print(f"Redis audit storage error: {e}")
    
    async def _store_in_database(self, record: Dict[str, Any]):
        """Store audit record in database"""
        # Database storage implementation
        pass
    
    async def _trigger_alert(self, record: Dict[str, Any]):
        """Trigger alert for critical events"""
        print(f"SECURITY ALERT: {record['event_type']} - {record['compliance_level']}")
        # Implement alerting logic (email, Slack, PagerDuty, etc.)
    
    async def get_audit_trail(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[ComplianceEvent] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail with filters
        """
        filtered_logs = self.audit_logs
        
        # Apply filters
        if start_date:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log['timestamp']) >= start_date
            ]
        
        if end_date:
            filtered_logs = [
                log for log in filtered_logs
                if datetime.fromisoformat(log['timestamp']) <= end_date
            ]
        
        if event_type:
            filtered_logs = [
                log for log in filtered_logs
                if log['event_type'] == event_type.value
            ]
        
        if user_id:
            filtered_logs = [
                log for log in filtered_logs
                if log['user_id'] == user_id
            ]
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(
            key=lambda x: datetime.fromisoformat(x['timestamp']),
            reverse=True
        )
        
        return filtered_logs[:limit]
    
    async def generate_compliance_report(
        self,
        framework: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate compliance report for specific framework
        """
        applicable_events = self.frameworks.get(framework, [])
        
        logs = await self.get_audit_trail(start_date=start_date, end_date=end_date)
        
        # Filter by framework
        framework_logs = [
            log for log in logs
            if log['event_type'] in applicable_events
        ]
        
        # Calculate metrics
        total_events = len(framework_logs)
        events_by_type = {}
        critical_events = []
        
        for log in framework_logs:
            event_type = log['event_type']
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            
            if log['compliance_level'] in ['high', 'critical']:
                critical_events.append(log)
        
        return {
            "framework": framework,
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": total_events,
            "events_by_type": events_by_type,
            "critical_events_count": len(critical_events),
            "critical_events": critical_events[:10],  # Top 10 critical
            "compliance_score": self._calculate_compliance_score(
                total_events,
                len(critical_events)
            ),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_compliance_score(
        self,
        total_events: int,
        critical_events: int
    ) -> float:
        """Calculate compliance score (0-100)"""
        if total_events == 0:
            return 100.0
        
        violation_rate = critical_events / total_events
        score = max(0, 100 - (violation_rate * 100))
        
        return round(score, 2)
    
    async def get_user_activity_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity summary for a specific user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        logs = await self.get_audit_trail(
            start_date=start_date,
            user_id=user_id
        )
        
        activities = {}
        for log in logs:
            activity = log['event_type']
            activities[activity] = activities.get(activity, 0) + 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_activities": len(logs),
            "activities_by_type": activities,
            "last_activity": logs[0]['timestamp'] if logs else None
        }
    
    async def export_audit_logs(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs in specified format
        """
        logs = await self.get_audit_trail(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if format == "json":
            return json.dumps(logs, indent=2)
        elif format == "csv":
            # CSV export implementation
            csv_lines = ["event_id,timestamp,event_type,user_id,action,compliance_level"]
            for log in logs:
                csv_lines.append(
                    f"{log['event_id']},{log['timestamp']},{log['event_type']},"
                    f"{log['user_id']},{log.get('action', '')},{log['compliance_level']}"
                )
            return "\n".join(csv_lines)
        else:
            return json.dumps({"error": "Unsupported format"})
