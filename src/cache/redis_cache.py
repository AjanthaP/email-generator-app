"""
Redis Cache Manager for Email Generator App.

Provides high-performance caching for sessions, user data, and email drafts.
"""

import redis
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta
import os

try:
    from ..utils.config import settings as app_settings
except ImportError:
    # Fallback for when imported directly
    class MockSettings:
        redis_url = "redis://localhost:6379"
        redis_host = "localhost"
        redis_port = 6379
        redis_db = 0
        redis_password = None
        redis_ssl = False
        redis_decode_responses = True
        redis_max_connections = 20
        redis_socket_timeout = 5
        redis_socket_connect_timeout = 5
        redis_retry_on_timeout = True
        redis_health_check_interval = 30
        redis_session_ttl = 86400
        redis_profile_ttl = 3600
        redis_draft_ttl = 7200
        redis_llm_response_ttl = 1800
        redis_rate_limit_ttl = 60
        redis_metrics_ttl = 604800
        enable_redis = True
    app_settings = MockSettings()


class RedisCacheManager:
    """
    Redis-based cache manager for the email generator app.
    
    Features:
    - Session caching with TTL
    - User profile caching
    - Email draft caching
    - LLM response caching
    - Metrics caching
    - Automatic serialization/deserialization
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        password: Optional[str] = None,
        decode_responses: Optional[bool] = None,
        prefix: str = "email_gen:",
        redis_url: Optional[str] = None
    ):
        """
        Initialize Redis cache manager.
        
        Args:
            host: Redis server host (uses config if None)
            port: Redis server port (uses config if None)
            db: Redis database number (uses config if None)
            password: Redis password (uses config if None)
            decode_responses: Whether to decode responses (uses config if None)
            prefix: Key prefix for all operations
            redis_url: Complete Redis URL (overrides individual params)
        """
        self.prefix = prefix
        
        # Use settings from config with parameter overrides
        redis_config = {
            'host': host or app_settings.redis_host,
            'port': port or app_settings.redis_port,
            'db': db or app_settings.redis_db,
            'password': password or app_settings.redis_password,
            'decode_responses': decode_responses if decode_responses is not None else app_settings.redis_decode_responses,
            'socket_connect_timeout': app_settings.redis_socket_connect_timeout,
            'socket_timeout': app_settings.redis_socket_timeout,
            'retry_on_timeout': app_settings.redis_retry_on_timeout,
            'max_connections': app_settings.redis_max_connections,
            'health_check_interval': app_settings.redis_health_check_interval
        }
        
        # Use redis_url if provided, otherwise use individual params
        if redis_url or app_settings.redis_url != "redis://localhost:6379":
            url = redis_url or app_settings.redis_url
            self.redis_client = redis.from_url(
                url,
                decode_responses=redis_config['decode_responses'],
                socket_connect_timeout=redis_config['socket_connect_timeout'],
                socket_timeout=redis_config['socket_timeout'],
                retry_on_timeout=redis_config['retry_on_timeout'],
                max_connections=redis_config['max_connections'],
                health_check_interval=redis_config['health_check_interval']
            )
        else:
            # Initialize Redis connection with individual parameters
            self.redis_client = redis.Redis(**redis_config)
        
        # Store TTL settings from config
        self.ttl_settings = {
            'session': app_settings.redis_session_ttl,
            'profile': app_settings.redis_profile_ttl,
            'draft': app_settings.redis_draft_ttl,
            'llm_response': app_settings.redis_llm_response_ttl,
            'rate_limit': app_settings.redis_rate_limit_ttl,
            'metrics': app_settings.redis_metrics_ttl
        }
        
        # Test connection
        try:
            self.redis_client.ping()
            self.available = True
        except (redis.ConnectionError, redis.TimeoutError):
            self.available = False
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.prefix}{key}"
    
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self.available
    
    # Session Management
    def set_session(self, token: str, session_data: Dict, ttl_hours: Optional[int] = None) -> bool:
        """
        Store session data in Redis.
        
        Args:
            token: Session token
            session_data: Session information
            ttl_hours: Time to live in hours
            
        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"session:{token}")
            # Use config TTL if not provided
            ttl_seconds = (ttl_hours * 3600) if ttl_hours is not None else self.ttl_settings['session']
            
            return self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(session_data)
            )
        except Exception:
            return False
    
    def get_session(self, token: str) -> Optional[Dict]:
        """
        Retrieve session data from Redis.
        
        Args:
            token: Session token
            
        Returns:
            Session data or None if not found
        """
        if not self.available:
            return None
        
        try:
            key = self._make_key(f"session:{token}")
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    def delete_session(self, token: str) -> bool:
        """Delete session from Redis."""
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"session:{token}")
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    def extend_session(self, token: str, ttl_hours: Optional[int] = None) -> bool:
        """Extend session TTL."""
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"session:{token}")
            ttl_seconds = (ttl_hours * 3600) if ttl_hours is not None else self.ttl_settings['session']
            return bool(self.redis_client.expire(key, ttl_seconds))
        except Exception:
            return False
    
    # User Profile Caching
    def set_user_profile(self, user_id: str, profile_data: Dict, ttl_hours: Optional[int] = None) -> bool:
        """Cache user profile data."""
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"profile:{user_id}")
            ttl_seconds = (ttl_hours * 3600) if ttl_hours is not None else self.ttl_settings['profile']
            
            return self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(profile_data)
            )
        except Exception:
            return False
    
    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Get cached user profile."""
        if not self.available:
            return None
        
        try:
            key = self._make_key(f"profile:{user_id}")
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    def invalidate_user_profile(self, user_id: str) -> bool:
        """Invalidate user profile cache."""
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"profile:{user_id}")
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    # Email Draft Caching
    def cache_email_draft(
        self,
        user_id: str,
        draft_id: str,
        draft_data: Dict,
        ttl_hours: Optional[int] = None
    ) -> bool:
        """Cache email draft."""
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"draft:{user_id}:{draft_id}")
            ttl_seconds = (ttl_hours * 3600) if ttl_hours is not None else self.ttl_settings['draft']
            
            return self.redis_client.setex(
                key,
                ttl_seconds,
                json.dumps(draft_data)
            )
        except Exception:
            return False
    
    def get_cached_draft(self, user_id: str, draft_id: str) -> Optional[Dict]:
        """Get cached email draft."""
        if not self.available:
            return None
        
        try:
            key = self._make_key(f"draft:{user_id}:{draft_id}")
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    def get_user_drafts(self, user_id: str) -> List[Dict]:
        """Get all cached drafts for a user."""
        if not self.available:
            return []
        
        try:
            pattern = self._make_key(f"draft:{user_id}:*")
            keys = self.redis_client.keys(pattern)
            
            drafts = []
            for key in keys:
                data = self.redis_client.get(key)
                if data:
                    drafts.append(json.loads(data))
            
            return drafts
        except Exception:
            return []
    
    # LLM Response Caching
    def cache_llm_response(
        self,
        prompt_hash: str,
        model: str,
        response_data: Dict,
        ttl_hours: Optional[int] = None
    ) -> bool:
        """Cache LLM response for repeated prompts."""
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"llm:{model}:{prompt_hash}")
            ttl_seconds = (ttl_hours * 3600) if ttl_hours is not None else self.ttl_settings['llm_response']
            
            return self.redis_client.setex(
                key,
                ttl_seconds,
                pickle.dumps(response_data)  # Use pickle for complex objects
            )
        except Exception:
            return False
    
    def get_cached_llm_response(self, prompt_hash: str, model: str) -> Optional[Dict]:
        """Get cached LLM response."""
        if not self.available:
            return None
        
        try:
            key = self._make_key(f"llm:{model}:{prompt_hash}")
            data = self.redis_client.get(key)
            
            if data:
                return pickle.loads(data)
            return None
        except Exception:
            return None
    
    # Metrics Caching
    def cache_metrics(self, user_id: str, metrics_data: Dict, ttl_minutes: int = 5) -> bool:
        """Cache user metrics for short periods."""
        if not self.available:
            return False
        
        try:
            key = self._make_key(f"metrics:{user_id}")
            ttl = timedelta(minutes=ttl_minutes)
            
            return self.redis_client.setex(
                key,
                ttl,
                json.dumps(metrics_data)
            )
        except Exception:
            return False
    
    def get_cached_metrics(self, user_id: str) -> Optional[Dict]:
        """Get cached metrics."""
        if not self.available:
            return None
        
        try:
            key = self._make_key(f"metrics:{user_id}")
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None
    
    # Rate Limiting Support
    def increment_rate_limit(
        self,
        key: str,
        window_seconds: int = 60,
        max_requests: int = 60
    ) -> tuple[int, bool]:
        """
        Implement rate limiting using Redis.
        
        Args:
            key: Rate limit key (e.g., user_id, ip_address)
            window_seconds: Time window in seconds
            max_requests: Maximum requests per window
            
        Returns:
            Tuple of (current_count, is_allowed)
        """
        if not self.available:
            return 0, True
        
        try:
            rate_key = self._make_key(f"rate:{key}")
            
            # Use Redis pipeline for atomic operations
            with self.redis_client.pipeline() as pipe:
                pipe.incr(rate_key)
                pipe.expire(rate_key, window_seconds)
                results = pipe.execute()
            
            current_count = results[0]
            is_allowed = current_count <= max_requests
            
            return current_count, is_allowed
        except Exception:
            return 0, True  # Allow on error
    
    # Utility Methods
    def flush_user_data(self, user_id: str) -> int:
        """Flush all cached data for a user."""
        if not self.available:
            return 0
        
        try:
            patterns = [
                f"session:*",  # Would need to check session data
                f"profile:{user_id}",
                f"draft:{user_id}:*",
                f"metrics:{user_id}",
                f"rate:{user_id}"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                keys = self.redis_client.keys(self._make_key(pattern))
                if keys:
                    deleted_count += self.redis_client.delete(*keys)
            
            return deleted_count
        except Exception:
            return 0
    
    def get_cache_stats(self) -> Dict:
        """Get Redis cache statistics."""
        if not self.available:
            return {"available": False}
        
        try:
            info = self.redis_client.info()
            
            return {
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                ) * 100
            }
        except Exception:
            return {"available": False, "error": "Failed to get stats"}
    
    def clear_all_cache(self) -> bool:
        """Clear all app-related cache (use with caution)."""
        if not self.available:
            return False
        
        try:
            pattern = self._make_key("*")
            keys = self.redis_client.keys(pattern)
            
            if keys:
                return bool(self.redis_client.delete(*keys))
            return True
        except Exception:
            return False


# Factory function for easy initialization
def create_redis_cache(
    use_redis: Optional[bool] = None,
    redis_url: Optional[str] = None,
    **kwargs
) -> Optional[RedisCacheManager]:
    """
    Factory function to create Redis cache manager.
    
    Args:
        use_redis: Whether to use Redis (uses config if None)
        redis_url: Redis URL (uses config if None)
        **kwargs: Additional Redis connection parameters
        
    Returns:
        RedisCacheManager instance or None if disabled/unavailable
    """
    # Use settings to determine if Redis should be enabled
    use_redis = use_redis if use_redis is not None else app_settings.enable_redis
    if not use_redis:
        return None
    
    # Parse Redis URL if provided
    if redis_url:
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(redis_url)
            
            kwargs.update({
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 6379,
                "password": parsed.password,
                "db": int(parsed.path.lstrip("/")) if parsed.path else 0
            })
        except Exception:
            pass  # Fall back to default parameters
    
    try:
        cache = RedisCacheManager(**kwargs)
        return cache if cache.is_available() else None
    except Exception:
        return None