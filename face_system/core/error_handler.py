"""
Professional Error Handler - Comprehensive error management
"""
import logging
import traceback
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from enum import Enum
import json

class ErrorLevel(Enum):
    """Error severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ErrorHandler:
    """Professional error handling and logging"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.setup_logging()
        
        # Error statistics
        self.error_stats = {
            'total_errors': 0,
            'critical_errors': 0,
            'warnings': 0,
            'last_error_time': None,
            'error_types': {}
        }
        
        # Error callbacks
        self.error_callbacks = {}
        
        print(f"🛡️  ErrorHandler initialized - Log dir: {log_dir}")
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        # Create logs directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configure main logger
        self.logger = logging.getLogger('FaceRecognitionSystem')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler for all logs
        log_file = os.path.join(self.log_dir, 'system.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # File handler for errors only
        error_file = os.path.join(self.log_dir, 'errors.log')
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def log_error(self, error: Exception, context: str = "", 
                  level: ErrorLevel = ErrorLevel.ERROR,
                  extra_data: Optional[Dict[str, Any]] = None):
        """Log error with full context"""
        try:
            # Update statistics
            self.error_stats['total_errors'] += 1
            self.error_stats['last_error_time'] = datetime.now().isoformat()
            
            if level == ErrorLevel.CRITICAL:
                self.error_stats['critical_errors'] += 1
            elif level == ErrorLevel.WARNING:
                self.error_stats['warnings'] += 1
            
            # Track error types
            error_type = type(error).__name__
            self.error_stats['error_types'][error_type] = \
                self.error_stats['error_types'].get(error_type, 0) + 1
            
            # Prepare error data
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'level': level.value,
                'context': context,
                'error_type': error_type,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'extra_data': extra_data or {}
            }
            
            # Log to file
            log_message = f"{context}: {error_type}: {str(error)}"
            
            if level == ErrorLevel.DEBUG:
                self.logger.debug(log_message)
            elif level == ErrorLevel.INFO:
                self.logger.info(log_message)
            elif level == ErrorLevel.WARNING:
                self.logger.warning(log_message)
            elif level == ErrorLevel.ERROR:
                self.logger.error(log_message)
            elif level == ErrorLevel.CRITICAL:
                self.logger.critical(log_message)
            
            # Save detailed error to JSON
            self._save_error_details(error_data)
            
            # Call error callbacks
            self._call_error_callbacks(level, error_data)
            
        except Exception as e:
            # Fallback error logging
            print(f"❌ Error handler failed: {e}")
            print(f"Original error: {error}")
    
    def log_info(self, message: str, context: str = "", 
                extra_data: Optional[Dict[str, Any]] = None):
        """Log info message"""
        try:
            log_message = f"{context}: {message}" if context else message
            self.logger.info(log_message)
            
            if extra_data:
                self.logger.debug(f"Extra data: {json.dumps(extra_data, default=str)}")
                
        except Exception as e:
            print(f"❌ Info logging failed: {e}")
    
    def log_warning(self, message: str, context: str = "",
                   extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        try:
            self.error_stats['warnings'] += 1
            
            log_message = f"{context}: {message}" if context else message
            self.logger.warning(log_message)
            
            if extra_data:
                self.logger.debug(f"Extra data: {json.dumps(extra_data, default=str)}")
                
        except Exception as e:
            print(f"❌ Warning logging failed: {e}")
    
    def _save_error_details(self, error_data: Dict[str, Any]):
        """Save detailed error information"""
        try:
            error_file = os.path.join(self.log_dir, 'error_details.jsonl')
            
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, default=str) + '\n')
                
        except Exception as e:
            print(f"❌ Error details save failed: {e}")
    
    def register_error_callback(self, level: ErrorLevel, callback: Callable):
        """Register callback for specific error level"""
        if level not in self.error_callbacks:
            self.error_callbacks[level] = []
        
        self.error_callbacks[level].append(callback)
        print(f"📞 Error callback registered for {level.value}")
    
    def _call_error_callbacks(self, level: ErrorLevel, error_data: Dict[str, Any]):
        """Call registered error callbacks"""
        try:
            callbacks = self.error_callbacks.get(level, [])
            for callback in callbacks:
                try:
                    callback(error_data)
                except Exception as e:
                    print(f"❌ Error callback failed: {e}")
                    
        except Exception as e:
            print(f"❌ Error callback execution failed: {e}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return self.error_stats.copy()
    
    def get_recent_errors(self, count: int = 10) -> list:
        """Get recent error details"""
        try:
            error_file = os.path.join(self.log_dir, 'error_details.jsonl')
            
            if not os.path.exists(error_file):
                return []
            
            errors = []
            with open(error_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get last N lines
            recent_lines = lines[-count:] if len(lines) > count else lines
            
            for line in recent_lines:
                try:
                    error_data = json.loads(line.strip())
                    errors.append(error_data)
                except:
                    continue
            
            return errors
            
        except Exception as e:
            print(f"❌ Get recent errors failed: {e}")
            return []
    
    def print_error_summary(self):
        """Print error summary"""
        stats = self.get_error_stats()
        
        print("\n" + "="*50)
        print("🛡️  ERROR SUMMARY")
        print("="*50)
        print(f"Total Errors: {stats['total_errors']}")
        print(f"Critical Errors: {stats['critical_errors']}")
        print(f"Warnings: {stats['warnings']}")
        print(f"Last Error: {stats['last_error_time']}")
        
        if stats['error_types']:
            print("\nError Types:")
            for error_type, count in stats['error_types'].items():
                print(f"   {error_type}: {count}")
        
        print("="*50)
    
    def clear_old_logs(self, days: int = 30):
        """Clear old log files"""
        try:
            import glob
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            log_files = glob.glob(os.path.join(self.log_dir, '*.log*'))
            cleared_count = 0
            
            for log_file in log_files:
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    if file_time < cutoff_date:
                        os.remove(log_file)
                        cleared_count += 1
                except:
                    continue
            
            if cleared_count > 0:
                print(f"🧹 Cleared {cleared_count} old log files")
                
        except Exception as e:
            print(f"❌ Log cleanup failed: {e}")

# Global error handler instance
_error_handler = None

def get_error_handler() -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

# Decorator for automatic error handling
def handle_errors(context: str = "", level: ErrorLevel = ErrorLevel.ERROR):
    """Decorator for automatic error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                func_context = f"{context} - {func.__name__}" if context else func.__name__
                error_handler.log_error(e, func_context, level)
                raise  # Re-raise the exception
        return wrapper
    return decorator