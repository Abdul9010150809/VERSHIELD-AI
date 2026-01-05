"""
Live FinOps Token Tracking Dashboard Service
Real-time monitoring of AI token usage and costs
"""

from typing import Dict, List, Any, Optional
import time
from datetime import datetime, timedelta
import json
import redis
import os
from collections import defaultdict

class FinOpsDashboardService:
    """
    Real-time FinOps dashboard for AI token tracking and cost monitoring
    """

    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 1)),  # Different DB for finops
            decode_responses=True
        )

        # Cost rates (per 1K tokens) - update based on current Azure OpenAI pricing
        self.cost_rates = {
            "gpt-4": {
                "input": 0.03,
                "output": 0.06
            },
            "gpt-4-turbo": {
                "input": 0.01,
                "output": 0.03
            },
            "gpt-35-turbo": {
                "input": 0.0015,
                "output": 0.002
            },
            "text-embedding-ada-002": {
                "input": 0.0001  # per 1K tokens
            },
            "azure-content-safety": 0.001,  # per request
            "azure-document-intelligence": 0.0025,  # per page
            "azure-ai-search": 0.0001  # per request
        }

        # Usage tracking keys
        self.usage_key = "finops:usage"
        self.cost_key = "finops:cost"
        self.metrics_key = "finops:metrics"

    def track_token_usage(self, model: str, tokens_input: int, tokens_output: int = 0,
                         user_id: str = "anonymous", session_id: str = None) -> Dict[str, Any]:
        """
        Track token usage for a request

        Args:
            model: AI model used
            tokens_input: Input tokens consumed
            tokens_output: Output tokens consumed
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Usage tracking result with cost
        """
        timestamp = time.time()
        date_key = datetime.now().strftime("%Y-%m-%d")

        # Calculate cost
        cost = self._calculate_cost(model, tokens_input, tokens_output)

        # Usage data
        usage_data = {
            "model": model,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "total_tokens": tokens_input + tokens_output,
            "cost": cost,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": timestamp,
            "date": date_key
        }

        # Store in Redis
        usage_id = f"{int(timestamp * 1000)}_{user_id}"
        self.redis_client.hset(f"{self.usage_key}:{usage_id}", mapping=usage_data)

        # Update daily aggregates
        self._update_daily_aggregates(date_key, usage_data)

        # Update real-time metrics
        self._update_realtime_metrics(usage_data)

        return {
            "usage_id": usage_id,
            "cost": cost,
            "tokens_used": usage_data["total_tokens"]
        }

    def _calculate_cost(self, model: str, tokens_input: int, tokens_output: int = 0) -> float:
        """Calculate cost based on model and tokens"""
        if model not in self.cost_rates:
            return 0.0

        rates = self.cost_rates[model]

        if isinstance(rates, dict):
            # Token-based pricing
            input_cost = (tokens_input / 1000) * rates.get("input", 0)
            output_cost = (tokens_output / 1000) * rates.get("output", 0)
            return input_cost + output_cost
        else:
            # Request-based pricing
            return rates

    def _update_daily_aggregates(self, date_key: str, usage_data: Dict[str, Any]):
        """Update daily usage aggregates"""
        agg_key = f"{self.usage_key}:daily:{date_key}"

        # Use Redis pipeline for atomic updates
        pipe = self.redis_client.pipeline()

        pipe.hincrbyfloat(agg_key, "total_tokens", usage_data["total_tokens"])
        pipe.hincrbyfloat(agg_key, "tokens_input", usage_data["tokens_input"])
        pipe.hincrbyfloat(agg_key, "tokens_output", usage_data["tokens_output"])
        pipe.hincrbyfloat(agg_key, "total_cost", usage_data["cost"])
        pipe.hincrby(agg_key, "request_count", 1)

        # Track per-model usage
        model_key = f"model_{usage_data['model']}"
        pipe.hincrbyfloat(agg_key, f"{model_key}_tokens", usage_data["total_tokens"])
        pipe.hincrbyfloat(agg_key, f"{model_key}_cost", usage_data["cost"])
        pipe.hincrby(agg_key, f"{model_key}_requests", 1)

        pipe.execute()

    def _update_realtime_metrics(self, usage_data: Dict[str, Any]):
        """Update real-time metrics for dashboard"""
        metrics_key = f"{self.metrics_key}:realtime"

        # Keep only last 24 hours of data
        expiry = 24 * 60 * 60

        pipe = self.redis_client.pipeline()

        # Overall metrics
        pipe.hincrbyfloat(metrics_key, "total_tokens_24h", usage_data["total_tokens"])
        pipe.hincrbyfloat(metrics_key, "total_cost_24h", usage_data["cost"])
        pipe.hincrby(metrics_key, "requests_24h", 1)

        # Per-model metrics
        model = usage_data["model"]
        pipe.hincrbyfloat(metrics_key, f"{model}_tokens_24h", usage_data["total_tokens"])
        pipe.hincrbyfloat(metrics_key, f"{model}_cost_24h", usage_data["cost"])
        pipe.hincrby(metrics_key, f"{model}_requests_24h", 1)

        # Set expiry on all keys
        pipe.expire(metrics_key, expiry)

        pipe.execute()

    def get_dashboard_data(self, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Get dashboard data for specified timeframe

        Args:
            timeframe: "1h", "24h", "7d", "30d"

        Returns:
            Dashboard metrics
        """
        if timeframe == "realtime":
            return self._get_realtime_dashboard()

        # Calculate date range
        end_date = datetime.now()
        if timeframe == "1h":
            start_date = end_date - timedelta(hours=1)
        elif timeframe == "24h":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "7d":
            start_date = end_date - timedelta(days=7)
        elif timeframe == "30d":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=1)

        # Aggregate data across date range
        total_tokens = 0
        total_cost = 0
        total_requests = 0
        model_breakdown = defaultdict(lambda: {"tokens": 0, "cost": 0, "requests": 0})

        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            agg_key = f"{self.usage_key}:daily:{date_key}"

            daily_data = self.redis_client.hgetall(agg_key)
            if daily_data:
                total_tokens += float(daily_data.get("total_tokens", 0))
                total_cost += float(daily_data.get("total_cost", 0))
                total_requests += int(daily_data.get("request_count", 0))

                # Model breakdown
                for key, value in daily_data.items():
                    if key.startswith("model_") and key.endswith("_tokens"):
                        model = key.replace("model_", "").replace("_tokens", "")
                        model_breakdown[model]["tokens"] += float(value)
                    elif key.startswith("model_") and key.endswith("_cost"):
                        model = key.replace("model_", "").replace("_cost", "")
                        model_breakdown[model]["cost"] += float(value)
                    elif key.startswith("model_") and key.endswith("_requests"):
                        model = key.replace("model_", "").replace("_requests", "")
                        model_breakdown[model]["requests"] += int(value)

            current_date += timedelta(days=1)

        # Calculate averages
        days = (end_date - start_date).days + 1
        avg_daily_cost = total_cost / days if days > 0 else 0
        avg_daily_tokens = total_tokens / days if days > 0 else 0

        return {
            "timeframe": timeframe,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_requests": total_requests,
            "avg_daily_cost": avg_daily_cost,
            "avg_daily_tokens": avg_daily_tokens,
            "model_breakdown": dict(model_breakdown),
            "cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0,
            "generated_at": datetime.now().isoformat()
        }

    def _get_realtime_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        metrics_key = f"{self.metrics_key}:realtime"
        data = self.redis_client.hgetall(metrics_key)

        if not data:
            return self._empty_dashboard("realtime")

        # Parse metrics
        total_tokens = float(data.get("total_tokens_24h", 0))
        total_cost = float(data.get("total_cost_24h", 0))
        total_requests = int(data.get("requests_24h", 0))

        model_breakdown = {}
        for key, value in data.items():
            if "_24h" in key:
                if key.endswith("_tokens_24h"):
                    model = key.replace("_tokens_24h", "")
                    if model not in model_breakdown:
                        model_breakdown[model] = {"tokens": 0, "cost": 0, "requests": 0}
                    model_breakdown[model]["tokens"] = float(value)
                elif key.endswith("_cost_24h"):
                    model = key.replace("_cost_24h", "")
                    if model not in model_breakdown:
                        model_breakdown[model] = {"tokens": 0, "cost": 0, "requests": 0}
                    model_breakdown[model]["cost"] = float(value)
                elif key.endswith("_requests_24h"):
                    model = key.replace("_requests_24h", "")
                    if model not in model_breakdown:
                        model_breakdown[model] = {"tokens": 0, "cost": 0, "requests": 0}
                    model_breakdown[model]["requests"] = int(value)

        return {
            "timeframe": "realtime",
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_requests": total_requests,
            "model_breakdown": model_breakdown,
            "cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0,
            "generated_at": datetime.now().isoformat()
        }

    def _empty_dashboard(self, timeframe: str) -> Dict[str, Any]:
        """Return empty dashboard structure"""
        return {
            "timeframe": timeframe,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_requests": 0,
            "avg_daily_cost": 0.0,
            "avg_daily_tokens": 0,
            "model_breakdown": {},
            "cost_per_token": 0.0,
            "generated_at": datetime.now().isoformat()
        }

    def get_cost_alerts(self, threshold: float = 100.0) -> List[Dict[str, Any]]:
        """
        Get cost alerts if daily spending exceeds threshold

        Args:
            threshold: Daily cost threshold

        Returns:
            List of alerts
        """
        alerts = []
        today_key = datetime.now().strftime("%Y-%m-%d")
        agg_key = f"{self.usage_key}:daily:{today_key}"

        daily_data = self.redis_client.hgetall(agg_key)
        if daily_data:
            daily_cost = float(daily_data.get("total_cost", 0))
            if daily_cost > threshold:
                alerts.append({
                    "type": "cost_threshold_exceeded",
                    "message": f"Daily cost ${daily_cost:.2f} exceeds threshold ${threshold:.2f}",
                    "severity": "high",
                    "timestamp": datetime.now().isoformat()
                })

        return alerts

    def export_usage_data(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Export usage data for date range

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of usage records
        """
        usage_records = []

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = start
        while current_date <= end:
            date_key = current_date.strftime("%Y-%m-%d")
            agg_key = f"{self.usage_key}:daily:{date_key}"

            daily_data = self.redis_client.hgetall(agg_key)
            if daily_data:
                usage_records.append({
                    "date": date_key,
                    "total_tokens": float(daily_data.get("total_tokens", 0)),
                    "total_cost": float(daily_data.get("total_cost", 0)),
                    "request_count": int(daily_data.get("request_count", 0)),
                    "model_breakdown": {
                        k.replace("model_", "").replace("_tokens", "").replace("_cost", "").replace("_requests", ""): v
                        for k, v in daily_data.items()
                        if k.startswith("model_")
                    }
                })

            current_date += timedelta(days=1)

        return usage_records

    def set_budget_limits(self, monthly_budget: float, daily_budget: float):
        """
        Set budget limits for alerts

        Args:
            monthly_budget: Monthly budget limit
            daily_budget: Daily budget limit
        """
        budget_key = f"{self.metrics_key}:budget"
        self.redis_client.hset(budget_key, mapping={
            "monthly_budget": monthly_budget,
            "daily_budget": daily_budget,
            "updated_at": datetime.now().isoformat()
        })


# Example usage
if __name__ == "__main__":
    finops = FinOpsDashboardService()

    # Track some usage
    finops.track_token_usage("gpt-4", 1000, 500, "user123", "session456")
    finops.track_token_usage("text-embedding-ada-002", 2000, 0, "user123", "session456")

    # Get dashboard
    dashboard = finops.get_dashboard_data("24h")
    print(f"Total cost: ${dashboard['total_cost']:.4f}")
    print(f"Total tokens: {dashboard['total_tokens']}")
    print(f"Model breakdown: {dashboard['model_breakdown']}")