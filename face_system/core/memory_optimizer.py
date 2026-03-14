"""
Memory Optimization Module - Face Recognition System
"""
import numpy as np
import gc
import psutil
import os
import cv2
from typing import List, Tuple, Optional
import threading
import time

class MemoryOptimizer:
    """Memory management va optimization"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.get_memory_usage()
        self.peak_memory = self.initial_memory
        self.lock = threading.Lock()
        
        print(f"🧠 MemoryOptimizer initialized - Initial memory: {self.initial_memory:.1f} MB")
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def compress_encodings(self, encodings: List[np.ndarray]) -> Tuple[np.ndarray, dict]:
        """Compress face encodings to save memory"""
        try:
            # Convert to single numpy array
            encodings_array = np.array(encodings, dtype=np.float32)  # Use float32 instead of float64
            
            # Compression metadata
            compression_info = {
                'original_dtype': str(encodings[0].dtype),
                'compressed_dtype': str(encodings_array.dtype),
                'original_size': sum(enc.nbytes for enc in encodings),
                'compressed_size': encodings_array.nbytes,
                'count': len(encodings)
            }
            
            compression_ratio = compression_info['original_size'] / compression_info['compressed_size']
            print(f"🗜️  Encodings compressed: {compression_ratio:.1f}x smaller")
            
            return encodings_array, compression_info
            
        except Exception as e:
            print(f"❌ Compression error: {e}")
            return np.array(encodings), {}
    
    def decompress_encodings(self, compressed_array: np.ndarray, compression_info: dict) -> List[np.ndarray]:
        """Decompress face encodings"""
        try:
            # Convert back to list of individual arrays
            encodings_list = [compressed_array[i] for i in range(len(compressed_array))]
            return encodings_list
            
        except Exception as e:
            print(f"❌ Decompression error: {e}")
            return []
    
    def optimize_numpy_arrays(self, encodings: List[np.ndarray]) -> List[np.ndarray]:
        """Optimize numpy arrays for memory efficiency"""
        optimized = []
        
        for encoding in encodings:
            # Convert to float32 if it's float64
            if encoding.dtype == np.float64:
                optimized_encoding = encoding.astype(np.float32)
            else:
                optimized_encoding = encoding
            
            # Make array contiguous in memory
            optimized_encoding = np.ascontiguousarray(optimized_encoding)
            
            # Explicit cleanup of original if different
            if optimized_encoding is not encoding:
                del encoding
            
            optimized.append(optimized_encoding)
        
        return optimized
    
    def cleanup_opencv_memory(self):
        """Clean up OpenCV memory leaks"""
        try:
            # Force OpenCV cleanup
            cv2.destroyAllWindows()
            
            # Clear internal caches if available
            if hasattr(cv2, 'clearCache'):
                cv2.clearCache()
            
            print("🧹 OpenCV memory cleaned")
            
        except Exception as e:
            print(f"❌ OpenCV cleanup error: {e}")
    
    def monitor_memory_threshold(self, threshold_mb: int = 500) -> bool:
        """Monitor memory usage and trigger cleanup if needed"""
        current_memory = self.get_memory_usage()
        
        if current_memory > threshold_mb:
            print(f"⚠️  Memory threshold exceeded: {current_memory:.1f}MB > {threshold_mb}MB")
            
            # Force cleanup
            freed = self.force_garbage_collection()
            self.cleanup_opencv_memory()
            
            # Check again
            new_memory = self.get_memory_usage()
            total_freed = current_memory - new_memory
            
            print(f"🧹 Memory cleanup: {total_freed:.1f}MB freed")
            
            return new_memory < threshold_mb
        
        return True
    
    def force_garbage_collection(self):
        """Force garbage collection"""
        with self.lock:
            before_memory = self.get_memory_usage()
            
            # Force garbage collection
            collected = gc.collect()
            
            after_memory = self.get_memory_usage()
            freed_memory = before_memory - after_memory
            
            if freed_memory > 0:
                print(f"🗑️  GC: Freed {freed_memory:.1f} MB, collected {collected} objects")
            
            return freed_memory
    
    def monitor_memory(self):
        """Monitor memory usage"""
        current_memory = self.get_memory_usage()
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
        
        return {
            'current_mb': current_memory,
            'peak_mb': self.peak_memory,
            'initial_mb': self.initial_memory,
            'increase_mb': current_memory - self.initial_memory
        }
    
    def print_memory_stats(self):
        """Print memory statistics"""
        stats = self.monitor_memory()
        print(f"""
🧠 Memory Statistics:
   Current: {stats['current_mb']:.1f} MB
   Peak: {stats['peak_mb']:.1f} MB
   Initial: {stats['initial_mb']:.1f} MB
   Increase: {stats['increase_mb']:.1f} MB
        """)
    
    def optimize_system_memory(self):
        """System-wide memory optimization"""
        try:
            # Force garbage collection
            freed = self.force_garbage_collection()
            
            # Clear numpy cache
            if hasattr(np, 'clear_cache'):
                np.clear_cache()
            
            # System memory info
            memory = psutil.virtual_memory()
            
            print(f"💾 System Memory: {memory.percent}% used, {memory.available / 1024 / 1024 / 1024:.1f} GB available")
            
            return freed
            
        except Exception as e:
            print(f"❌ Memory optimization error: {e}")
            return 0

# Global memory optimizer instance
_memory_optimizer = None

def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer instance"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer