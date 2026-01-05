"""
Semantic Response Caching Service
Caches AI responses based on semantic similarity using embeddings
"""

import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
import redis
import numpy as np
from openai import AzureOpenAI
import os
from datetime import datetime


class SemanticCacheService:
    """
    Semantic caching for AI responses using vector similarity
    Reduces API calls by serving cached similar responses
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        ttl_hours: int = 24
    ):
        """
        Initialize semantic cache

        Args:
            similarity_threshold: Cosine similarity threshold (0-1)
            ttl_hours: Cache TTL in hours
        """
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_hours * 3600

        # Redis for cache storage
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_db = os.getenv("REDIS_DB", "0")

        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(redis_port),
            db=int(redis_db),
            decode_responses=True
        )

        # Azure OpenAI for embeddings
        openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not set")

        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version="2023-12-01-preview",
            azure_endpoint=openai_endpoint
        )

        self.embedding_model = os.getenv(
            "AZURE_OPENAI_EMBEDDING_MODEL",
            "text-embedding-ada-002"
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return []

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        arr1 = np.array(vec1)
        arr2 = np.array(vec2)

        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def _cache_key(self, text: str) -> str:
        """Generate cache key from text hash"""
        return f"semantic_cache:{hashlib.md5(text.encode()).hexdigest()}"

    def get_cached_response(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response if similar query exists

        Returns:
            Cached response dict or None
        """
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return None

        # Get all cache keys
        # In production, use Redis search/RediSearch for better performance
        cache_keys = self.redis_client.keys("semantic_cache:*")

        best_match = None
        best_similarity = 0.0

        for key in cache_keys:
            cached_data = self.redis_client.get(key)
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    cached_embedding = data.get("query_embedding", [])

                    if cached_embedding:
                        similarity = self._cosine_similarity(
                            query_embedding, cached_embedding
                        )
                        threshold = self.similarity_threshold
                        if (similarity > best_similarity and
                                similarity >= threshold):
                            best_similarity = similarity
                            best_match = data
                except json.JSONDecodeError:
                    continue

        if best_match:
            # Update access time
            best_match["last_accessed"] = datetime.now().isoformat()
            self.redis_client.setex(
                self._cache_key(best_match["query"]),
                self.ttl_seconds,
                json.dumps(best_match)
            )

            return {
                "response": best_match["response"],
                "similarity": best_similarity,
                "cached": True,
                "cache_hit": True
            }

        return None

    def cache_response(
        self,
        query: str,
        response: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cache a response with its query embedding

        Args:
            query: Original query text
            response: Response to cache
            metadata: Additional metadata

        Returns:
            True if cached successfully
        """
        query_embedding = self._get_embedding(query)
        if not query_embedding:
            return False

        cache_data = {
            "query": query,
            "query_embedding": query_embedding,
            "response": response,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }

        cache_key = self._cache_key(query)
        success = self.redis_client.setex(
            cache_key,
            self.ttl_seconds,
            json.dumps(cache_data)
        )

        return bool(success)

    def invalidate_cache(self, pattern: str = "*") -> int:
        """
        Invalidate cache entries matching pattern

        Returns:
            Number of entries invalidated
        """
        keys = self.redis_client.keys(f"semantic_cache:{pattern}")
        if keys:
            return self.redis_client.delete(*keys)
        return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        keys = self.redis_client.keys("semantic_cache:*")
        total_entries = len(keys)

        total_size = 0
        oldest_entry = None
        newest_entry = None

        for key in keys:
            data = self.redis_client.get(key)
            if data:
                total_size += len(data.encode('utf-8'))
                try:
                    entry = json.loads(data)
                    created_at = entry.get("created_at")
                    if created_at:
                        created_dt = datetime.fromisoformat(created_at)
                        if oldest_entry is None or created_dt < oldest_entry:
                            oldest_entry = created_dt
                        if newest_entry is None or created_dt > newest_entry:
                            newest_entry = created_dt
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue

        return {
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "oldest_entry": oldest_entry.isoformat() if oldest_entry else None,
            "newest_entry": newest_entry.isoformat() if newest_entry else None,
            "similarity_threshold": self.similarity_threshold,
            "ttl_hours": self.ttl_seconds / 3600
        }

    def warmup_cache(
        self,
        queries_and_responses: List[Tuple[str, Any]]
    ) -> int:
        """
        Pre-populate cache with known queries/responses

        Returns:
            Number of entries cached
        """
        cached_count = 0
        for query, response in queries_and_responses:
            if self.cache_response(query, response):
                cached_count += 1
        return cached_count


# Example usage
if __name__ == "__main__":
    cache = SemanticCacheService()

    # Test caching
    test_query = "What is the capital of France?"
    test_response = "Paris"

    # Cache response
    cache.cache_response(test_query, test_response)

    # Retrieve similar query
    similar_query = "What's the capital of France?"
    result = cache.get_cached_response(similar_query)

    if result:
        response = result['response']
        similarity = result['similarity']
        print(
            f"Cache hit! Response: {response}, "
            f"Similarity: {similarity:.3f}"
        )
    else:
        print("No cache hit")

    print(f"Cache stats: {cache.get_cache_stats()}")
