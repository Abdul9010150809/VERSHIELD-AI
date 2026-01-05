"""
FinOps Token Tracking Service
Real-time cost monitoring and optimization
"""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import json

class FinOpsTracker:
    """
    Track and analyze API costs in real-time
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        
        # Model pricing (per 1M tokens)
        self.pricing = {
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "gpt-4o-mini": {"input": 0.150, "output": 0.600},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "text-embedding-3-small": {"input": 0.020, "output": 0},
            "text-embedding-3-large": {"input": 0.130, "output": 0}
        }
        
        self.cost_data = defaultdict(lambda: {
            "total_cost": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "requests": 0
        })
    
    async def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track API usage and calculate cost
        """
        pricing = self.pricing.get(model, {"input": 0, "output": 0})
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        usage_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": round(total_cost, 6),
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        # Update in-memory stats
        key = f"{model}:{user_id}" if user_id else model
        self.cost_data[key]["total_cost"] += total_cost
        self.cost_data[key]["input_tokens"] += input_tokens
        self.cost_data[key]["output_tokens"] += output_tokens
        self.cost_data[key]["requests"] += 1
        
        # Store in Redis if available
        if self.redis_client:
            await self._store_in_redis(usage_record)
        
        return usage_record
    
    async def _store_in_redis(self, record: Dict[str, Any]):
        """Store usage record in Redis"""
        try:
            # Store individual record
            key = f"finops:usage:{datetime.utcnow().strftime('%Y%m%d')}:{record['model']}"
            await self.redis_client.lpush(key, json.dumps(record))
            await self.redis_client.expire(key, 86400 * 30)  # 30 days retention
            
            # Update aggregated stats
            stats_key = f"finops:stats:{datetime.utcnow().strftime('%Y%m%d')}"
            await self.redis_client.hincrby(stats_key, "total_requests", 1)
            await self.redis_client.hincrbyfloat(stats_key, "total_cost", record["cost_usd"])
            await self.redis_client.hincrby(stats_key, "total_tokens", record["total_tokens"])
            
        except Exception as e:
            print(f"Redis storage error: {e}")
    
    async def get_daily_stats(
        self,
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get cost statistics for a specific day"""
        target_date = date or datetime.utcnow()
        date_str = target_date.strftime('%Y%m%d')
        
        if self.redis_client:
            try:
                stats_key = f"finops:stats:{date_str}"
                stats = await self.redis_client.hgetall(stats_key)
                
                return {
                    "date": date_str,
                    "total_requests": int(stats.get(b"total_requests", 0)),
                    "total_cost": float(stats.get(b"total_cost", 0)),
                    "total_tokens": int(stats.get(b"total_tokens", 0)),
                    "average_cost_per_request": float(stats.get(b"total_cost", 0)) / max(int(stats.get(b"total_requests", 1)), 1)
                }
            except Exception as e:
                print(f"Stats retrieval error: {e}")
        
        # Fallback to in-memory data
        total_cost = sum(data["total_cost"] for data in self.cost_data.values())
        total_requests = sum(data["requests"] for data in self.cost_data.values())
        total_tokens = sum(
            data["input_tokens"] + data["output_tokens"]
            for data in self.cost_data.values()
        )
        
        return {
            "date": date_str,
            "total_requests": total_requests,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "average_cost_per_request": round(total_cost / max(total_requests, 1), 4)
        }
    
    async def get_model_breakdown(self) -> Dict[str, Any]:
        """Get cost breakdown by model"""
        breakdown = {}
        
        for key, data in self.cost_data.items():
            model = key.split(':')[0]
            if model not in breakdown:
                breakdown[model] = {
                    "total_cost": 0,
                    "requests": 0,
                    "tokens": 0
                }
            
            breakdown[model]["total_cost"] += data["total_cost"]
            breakdown[model]["requests"] += data["requests"]
            breakdown[model]["tokens"] += data["input_tokens"] + data["output_tokens"]
        
        return breakdown
    
    async def get_user_costs(self, user_id: str) -> Dict[str, Any]:
        """Get costs for specific user"""
        user_data = {
            key: data for key, data in self.cost_data.items()
            if user_id in key
        }
        
        total_cost = sum(data["total_cost"] for data in user_data.values())
        total_requests = sum(data["requests"] for data in user_data.values())
        
        return {
            "user_id": user_id,
            "total_cost": round(total_cost, 4),
            "total_requests": total_requests,
            "models_used": list(user_data.keys())
        }
    
    async def get_cost_forecast(
        self,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """Forecast costs based on historical usage"""
        # Get last 7 days average
        recent_stats = await self.get_daily_stats()
        daily_average = recent_stats["total_cost"]
        
        forecast = {
            "forecast_period_days": days_ahead,
            "daily_average_cost": round(daily_average, 4),
            "projected_total_cost": round(daily_average * days_ahead, 4),
            "confidence": "medium"
        }
        
        return forecast
    
    async def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Generate cost optimization suggestions"""
        suggestions = []
        breakdown = await self.get_model_breakdown()
        
        for model, data in breakdown.items():
            cost = data["total_cost"]
            requests = data["requests"]
            
            if "gpt-4" in model and requests > 100:
                suggestions.append({
                    "type": "model_downgrade",
                    "priority": "high",
                    "model": model,
                    "suggestion": f"Consider using gpt-4o-mini for simpler tasks. Potential savings: ~85%",
                    "estimated_savings": cost * 0.85
                })
            
            if requests > 1000:
                suggestions.append({
                    "type": "caching",
                    "priority": "medium",
                    "model": model,
                    "suggestion": "Enable semantic caching to reduce redundant API calls",
                    "estimated_savings": cost * 0.30
                })
        
        return suggestions
