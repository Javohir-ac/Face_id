"""
High-Performance Cache Manager - Face Recognition System
"""
import pickle
import hashlib
import time
import os
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import threading
import json

class CacheManager:
    """Professional caching system for face recognition"""
    
    def __init__(self, cache_dir: str = "cache", max_memory_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory_usage = 0
        
        # In-memory cache
        self.memory_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_access_count: Dict[str, int] = {}
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_usage': 0
        }
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        print(f"🚀 CacheManager initialized - Max memory: {max_memory_mb}MB")
    
    def _generate_key(self, data: Any) -> str:
        """Generate unique cache key"""
        if isinstance(data, str):
            return hashlib.md5(data.encode()).hexdigest()
        elif isinstance(data, (list, tuple)):
            return hashlib.md5(str(data).encode()).hexdigest()
        elif isinstance(data, np.ndarray):
            return hashlib.md5(data.tobytes()).hexdigest()
        else:
            return hashlib.md5(str(data).encode()).hexdigest()
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate object size in bytes"""
        if isinstance(obj, np.ndarray):
            return obj.nbytes
        elif isinstance(obj, (list, tuple)):
            return sum(self._estimate_size(item) for item in obj)
        elif isinstance(obj, dict):
            return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in obj.items())
        elif isinstance(obj, str):
            return len(obj.encode('utf-8'))
        else:
            # Fallback to pickle size
            try:
                return len(pickle.dumps(obj))
            except:
                return 1024  # Default estimate
    
    def _evict_lru(self, needed_space: int):
        """Evict least recently used items"""
        with self.lock:
            # Sort by access time (oldest first)
            sorted_keys = sorted(
                self.cache_timestamps.keys(),
                key=lambda k: (self.cache_timestamps[k], self.cache_access_count.get(k, 0))
            )
            
            freed_space = 0
            for key in sorted_keys:
                if freed_space >= needed_space:
                    break
                
                obj_size = self._estimate_size(self.memory_cache[key])
                
                # Remove from cache
                del self.memory_cache[key]
                del self.cache_timestamps[key]
                if key in self.cache_access_count:
                    del self.cache_access_count[key]
                
                freed_space += obj_size
                self.current_memory_usage -= obj_size
                self.stats['evictions'] += 1
            
            print(f"🗑️  Evicted {len(sorted_keys[:self.stats['evictions']])} items, freed {freed_space} bytes")
    
    def put(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Store value in cache"""
        try:
            with self.lock:
                cache_key = self._generate_key(key)
                obj_size = self._estimate_size(value)
                
                # Check if we need to evict
                if self.current_memory_usage + obj_size > self.max_memory_bytes:
                    needed_space = obj_size - (self.max_memory_bytes - self.current_memory_usage)
                    self._evict_lru(needed_space)
                
                # Store in cache
                self.memory_cache[cache_key] = value
                self.cache_timestamps[cache_key] = time.time() + ttl_seconds
                self.cache_access_count[cache_key] = 0
                self.current_memory_usage += obj_size
                
                # Update stats
                self.stats['memory_usage'] = self.current_memory_usage
                
                return True
                
        except Exception as e:
            print(f"❌ Cache put error: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache"""
        try:
            with self.lock:
                cache_key = self._generate_key(key)
                
                if cache_key not in self.memory_cache:
                    self.stats['misses'] += 1
                    return None
                
                # Check TTL
                if time.time() > self.cache_timestamps[cache_key]:
                    # Expired
                    obj_size = self._estimate_size(self.memory_cache[cache_key])
                    del self.memory_cache[cache_key]
                    del self.cache_timestamps[cache_key]
                    if cache_key in self.cache_access_count:
                        del self.cache_access_count[cache_key]
                    self.current_memory_usage -= obj_size
                    self.stats['misses'] += 1
                    return None
                
                # Update access info
                self.cache_access_count[cache_key] += 1
                self.stats['hits'] += 1
                
                return self.memory_cache[cache_key]
                
        except Exception as e:
            print(f"❌ Cache get error: {e}")
            self.stats['misses'] += 1
            return None
    
    def put_encodings(self, encodings: List[np.ndarray], names: List[str]) -> bool:
        """Specialized method for face encodings"""
        try:
            # Create optimized storage format
            encodings_array = np.array(encodings)
            cache_data = {
                'encodings': encodings_array,
                'names': names,
                'count': len(names),
                'unique_users': len(set(names)),
                'timestamp': time.time()
            }
            
            return self.put('face_encodings', cache_data, ttl_seconds=7200)  # 2 hours
            
        except Exception as e:
            print(f"❌ Encodings cache error: {e}")
            return False
    
    def get_encodings(self) -> Optional[Tuple[List[np.ndarray], List[str]]]:
        """Specialized method for face encodings"""
        try:
            cache_data = self.get('face_encodings')
            if cache_data is None:
                return None
            
            encodings_array = cache_data['encodings']
            names = cache_data['names']
            
            # Convert back to list
            encodings_list = [encodings_array[i] for i in range(len(encodings_array))]
            
            print(f"✅ Cache hit: {cache_data['count']} encodings, {cache_data['unique_users']} users")
            return encodings_list, names
            
        except Exception as e:
            print(f"❌ Encodings cache get error: {e}")
            return None
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.memory_cache.clear()
            self.cache_timestamps.clear()
            self.cache_access_count.clear()
            self.current_memory_usage = 0
            print("🧹 Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                **self.stats,
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': total_requests,
                'cache_size': len(self.memory_cache),
                'memory_usage_mb': round(self.current_memory_usage / 1024 / 1024, 2)
            }
    
    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_stats()
        print(f"""
📊 Cache Statistics:
   Hit Rate: {stats['hit_rate_percent']}%
   Total Requests: {stats['total_requests']}
   Cache Size: {stats['cache_size']} items
   Memory Usage: {stats['memory_usage_mb']} MB
   Evictions: {stats['evictions']}
        """)

# Global cache instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager