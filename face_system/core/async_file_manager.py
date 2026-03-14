"""
Async File Manager - Non-blocking file operations
"""
import json
import threading
import queue
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import os

class AsyncFileManager:
    """Asynchronous file operations to prevent blocking"""
    
    def __init__(self, max_queue_size: int = 100):
        self.write_queue = queue.Queue(maxsize=max_queue_size)
        self.worker_thread = None
        self.is_running = False
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'writes_queued': 0,
            'writes_completed': 0,
            'writes_failed': 0,
            'queue_full_errors': 0
        }
        
        print("📁 AsyncFileManager initialized")
    
    def start(self):
        """Start async file worker"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        
        print("🚀 Async file worker started")
    
    def stop(self):
        """Stop async file worker"""
        self.is_running = False
        
        # Add stop signal to queue
        try:
            self.write_queue.put(('STOP', None, None, None), timeout=1)
        except queue.Full:
            pass
        
        # Wait for worker to finish
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        
        print("🛑 Async file worker stopped")
    
    def _worker(self):
        """Background worker for file operations"""
        while self.is_running:
            try:
                # Get task from queue
                task = self.write_queue.get(timeout=1)
                
                if task[0] == 'STOP':
                    break
                
                operation, filepath, data, callback = task
                
                # Perform file operation
                success = False
                error = None
                
                try:
                    if operation == 'write_json':
                        success = self._write_json_sync(filepath, data)
                    elif operation == 'append_log':
                        success = self._append_log_sync(filepath, data)
                    
                    if success:
                        self.stats['writes_completed'] += 1
                    else:
                        self.stats['writes_failed'] += 1
                        
                except Exception as e:
                    error = e
                    self.stats['writes_failed'] += 1
                
                # Call callback if provided
                if callback:
                    try:
                        callback(success, error)
                    except:
                        pass
                
                # Mark task as done
                self.write_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Async file worker error: {e}")
    
    def write_json_async(self, filepath: str, data: Dict[str, Any], 
                        callback: Optional[Callable] = None) -> bool:
        """Queue JSON write operation"""
        try:
            self.write_queue.put(('write_json', filepath, data, callback), block=False)
            self.stats['writes_queued'] += 1
            return True
            
        except queue.Full:
            self.stats['queue_full_errors'] += 1
            print(f"⚠️  Async write queue full, falling back to sync write: {filepath}")
            
            # Fallback to synchronous write
            return self._write_json_sync(filepath, data)
    
    def append_log_async(self, filepath: str, log_entry: str,
                        callback: Optional[Callable] = None) -> bool:
        """Queue log append operation"""
        try:
            self.write_queue.put(('append_log', filepath, log_entry, callback), block=False)
            self.stats['writes_queued'] += 1
            return True
            
        except queue.Full:
            self.stats['queue_full_errors'] += 1
            print(f"⚠️  Async log queue full, falling back to sync write: {filepath}")
            
            # Fallback to synchronous write
            return self._append_log_sync(filepath, log_entry)
    
    def _write_json_sync(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Synchronous JSON write with error handling"""
        try:
            # Create backup if file exists
            if os.path.exists(filepath):
                backup_path = f"{filepath}.backup"
                try:
                    os.rename(filepath, backup_path)
                except:
                    pass
            
            # Write new data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Remove backup on success
            backup_path = f"{filepath}.backup"
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"❌ JSON write error {filepath}: {e}")
            
            # Restore backup if available
            backup_path = f"{filepath}.backup"
            if os.path.exists(backup_path):
                try:
                    os.rename(backup_path, filepath)
                    print(f"🔄 Restored backup: {filepath}")
                except:
                    pass
            
            return False
    
    def _append_log_sync(self, filepath: str, log_entry: str) -> bool:
        """Synchronous log append with rotation"""
        try:
            # Check file size and rotate if needed
            max_size = 10 * 1024 * 1024  # 10MB
            
            if os.path.exists(filepath) and os.path.getsize(filepath) > max_size:
                # Rotate log file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                rotated_path = f"{filepath}.{timestamp}"
                os.rename(filepath, rotated_path)
                print(f"🔄 Log rotated: {rotated_path}")
            
            # Append log entry
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - {log_entry}\n")
                f.flush()  # Force write to disk
            
            return True
            
        except Exception as e:
            print(f"❌ Log append error {filepath}: {e}")
            return False
    
    def write_json_sync_safe(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Safe synchronous JSON write (for critical operations)"""
        return self._write_json_sync(filepath, data)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get async queue status"""
        return {
            'queue_size': self.write_queue.qsize(),
            'is_running': self.is_running,
            'stats': self.stats.copy()
        }
    
    def wait_for_completion(self, timeout: float = 10.0) -> bool:
        """Wait for all queued operations to complete"""
        try:
            # Wait for queue to be empty
            start_time = time.time()
            while not self.write_queue.empty():
                if time.time() - start_time > timeout:
                    return False
                time.sleep(0.1)
            
            # Wait for all tasks to be done
            self.write_queue.join()
            return True
            
        except Exception as e:
            print(f"❌ Wait for completion error: {e}")
            return False
    
    def print_stats(self):
        """Print file operation statistics"""
        stats = self.get_queue_status()
        print(f"""
📁 Async File Manager Statistics:
   Queue Size: {stats['queue_size']}
   Running: {stats['is_running']}
   Writes Queued: {stats['stats']['writes_queued']}
   Writes Completed: {stats['stats']['writes_completed']}
   Writes Failed: {stats['stats']['writes_failed']}
   Queue Full Errors: {stats['stats']['queue_full_errors']}
        """)

# Global async file manager instance
_async_file_manager = None

def get_async_file_manager() -> AsyncFileManager:
    """Get global async file manager instance"""
    global _async_file_manager
    if _async_file_manager is None:
        _async_file_manager = AsyncFileManager()
        _async_file_manager.start()
    return _async_file_manager