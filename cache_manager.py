import time
import logging
from typing import Any, Optional
import json
import hashlib

class CacheManager:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self.cache = {}
        self.ttl = {}
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self.ttl:
            return True
        return time.time() > self.ttl[key]
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [key for key, expiry in self.ttl.items() if current_time > expiry]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.ttl.pop(key, None)
    
    def _hash_key(self, key: str) -> str:
        """Create a consistent hash for the key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        try:
            hashed_key = self._hash_key(key)
            
            if hashed_key not in self.cache:
                return None
            
            if self._is_expired(hashed_key):
                self.cache.pop(hashed_key, None)
                self.ttl.pop(hashed_key, None)
                return None
            
            logging.debug(f"Cache hit for key: {key}")
            return self.cache[hashed_key]
            
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
        """
        try:
            hashed_key = self._hash_key(key)
            
            # Cleanup expired entries occasionally
            if len(self.cache) % 100 == 0:
                self._cleanup_expired()
            
            self.cache[hashed_key] = value
            self.ttl[hashed_key] = time.time() + ttl_seconds
            
            logging.debug(f"Cache set for key: {key}, TTL: {ttl_seconds}s")
            
        except Exception as e:
            logging.error(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """Delete value from cache"""
        try:
            hashed_key = self._hash_key(key)
            self.cache.pop(hashed_key, None)
            self.ttl.pop(hashed_key, None)
            logging.debug(f"Cache delete for key: {key}")
            
        except Exception as e:
            logging.error(f"Cache delete error: {e}")
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.ttl.clear()
        logging.info("Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        current_time = time.time()
        active_entries = sum(1 for expiry in self.ttl.values() if current_time <= expiry)
        
        return {
            'total_entries': len(self.cache),
            'active_entries': active_entries,
            'expired_entries': len(self.cache) - active_entries
        }
