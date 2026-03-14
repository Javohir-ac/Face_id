"""
Performance Monitor - Face Recognition System
"""
import time
import psutil
import threading
from typing import Dict, List
from datetime import datetime
import json

class PerformanceMonitor:
    """System performance monitoring"""
    
    def __init__(self):
        self.metrics = {
            'recognition_times': [],
            'frame_processing_times': [],
            'database_query_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'cache_hit_rates': []
        }
        
        self.start_time = time.time()
        self.lock = threading.Lock()
        
        print("📊 PerformanceMonitor initialized")
    
    def record_recognition_time(self, duration: float):
        """Record face recognition time"""
        with self.lock:
            self.metrics['recognition_times'].append(duration)
            # Keep only last 100 measurements
            if len(self.metrics['recognition_times']) > 100:
                self.metrics['recognition_times'].pop(0)
    
    def record_frame_processing_time(self, duration: float):
        """Record frame processing time"""
        with self.lock:
            self.metrics['frame_processing_times'].append(duration)
            if len(self.metrics['frame_processing_times']) > 100:
                self.metrics['frame_processing_times'].pop(0)
    
    def record_database_query_time(self, duration: float):
        """Record database query time"""
        with self.lock:
            self.metrics['database_query_times'].append(duration)
            if len(self.metrics['database_query_times']) > 50:
                self.metrics['database_query_times'].pop(0)
    
    def record_system_metrics(self):
        """Record system-wide metrics"""
        with self.lock:
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append(memory.percent)
            
            # CPU usage
            cpu = psutil.cpu_percent(interval=None)
            self.metrics['cpu_usage'].append(cpu)
            
            # Keep only last 50 measurements
            for key in ['memory_usage', 'cpu_usage']:
                if len(self.metrics[key]) > 50:
                    self.metrics[key].pop(0)
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        with self.lock:
            stats = {}
            
            # Recognition performance
            if self.metrics['recognition_times']:
                recognition_times = self.metrics['recognition_times']
                stats['recognition'] = {
                    'avg_ms': round(sum(recognition_times) / len(recognition_times) * 1000, 2),
                    'min_ms': round(min(recognition_times) * 1000, 2),
                    'max_ms': round(max(recognition_times) * 1000, 2),
                    'count': len(recognition_times)
                }
            
            # Frame processing performance
            if self.metrics['frame_processing_times']:
                frame_times = self.metrics['frame_processing_times']
                stats['frame_processing'] = {
                    'avg_ms': round(sum(frame_times) / len(frame_times) * 1000, 2),
                    'fps': round(1.0 / (sum(frame_times) / len(frame_times)), 1),
                    'count': len(frame_times)
                }
            
            # Database performance
            if self.metrics['database_query_times']:
                db_times = self.metrics['database_query_times']
                stats['database'] = {
                    'avg_ms': round(sum(db_times) / len(db_times) * 1000, 2),
                    'min_ms': round(min(db_times) * 1000, 2),
                    'max_ms': round(max(db_times) * 1000, 2),
                    'count': len(db_times)
                }
            
            # System metrics
            if self.metrics['memory_usage']:
                stats['system'] = {
                    'memory_percent': round(sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage']), 1),
                    'cpu_percent': round(sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage']), 1) if self.metrics['cpu_usage'] else 0
                }
            
            # Uptime
            stats['uptime_seconds'] = round(time.time() - self.start_time, 1)
            
            return stats
    
    def print_performance_report(self):
        """Print detailed performance report"""
        stats = self.get_performance_stats()
        
        print("\n" + "="*50)
        print("📊 PERFORMANCE REPORT")
        print("="*50)
        
        if 'recognition' in stats:
            print(f"🎯 Face Recognition:")
            print(f"   Average: {stats['recognition']['avg_ms']} ms")
            print(f"   Range: {stats['recognition']['min_ms']}-{stats['recognition']['max_ms']} ms")
            print(f"   Count: {stats['recognition']['count']}")
        
        if 'frame_processing' in stats:
            print(f"🎬 Frame Processing:")
            print(f"   Average: {stats['frame_processing']['avg_ms']} ms")
            print(f"   FPS: {stats['frame_processing']['fps']}")
            print(f"   Count: {stats['frame_processing']['count']}")
        
        if 'database' in stats:
            print(f"💾 Database Queries:")
            print(f"   Average: {stats['database']['avg_ms']} ms")
            print(f"   Range: {stats['database']['min_ms']}-{stats['database']['max_ms']} ms")
            print(f"   Count: {stats['database']['count']}")
        
        if 'system' in stats:
            print(f"🖥️  System Resources:")
            print(f"   Memory: {stats['system']['memory_percent']}%")
            print(f"   CPU: {stats['system']['cpu_percent']}%")
        
        print(f"⏱️  Uptime: {stats['uptime_seconds']} seconds")
        print("="*50)
    
    def save_performance_log(self, filename: str = "performance_log.json"):
        """Save performance metrics to file"""
        try:
            stats = self.get_performance_stats()
            stats['timestamp'] = datetime.now().isoformat()
            
            with open(filename, 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"📊 Performance log saved to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving performance log: {e}")

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor