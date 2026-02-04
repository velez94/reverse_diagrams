"""Caching system for AWS API responses."""
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import tempfile
import os

from ..config import get_config

logger = logging.getLogger(__name__)


class AWSDataCache:
    """Cache for AWS API responses with TTL support."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 1):
        """
        Initialize cache.
        
        Args:
            cache_dir: Cache directory path (optional, uses temp dir if None)
            ttl_hours: Time to live in hours
        """
        if cache_dir is None:
            cache_dir = Path(tempfile.gettempdir()) / "reverse_diagrams_cache"
        
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Set appropriate permissions
        try:
            os.chmod(self.cache_dir, 0o755)
        except OSError:
            logger.warning(f"Could not set permissions on cache directory: {self.cache_dir}")
        
        logger.debug(f"Cache initialized at {self.cache_dir} with TTL {ttl_hours}h")
    
    def _get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """
        Generate cache key from operation and parameters.
        
        Args:
            operation: AWS operation name
            params: Operation parameters
            
        Returns:
            Cache key string
        """
        # Sort parameters for consistent hashing
        param_str = json.dumps(params, sort_keys=True, default=str)
        cache_string = f"{operation}:{param_str}"
        
        # Create hash
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        Get cached data if still valid.
        
        Args:
            operation: AWS operation name
            params: Operation parameters
            
        Returns:
            Cached data if valid, None otherwise
        """
        try:
            cache_key = self._get_cache_key(operation, params)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if not cache_file.exists():
                logger.debug(f"Cache miss for {operation}")
                return None
            
            # Check if cache is still valid
            stat = cache_file.stat()
            cache_time = datetime.fromtimestamp(stat.st_mtime)
            
            if cache_time + self.ttl < datetime.now():
                logger.debug(f"Cache expired for {operation}")
                # Clean up expired cache
                try:
                    cache_file.unlink()
                except OSError:
                    pass
                return None
            
            # Load and return cached data
            with cache_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Cache hit for {operation}")
            return data
            
        except Exception as e:
            logger.warning(f"Error reading cache for {operation}: {e}")
            return None
    
    def set(self, operation: str, params: Dict[str, Any], data: Any) -> None:
        """
        Cache data.
        
        Args:
            operation: AWS operation name
            params: Operation parameters
            data: Data to cache
        """
        try:
            cache_key = self._get_cache_key(operation, params)
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            # Write data to cache
            with cache_file.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Set appropriate permissions
            try:
                os.chmod(cache_file, 0o644)
            except OSError:
                pass
            
            logger.debug(f"Cached data for {operation}")
            
        except Exception as e:
            logger.warning(f"Error writing cache for {operation}: {e}")
    
    def clear(self) -> None:
        """Clear all cached data."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
    
    def clear_expired(self) -> int:
        """
        Clear expired cache entries.
        
        Returns:
            Number of entries cleared
        """
        cleared = 0
        try:
            current_time = datetime.now()
            
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    stat = cache_file.stat()
                    cache_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    if cache_time + self.ttl < current_time:
                        cache_file.unlink()
                        cleared += 1
                        
                except OSError:
                    continue
            
            if cleared > 0:
                logger.info(f"Cleared {cleared} expired cache entries")
                
        except Exception as e:
            logger.warning(f"Error clearing expired cache: {e}")
        
        return cleared
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache information
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            # Count expired entries
            current_time = datetime.now()
            expired = 0
            
            for cache_file in cache_files:
                try:
                    stat = cache_file.stat()
                    cache_time = datetime.fromtimestamp(stat.st_mtime)
                    if cache_time + self.ttl < current_time:
                        expired += 1
                except OSError:
                    continue
            
            return {
                "cache_dir": str(self.cache_dir),
                "total_entries": len(cache_files),
                "expired_entries": expired,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "ttl_hours": self.ttl.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.warning(f"Error getting cache info: {e}")
            return {"error": str(e)}


# Global cache instance
_cache: Optional[AWSDataCache] = None


def get_cache() -> AWSDataCache:
    """Get or create global cache instance."""
    global _cache
    
    if _cache is None:
        config = get_config()
        if config.enable_caching:
            _cache = AWSDataCache(ttl_hours=config.cache_ttl_hours)
        else:
            # Create a no-op cache that doesn't actually cache
            _cache = NoOpCache()
    
    return _cache


class NoOpCache:
    """No-operation cache for when caching is disabled."""
    
    def get(self, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        return None
    
    def set(self, operation: str, params: Dict[str, Any], data: Any) -> None:
        pass
    
    def clear(self) -> None:
        pass
    
    def clear_expired(self) -> int:
        return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        return {"caching": "disabled"}


def cached_aws_call(operation: str, params: Dict[str, Any], fetch_func) -> Any:
    """
    Decorator-like function for caching AWS API calls.
    
    Args:
        operation: AWS operation name
        params: Operation parameters
        fetch_func: Function to call if cache miss
        
    Returns:
        Cached or fresh data
    """
    cache = get_cache()
    
    # Try to get from cache first
    cached_data = cache.get(operation, params)
    if cached_data is not None:
        return cached_data
    
    # Cache miss - fetch fresh data
    fresh_data = fetch_func()
    
    # Cache the result
    cache.set(operation, params, fresh_data)
    
    return fresh_data