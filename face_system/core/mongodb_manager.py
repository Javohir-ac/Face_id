"""
MongoDB Database Manager - Professional Face Recognition System
Enhanced with connection resilience and retry logic
"""
import os
import pickle
import base64
import time
import threading
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
import numpy as np
from dotenv import load_dotenv
from .error_handler import get_error_handler, handle_errors

# Load environment variables
load_dotenv()

class MongoDBManager:
    """MongoDB ma'lumotlar bazasi boshqaruvchisi"""
    
    def __init__(self):
        self.mongo_uri = os.getenv('MONGODB_URI')
        self.db_name = os.getenv('DATABASE_NAME', 'face_recognition_db')
        
        if not self.mongo_uri:
            raise ValueError("MONGODB_URI environment variable not set")
        
        # Connection management
        self.client = None
        self.db = None
        self.is_connected = False
        self.connection_lock = threading.Lock()
        self.error_handler = get_error_handler()
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2.0
        self.connection_timeout = 10
        
        # Connection statistics
        self.connection_stats = {
            'total_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'last_connection_time': None,
            'last_error': None
        }
        
        # Initial connection
        self.connect()
        
        # Collections (will be set after successful connection)
        self.users_collection = None
        self.encodings_collection = None
        self.attendance_collection = None
        self.logs_collection = None
        self.system_collection = None
        
        if self.is_connected:
            self._setup_collections()
        
        print("🗄️  MongoDB Manager initialized")
    
    def connect(self):
        """MongoDB ga ulanish"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            print("✅ MongoDB ga muvaffaqiyatli ulandi")
            return True
        except ConnectionFailure as e:
            print(f"❌ MongoDB ulanish xatosi: {e}")
            return False
        except Exception as e:
            print(f"❌ MongoDB xatosi: {e}")
            return False
    
    def disconnect(self):
        """MongoDB dan uzilish"""
        if self.client:
            self.client.close()
            print("🔌 MongoDB dan uzildi")
    
    # ==================== USERS ====================
    
    def add_user(self, user_name: str, metadata: Dict = None) -> bool:
        """Yangi foydalanuvchi qo'shish"""
        try:
            user_doc = {
                'name': user_name,
                'created_at': datetime.now(),
                'is_active': True,
                'total_entries': 0,
                'total_time_minutes': 0,
                'metadata': metadata or {}
            }
            
            # Check if user exists
            if self.users_collection.find_one({'name': user_name}):
                print(f"⚠️  Foydalanuvchi allaqachon mavjud: {user_name}")
                return False
            
            result = self.users_collection.insert_one(user_doc)
            print(f"✅ Foydalanuvchi qo'shildi: {user_name}")
            return bool(result.inserted_id)
        except Exception as e:
            print(f"❌ Foydalanuvchi qo'shishda xatolik: {e}")
            return False
    
    def get_user(self, user_name: str) -> Optional[Dict]:
        """Foydalanuvchi ma'lumotlarini olish"""
        try:
            return self.users_collection.find_one({'name': user_name})
        except Exception as e:
            print(f"❌ Foydalanuvchi olishda xatolik: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Barcha foydalanuvchilarni olish"""
        try:
            return list(self.users_collection.find({'is_active': True}))
        except Exception as e:
            print(f"❌ Foydalanuvchilarni olishda xatolik: {e}")
            return []
    
    def update_user_stats(self, user_name: str, total_entries: int = None, total_time_minutes: int = None) -> bool:
        """Foydalanuvchi statistikasini yangilash"""
        try:
            update_data = {'updated_at': datetime.now()}
            
            if total_entries is not None:
                update_data['total_entries'] = total_entries
            if total_time_minutes is not None:
                update_data['total_time_minutes'] = total_time_minutes
            
            result = self.users_collection.update_one(
                {'name': user_name},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Foydalanuvchi statistikasini yangilashda xatolik: {e}")
            return False
    
    # ==================== ENCODINGS ====================
    
    def save_encoding(self, user_name: str, encoding: np.ndarray, image_path: str, direction: str = None) -> bool:
        """Face encoding ni saqlash"""
        try:
            # Convert numpy array to base64 string
            encoding_bytes = pickle.dumps(encoding)
            encoding_b64 = base64.b64encode(encoding_bytes).decode('utf-8')
            
            encoding_doc = {
                'user_name': user_name,
                'encoding': encoding_b64,
                'image_path': image_path,
                'direction': direction,
                'created_at': datetime.now(),
                'is_active': True
            }
            
            result = self.encodings_collection.insert_one(encoding_doc)
            return bool(result.inserted_id)
        except Exception as e:
            print(f"❌ Encoding saqlashda xatolik: {e}")
            return False
    
    def get_user_encodings(self, user_name: str) -> List[np.ndarray]:
        """Foydalanuvchining barcha encodinglarini olish"""
        try:
            encodings = []
            cursor = self.encodings_collection.find({
                'user_name': user_name,
                'is_active': True
            })
            
            for doc in cursor:
                # Convert base64 back to numpy array
                encoding_bytes = base64.b64decode(doc['encoding'])
                encoding = pickle.loads(encoding_bytes)
                encodings.append(encoding)
            
            return encodings
        except Exception as e:
            print(f"❌ Encodinglarni olishda xatolik: {e}")
            return []
    
    def get_all_encodings(self) -> tuple[List[np.ndarray], List[str]]:
        """Barcha encodinglar va nomlarni olish"""
        try:
            encodings = []
            names = []
            
            cursor = self.encodings_collection.find({'is_active': True})
            
            for doc in cursor:
                # Convert base64 back to numpy array
                encoding_bytes = base64.b64decode(doc['encoding'])
                encoding = pickle.loads(encoding_bytes)
                
                encodings.append(encoding)
                names.append(doc['user_name'])
            
            print(f"📊 MongoDB dan {len(encodings)} ta encoding yuklandi")
            return encodings, names
        except Exception as e:
            print(f"❌ Barcha encodinglarni olishda xatolik: {e}")
            return [], []
    
    def delete_user_encodings(self, user_name: str) -> bool:
        """Foydalanuvchining barcha encodinglarini o'chirish"""
        try:
            result = self.encodings_collection.update_many(
                {'user_name': user_name},
                {'$set': {'is_active': False, 'deleted_at': datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Encodinglarni o'chirishda xatolik: {e}")
            return False
    
    # ==================== ATTENDANCE ====================
    
    def log_attendance(self, user_name: str, action: str, method: str, confidence: float = None) -> bool:
        """Davomat yozuvi qo'shish"""
        try:
            attendance_doc = {
                'user_name': user_name,
                'action': action,  # 'entry' or 'exit'
                'method': method,  # 'camera', 'manual', etc.
                'confidence': confidence,
                'timestamp': datetime.now(),
                'date': date.today().isoformat()
            }
            
            result = self.attendance_collection.insert_one(attendance_doc)
            return bool(result.inserted_id)
        except Exception as e:
            print(f"❌ Davomat yozishda xatolik: {e}")
            return False
    
    def get_daily_attendance(self, target_date: date = None) -> List[Dict]:
        """Kunlik davomat ma'lumotlari"""
        try:
            if target_date is None:
                target_date = date.today()
            
            date_str = target_date.isoformat()
            
            cursor = self.attendance_collection.find({
                'date': date_str
            }).sort('timestamp', 1)
            
            return list(cursor)
        except Exception as e:
            print(f"❌ Kunlik davomat olishda xatolik: {e}")
            return []
    
    def get_user_attendance_history(self, user_name: str, days: int = 30) -> List[Dict]:
        """Foydalanuvchi davomat tarixi"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            cursor = self.attendance_collection.find({
                'user_name': user_name,
                'timestamp': {'$gte': start_date}
            }).sort('timestamp', -1)
            
            return list(cursor)
        except Exception as e:
            print(f"❌ Davomat tarixini olishda xatolik: {e}")
            return []
    
    # ==================== LOGS ====================
    
    def log_system_event(self, level: str, message: str, metadata: Dict = None) -> bool:
        """Tizim log yozuvi"""
        try:
            log_doc = {
                'level': level,
                'message': message,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            }
            
            result = self.logs_collection.insert_one(log_doc)
            
            # Console ga ham chiqarish
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] {level}: {message}")
            
            return bool(result.inserted_id)
        except Exception as e:
            print(f"❌ Log yozishda xatolik: {e}")
            return False
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """So'nggi loglarni olish"""
        try:
            cursor = self.logs_collection.find().sort('timestamp', -1).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"❌ Loglarni olishda xatolik: {e}")
            return []
    
    # ==================== SYSTEM ====================
    
    def save_system_state(self, current_users: Dict) -> bool:
        """Tizim holatini saqlash"""
        try:
            # Convert datetime objects to ISO strings
            current_users_serializable = {}
            for user, entry_time in current_users.items():
                current_users_serializable[user] = entry_time.isoformat()
            
            system_doc = {
                'type': 'current_users',
                'data': current_users_serializable,
                'updated_at': datetime.now()
            }
            
            # Upsert - update if exists, insert if not
            result = self.system_collection.replace_one(
                {'type': 'current_users'},
                system_doc,
                upsert=True
            )
            
            return True
        except Exception as e:
            print(f"❌ Tizim holatini saqlashda xatolik: {e}")
            return False
    def save_system_metadata(self, metadata: Dict) -> bool:
        """Tizim metadata saqlash"""
        try:
            metadata_doc = {
                'type': 'system_metadata',
                'data': metadata,
                'updated_at': datetime.now()
            }

            # Upsert - update if exists, insert if not
            result = self.system_collection.replace_one(
                {'type': 'system_metadata'},
                metadata_doc,
                upsert=True
            )

            return True
        except Exception as e:
            print(f"❌ System metadata saqlashda xatolik: {e}")
            return False

    def load_system_metadata(self) -> Optional[Dict]:
        """Tizim metadata yuklash"""
        try:
            doc = self.system_collection.find_one({'type': 'system_metadata'})
            if doc and 'data' in doc:
                return doc['data']
            return None
        except Exception as e:
            print(f"❌ System metadata yuklashda xatolik: {e}")
            return None

    def save_recovery_checkpoint(self, checkpoint_data: Dict) -> bool:
        """Recovery checkpoint saqlash"""
        try:
            checkpoint_doc = {
                'type': 'recovery_checkpoint',
                'data': checkpoint_data,
                'created_at': datetime.now(),
                'checkpoint_id': f"checkpoint_{int(time.time())}"
            }

            # Insert new checkpoint
            result = self.system_collection.insert_one(checkpoint_doc)

            # Keep only last 10 checkpoints
            checkpoints = list(self.system_collection.find(
                {'type': 'recovery_checkpoint'}
            ).sort('created_at', -1))

            if len(checkpoints) > 10:
                for old_checkpoint in checkpoints[10:]:
                    self.system_collection.delete_one({'_id': old_checkpoint['_id']})

            return True
        except Exception as e:
            print(f"❌ Recovery checkpoint saqlashda xatolik: {e}")
            return False

    def get_latest_recovery_checkpoint(self) -> Optional[Dict]:
        """Eng oxirgi recovery checkpoint olish"""
        try:
            doc = self.system_collection.find_one(
                {'type': 'recovery_checkpoint'},
                sort=[('created_at', -1)]
            )
            if doc and 'data' in doc:
                return doc['data']
            return None
        except Exception as e:
            print(f"❌ Recovery checkpoint yuklashda xatolik: {e}")
            return None
    
    def load_system_state(self) -> Dict:
        """Tizim holatini yuklash"""
        try:
            doc = self.system_collection.find_one({'type': 'current_users'})
            
            if not doc:
                return {}
            
            # Convert ISO strings back to datetime objects
            current_users = {}
            for user, entry_time_str in doc['data'].items():
                current_users[user] = datetime.fromisoformat(entry_time_str)
            
            return current_users
        except Exception as e:
            print(f"❌ Tizim holatini yuklashda xatolik: {e}")
            return {}
    
    # ==================== MIGRATION ====================
    
    def migrate_from_json(self, json_data_manager) -> bool:
        """JSON fayllardan MongoDB ga ko'chirish"""
        try:
            print("🔄 JSON dan MongoDB ga migration boshlandi...")
            
            # Users migration
            for user_name, user_data in json_data_manager.users_data.items():
                if user_data.get('is_active', True):
                    self.add_user(user_name, {
                        'total_entries': user_data.get('total_entries', 0),
                        'total_time_minutes': user_data.get('total_time_minutes', 0)
                    })
            
            # Attendance migration
            for record in json_data_manager.attendance_data:
                self.log_attendance(
                    record['user_name'],
                    record['action'],
                    record.get('method', 'camera'),
                    record.get('confidence')
                )
            
            # Logs migration
            for log_entry in json_data_manager.logs_data:
                self.log_system_event(
                    log_entry['level'],
                    log_entry['message']
                )
            
            print("✅ Migration tugallandi!")
            return True
        except Exception as e:
            print(f"❌ Migration xatosi: {e}")
            return False
        def _setup_collections(self):
            """Setup MongoDB collections"""
            try:
                self.users_collection = self.db.users
                self.encodings_collection = self.db.encodings
                self.attendance_collection = self.db.attendance
                self.logs_collection = self.db.logs
                self.system_collection = self.db.system

                # Create indexes for better performance
                self._create_indexes()

            except Exception as e:
                self.error_handler.log_error(e, "MongoDB collections setup")

        def _create_indexes(self):
            """Create database indexes for performance"""
            try:
                # User collection indexes
                self.users_collection.create_index("name", unique=True)

                # Attendance collection indexes
                self.attendance_collection.create_index([("user_name", 1), ("timestamp", -1)])
                self.attendance_collection.create_index("timestamp")

                # Logs collection indexes
                self.logs_collection.create_index("timestamp")
                self.logs_collection.create_index("level")

                print("📊 MongoDB indexes created")

            except Exception as e:
                self.error_handler.log_error(e, "MongoDB index creation")

        @handle_errors("MongoDB Connection")
        def connect(self) -> bool:
            """Connect to MongoDB with retry logic"""
            with self.connection_lock:
                self.connection_stats['total_attempts'] += 1

                for attempt in range(self.max_retries):
                    try:
                        print(f"🔄 MongoDB connection attempt {attempt + 1}/{self.max_retries}")

                        # Create client with timeout settings
                        self.client = MongoClient(
                            self.mongo_uri,
                            serverSelectionTimeoutMS=self.connection_timeout * 1000,
                            connectTimeoutMS=self.connection_timeout * 1000,
                            socketTimeoutMS=self.connection_timeout * 1000,
                            maxPoolSize=10,
                            retryWrites=True
                        )

                        # Test connection
                        self.client.admin.command('ping')

                        # Get database
                        self.db = self.client[self.db_name]

                        # Test database access
                        self.db.list_collection_names()

                        # Success
                        self.is_connected = True
                        self.connection_stats['successful_connections'] += 1
                        self.connection_stats['last_connection_time'] = datetime.now().isoformat()
                        self.connection_stats['last_error'] = None

                        print("✅ MongoDB connected successfully")
                        return True

                    except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as e:
                        self.connection_stats['failed_connections'] += 1
                        self.connection_stats['last_error'] = str(e)

                        print(f"❌ MongoDB connection failed (attempt {attempt + 1}): {e}")

                        if attempt < self.max_retries - 1:
                            print(f"⏳ Retrying in {self.retry_delay} seconds...")
                            time.sleep(self.retry_delay)
                            self.retry_delay *= 1.5  # Exponential backoff

                    except Exception as e:
                        self.error_handler.log_error(e, f"MongoDB connection unexpected error (attempt {attempt + 1})")
                        break

                # All attempts failed
                self.is_connected = False
                print("❌ MongoDB connection failed after all attempts")
                return False

        def ensure_connection(self) -> bool:
            """Ensure MongoDB connection is active"""
            if not self.is_connected:
                return self.connect()

            try:
                # Test connection
                self.client.admin.command('ping')
                return True

            except Exception as e:
                self.error_handler.log_error(e, "MongoDB connection test")
                self.is_connected = False
                return self.connect()

        def execute_with_retry(self, operation_name: str, operation_func, *args, **kwargs):
            """Execute MongoDB operation with retry logic"""
            for attempt in range(self.max_retries):
                try:
                    if not self.ensure_connection():
                        raise ConnectionFailure("Could not establish MongoDB connection")

                    return operation_func(*args, **kwargs)

                except (ConnectionFailure, ServerSelectionTimeoutError, OperationFailure) as e:
                    self.error_handler.log_error(e, f"{operation_name} (attempt {attempt + 1})")

                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        raise

                except Exception as e:
                    self.error_handler.log_error(e, f"{operation_name} unexpected error")
                    raise

        def get_connection_stats(self) -> Dict[str, Any]:
            """Get connection statistics"""
            return self.connection_stats.copy()

        def print_connection_stats(self):
            """Print connection statistics"""
            stats = self.get_connection_stats()
            print(f"""
    🗄️  MongoDB Connection Statistics:
       Total Attempts: {stats['total_attempts']}
       Successful: {stats['successful_connections']}
       Failed: {stats['failed_connections']}
       Last Connection: {stats['last_connection_time']}
       Last Error: {stats['last_error']}
       Current Status: {'Connected' if self.is_connected else 'Disconnected'}
            """)
