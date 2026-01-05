"""
Semantic Response Caching with Redis and Embeddings
Reduces API costs and improves response times
"""
import os
import json
import hashlib
import asyncio
from typing import Dict, List, Optional, Any
import redis.asyncio as redis
from openai import AsyncOpenAI
import numpy as np
from datetime import datetime, timedelta

class SemanticCache:
    """
    Redis-based semantic caching with embedding similarity
    """
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        api_key = os.getenv("OPENAI_API_KEY")
        # Only initialize OpenAI client if API key is provided and not a placeholder
        if api_key and not api_key.startswith("sk-proj-test"):
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            self.openai_client = None
        self.redis_client = None
        self.similarity_threshold = 0.92  # Cosine similarity threshold
        self.default_ttl = 3600  # 1 hour default cache TTL
        
    async def connect(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False
            )
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI
        """
        if not self.openai_client:
            # Return None if OpenAI client is not available
            return None
        
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding generation error: {e}")
            # Fallback to hash-based caching
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        magnitude1 = np.linalg.norm(vec1_np)
        magnitude2 = np.linalg.norm(vec2_np)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def get_cached_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if semantically similar query exists
        """
        await self.connect()
        
        # Generate embedding for query
        query_embedding = await self.get_embedding(query)
        
        if query_embedding is None:
            # Fallback to exact match
            return await self._get_exact_match(query, context)
        
        # Search for similar cached queries
        cache_key_pattern = "cache:query:*"
        
        try:
            cursor = 0
            best_match = None
            best_similarity = 0.0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=cache_key_pattern,
                    count=100
                )
                
                for key in keys:
                    cached_data = await self.redis_client.get(key)
                    if cached_data:
                        cached_item = json.loads(cached_data)
                        cached_embedding = cached_item.get("embedding")
                        
                        if cached_embedding:
                            similarity = self.cosine_similarity(
                                query_embedding,
                                cached_embedding
                            )
                            
                            if similarity > best_similarity and similarity >= self.similarity_threshold:
                                best_similarity = similarity
                                best_match = cached_item
                
                if cursor == 0:
                    break
            
            if best_match:
                # Update cache hit statistics
                await self._update_cache_stats(best_match["cache_key"], "hit")
                
                return {
                    "response": best_match["response"],
                    "cached": True,
                    "similarity": best_similarity,
                    "timestamp": best_match["timestamp"],
                    "ttl": await self.redis_client.ttl(best_match["cache_key"])
                }
            
            return None
            
        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None
    
    async def cache_response(
        self,
        query: str,
        response: Any,
        context: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> str:
        """
        Cache a response with its query embedding
        """
        await self.connect()
        
        # Generate embedding
        query_embedding = await self.get_embedding(query)
        
        # Create cache key
        cache_key = f"cache:query:{hashlib.sha256(query.encode()).hexdigest()}"
        
        # Prepare cache data
        cache_data = {
            "query": query,
            "response": response,
            "embedding": query_embedding,
            "context": context,
            "timestamp": datetime.utcnow().isoformat(),
            "cache_key": cache_key,
            "hits": 0
        }
        
        try:
            # Store in Redis
            await self.redis_client.setex(
                cache_key,
                ttl or self.default_ttl,
                json.dumps(cache_data)
            )
            
            # Update cache statistics
            await self._update_cache_stats(cache_key, "create")
            
            return cache_key
            
        except Exception as e:
            print(f"Cache storage error: {e}")
            return ""
    
    async def _get_exact_match(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fallback to exact query match when embeddings unavailable
        """
        cache_key = f"cache:exact:{hashlib.sha256(query.encode()).hexdigest()}"
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return {
                    "response": json.loads(cached_data),
                    "cached": True,
                    "exact_match": True
                }
            return None
        except Exception as e:
            print(f"Exact match error: {e}")
            return None
    
    async def _update_cache_stats(self, cache_key: str, action: str):
        """
        Update cache statistics
        """
        try:
            stats_key = "cache:stats:global"
            
            if action == "hit":
                await self.redis_client.hincrby(stats_key, "hits", 1)
                await self.redis_client.hincrby(f"{cache_key}:stats", "hits", 1)
            elif action == "create":
                await self.redis_client.hincrby(stats_key, "creates", 1)
            
        except Exception as e:
            print(f"Stats update error: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retrieve cache performance statistics
        """
        await self.connect()
        
        try:
            stats_key = "cache:stats:global"
            stats = await self.redis_client.hgetall(stats_key)
            
            hits = int(stats.get(b"hits", 0))
            creates = int(stats.get(b"creates", 0))
            
            hit_rate = (hits / (hits + creates) * 100) if (hits + creates) > 0 else 0
            
            # Get Redis info
            info = await self.redis_client.info("memory")
            
            return {
                "cache_hits": hits,
                "cache_creates": creates,
                "hit_rate": round(hit_rate, 2),
                "memory_used_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "total_keys": await self.redis_client.dbsize()
            }
            
        except Exception as e:
            print(f"Stats retrieval error: {e}")
            return {
                "cache_hits": 0,
                "cache_creates": 0,
                "hit_rate": 0,
                "error": str(e)
            }
    
    async def invalidate_cache(
        self,
        pattern: Optional[str] = None,
        query: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries
        """
        await self.connect()
        
        try:
            if query:
                cache_key = f"cache:query:{hashlib.sha256(query.encode()).hexdigest()}"
                deleted = await self.redis_client.delete(cache_key)
                return deleted
            
            if pattern:
                cursor = 0
                deleted_count = 0
                
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )
                    
                    if keys:
                        deleted_count += await self.redis_client.delete(*keys)
                    
                    if cursor == 0:
                        break
                
                return deleted_count
            
            return 0
            
        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return 0
    
    async def warm_cache(
        self,
        queries: List[str],
        response_generator
    ):
        """
        Pre-populate cache with common queries
        """
        for query in queries:
            try:
                response = await response_generator(query)
                await self.cache_response(query, response)
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Cache warming error for '{query}': {e}")
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
