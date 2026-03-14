"""
🔄 PERSISTENT STATE MANAGER - Robust holatni saqlash va tiklash
Script to'xtab qolsa ham ma'lumotlarni himoya qilish
"""

import json
import os
import time
import threading
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import shutil

class PersistentStateManager:
    """Tizim holatini doimiy saqlash va tiklash"""
    
    def __init__(self, face_system):
        self.face_system = face_system
        self.state_dir = Path("state_backup")
        self.state_dir.mkdir(exist_ok=True)
        
        # State fayllari
        self.current_users_file = "current_users.json"
        self.system_state_file = self.state_dir / "system_state.json"
        self.session_state_file = self.state_dir / "session_state.pkl"
        self.recovery_log_file = self.state_dir / "recovery.log"
        
        # Auto-save settings
        self.auto_save_interval = 30  # 30 soniya
        self.is_auto_saving = False
        self.auto_save_thread = None
        
        # State versioning
        self.state_version = 1
        self.last_save_hash = None
        
        print("🔄 PersistentStateManager initialized")
    
    def start_auto_save(self):
        """Avtomatik saqlashni boshlash"""
        if self.is_auto_saving:
            return
        
        self.is_auto_saving = True
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self.auto_save_thread.start()
        
        self.log("🔄 Auto-save boshlandi (har 30 soniyada)")
    
    def stop_auto_save(self):
        """Avtomatik saqlashni to'xtatish"""
        self.is_auto_saving = False
        if self.auto_save_thread:
            self.auto_save_thread.join(timeout=5)
        
        self.log("🔄 Auto-save to'xtatildi")
    
    def _auto_save_loop(self):
        """Avtomatik saqlash loop"""
        while self.is_auto_saving:
            try:
                self.save_complete_state()
                time.sleep(self.auto_save_interval)
            except Exception as e:
                self.log(f"❌ Auto-save error: {e}")
                time.sleep(5)  # Error bo'lsa kamroq kutish
    
    def log(self, message):
        """Recovery log yozish"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.recovery_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass  # Log yozishda xatolik bo'lsa ham davom etish
        
        print(log_entry.strip())
    
    def get_state_hash(self, state_data):
        """State ma'lumotlarining hash qiymatini olish"""
        state_str = json.dumps(state_data, sort_keys=True, default=str)
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def save_complete_state(self):
        """To'liq tizim holatini saqlash"""
        try:
            # Current state to'plash
            current_state = {
                'version': self.state_version,
                'timestamp': datetime.now().isoformat(),
                'current_users': {},
                'system_info': {
                    'total_users': len(self.face_system.known_face_names),
                    'total_encodings': len(self.face_system.known_face_encodings),
                    'uptime_seconds': time.time() - getattr(self.face_system, 'start_time', time.time()),
                    'config': self.face_system.data_manager.config.copy()
                },
                'session_stats': {
                    'total_recognitions': getattr(self.face_system, 'total_recognitions', 0),
                    'successful_recognitions': getattr(self.face_system, 'successful_recognitions', 0),
                    'failed_recognitions': getattr(self.face_system, 'failed_recognitions', 0)
                }
            }
            
            # Current users ma'lumoti
            for user_name, entry_time in self.face_system.current_users.items():
                current_state['current_users'][user_name] = {
                    'entry_time': entry_time.isoformat(),
                    'duration_minutes': (datetime.now() - entry_time).total_seconds() / 60,
                    'expected_action': self.face_system.get_next_expected_action(user_name)
                }
            
            # State hash tekshirish
            state_hash = self.get_state_hash(current_state)
            if state_hash == self.last_save_hash:
                return  # O'zgarish yo'q, saqlash shart emas
            
            # 1. JSON formatda saqlash (human-readable)
            self._save_json_state(current_state)
            
            # 2. Pickle formatda saqlash (binary, tezroq)
            self._save_pickle_state(current_state)
            
            # 3. MongoDB ga saqlash
            self._save_mongodb_state(current_state)
            
            # 4. Multiple backup copies
            self._create_backup_copies(current_state)
            
            self.last_save_hash = state_hash
            
        except Exception as e:
            self.log(f"❌ Complete state save error: {e}")
    
    def _save_json_state(self, state_data):
        """JSON formatda saqlash"""
        try:
            # Temporary file orqali atomic write
            temp_file = self.system_state_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Atomic rename
            temp_file.replace(self.system_state_file)
            
            # Legacy current_users.json ham yangilash
            current_users_data = {}
            for user_name, user_info in state_data['current_users'].items():
                current_users_data[user_name] = user_info['entry_time']
            
            with open(self.current_users_file, 'w', encoding='utf-8') as f:
                json.dump(current_users_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.log(f"❌ JSON state save error: {e}")
    
    def _save_pickle_state(self, state_data):
        """Pickle formatda saqlash (tezroq)"""
        try:
            temp_file = self.session_state_file.with_suffix('.tmp')
            
            with open(temp_file, 'wb') as f:
                pickle.dump(state_data, f)
            
            temp_file.replace(self.session_state_file)
            
        except Exception as e:
            self.log(f"❌ Pickle state save error: {e}")
    
    def _save_mongodb_state(self, state_data):
        """MongoDB ga saqlash"""
        try:
            if self.face_system.use_mongodb and self.face_system.mongodb_manager:
                # Current users MongoDB ga saqlash
                current_users_for_mongo = {}
                for user_name, user_info in state_data['current_users'].items():
                    current_users_for_mongo[user_name] = datetime.fromisoformat(user_info['entry_time'])
                
                self.face_system.mongodb_manager.save_system_state(current_users_for_mongo)
                
                # System state ham saqlash
                self.face_system.mongodb_manager.save_system_metadata({
                    'last_update': datetime.now(),
                    'version': state_data['version'],
                    'system_info': state_data['system_info'],
                    'session_stats': state_data['session_stats']
                })
                
        except Exception as e:
            self.log(f"❌ MongoDB state save error: {e}")
    
    def _create_backup_copies(self, state_data):
        """Multiple backup nusxalari yaratish"""
        try:
            # Timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.state_dir / f"backup_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Faqat oxirgi 10 ta backup saqlash
            self._cleanup_old_backups()
            
        except Exception as e:
            self.log(f"❌ Backup creation error: {e}")
    
    def _cleanup_old_backups(self):
        """Eski backuplarni tozalash"""
        try:
            backup_files = list(self.state_dir.glob("backup_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Faqat oxirgi 10 ta saqlash
            for old_backup in backup_files[10:]:
                old_backup.unlink()
            
        except Exception as e:
            self.log(f"❌ Backup cleanup error: {e}")
    
    def load_complete_state(self):
        """To'liq tizim holatini yuklash"""
        self.log("🔄 Complete state recovery boshlandi")
        
        # 1. Eng yaxshi source ni topish
        recovery_source = self._find_best_recovery_source()
        
        if not recovery_source:
            self.log("❌ Hech qanday recovery source topilmadi")
            return False
        
        self.log(f"📂 Recovery source: {recovery_source['type']}")
        
        # 2. State ni yuklash
        try:
            state_data = recovery_source['data']
            
            # Current users tiklash
            recovered_users = {}
            for user_name, user_info in state_data.get('current_users', {}).items():
                if isinstance(user_info, dict):
                    entry_time = datetime.fromisoformat(user_info['entry_time'])
                else:
                    # Legacy format
                    entry_time = datetime.fromisoformat(user_info)
                
                # Faqat 24 soat ichidagi sessiyalarni tiklash
                if datetime.now() - entry_time < timedelta(hours=24):
                    recovered_users[user_name] = entry_time
                    self.log(f"👤 {user_name} tiklandi (ichkarida: {entry_time.strftime('%H:%M')})")
            
            # Face system ga yuklash
            self.face_system.current_users = recovered_users
            
            # System stats tiklash
            if 'session_stats' in state_data:
                stats = state_data['session_stats']
                self.face_system.total_recognitions = stats.get('total_recognitions', 0)
                self.face_system.successful_recognitions = stats.get('successful_recognitions', 0)
                self.face_system.failed_recognitions = stats.get('failed_recognitions', 0)
            
            self.log(f"✅ Recovery tugallandi: {len(recovered_users)} ta user tiklandi")
            return True
            
        except Exception as e:
            self.log(f"❌ State loading error: {e}")
            return False
    
    def _find_best_recovery_source(self):
        """Eng yaxshi recovery source ni topish"""
        sources = []
        
        # 1. MongoDB dan yuklash
        try:
            if self.face_system.use_mongodb and self.face_system.mongodb_manager:
                mongodb_users = self.face_system.mongodb_manager.load_system_state()
                if mongodb_users:
                    sources.append({
                        'type': 'MongoDB',
                        'priority': 1,
                        'timestamp': datetime.now(),
                        'data': {'current_users': {name: time.isoformat() for name, time in mongodb_users.items()}}
                    })
        except Exception as e:
            self.log(f"⚠️  MongoDB recovery error: {e}")
        
        # 2. JSON state file
        try:
            if self.system_state_file.exists():
                with open(self.system_state_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                sources.append({
                    'type': 'JSON State',
                    'priority': 2,
                    'timestamp': datetime.fromisoformat(json_data.get('timestamp', datetime.now().isoformat())),
                    'data': json_data
                })
        except Exception as e:
            self.log(f"⚠️  JSON state recovery error: {e}")
        
        # 3. Pickle state file
        try:
            if self.session_state_file.exists():
                with open(self.session_state_file, 'rb') as f:
                    pickle_data = pickle.load(f)
                
                sources.append({
                    'type': 'Pickle State',
                    'priority': 3,
                    'timestamp': datetime.fromisoformat(pickle_data.get('timestamp', datetime.now().isoformat())),
                    'data': pickle_data
                })
        except Exception as e:
            self.log(f"⚠️  Pickle state recovery error: {e}")
        
        # 4. Legacy current_users.json
        try:
            if os.path.exists(self.current_users_file):
                with open(self.current_users_file, 'r', encoding='utf-8') as f:
                    legacy_data = json.load(f)
                
                sources.append({
                    'type': 'Legacy JSON',
                    'priority': 4,
                    'timestamp': datetime.fromtimestamp(os.path.getmtime(self.current_users_file)),
                    'data': {'current_users': legacy_data}
                })
        except Exception as e:
            self.log(f"⚠️  Legacy JSON recovery error: {e}")
        
        # 5. Backup files
        try:
            backup_files = list(self.state_dir.glob("backup_*.json"))
            if backup_files:
                # Eng yangi backup
                latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
                
                with open(latest_backup, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                sources.append({
                    'type': f'Backup ({latest_backup.name})',
                    'priority': 5,
                    'timestamp': datetime.fromisoformat(backup_data.get('timestamp', datetime.now().isoformat())),
                    'data': backup_data
                })
        except Exception as e:
            self.log(f"⚠️  Backup recovery error: {e}")
        
        # Eng yaxshisini tanlash (priority va timestamp bo'yicha)
        if not sources:
            return None
        
        # Priority bo'yicha saralash, keyin timestamp bo'yicha
        sources.sort(key=lambda x: (x['priority'], -x['timestamp'].timestamp()))
        
        best_source = sources[0]
        self.log(f"📊 {len(sources)} ta recovery source topildi, eng yaxshisi: {best_source['type']}")
        
        return best_source
    
    def force_save_state(self):
        """Majburiy holatni saqlash (shutdown paytida)"""
        self.log("💾 Force save state...")
        
        try:
            # Auto-save to'xtatish
            self.stop_auto_save()
            
            # Oxirgi marta saqlash
            self.save_complete_state()
            
            # Emergency backup
            emergency_backup = self.state_dir / f"emergency_backup_{int(time.time())}.json"
            
            emergency_data = {
                'timestamp': datetime.now().isoformat(),
                'current_users': {},
                'emergency_save': True
            }
            
            for user_name, entry_time in self.face_system.current_users.items():
                emergency_data['current_users'][user_name] = entry_time.isoformat()
            
            with open(emergency_backup, 'w', encoding='utf-8') as f:
                json.dump(emergency_data, f, indent=2, ensure_ascii=False)
            
            self.log(f"💾 Emergency backup yaratildi: {emergency_backup}")
            
        except Exception as e:
            self.log(f"❌ Force save error: {e}")
    
    def get_recovery_report(self):
        """Recovery hisoboti"""
        report = {
            'available_sources': [],
            'current_state': {
                'users_count': len(self.face_system.current_users),
                'users': list(self.face_system.current_users.keys())
            }
        }
        
        # Available sources
        sources = [
            ('MongoDB', lambda: self.face_system.mongodb_manager.load_system_state() if self.face_system.use_mongodb else None),
            ('JSON State', lambda: self.system_state_file.exists()),
            ('Pickle State', lambda: self.session_state_file.exists()),
            ('Legacy JSON', lambda: os.path.exists(self.current_users_file)),
            ('Backups', lambda: len(list(self.state_dir.glob("backup_*.json"))))
        ]
        
        for source_name, check_func in sources:
            try:
                result = check_func()
                report['available_sources'].append({
                    'name': source_name,
                    'available': bool(result),
                    'details': str(result) if result else None
                })
            except Exception as e:
                report['available_sources'].append({
                    'name': source_name,
                    'available': False,
                    'error': str(e)
                })
        
        return report

# Global instance
_persistent_state_manager = None

def get_persistent_state_manager(face_system):
    """Global persistent state manager instance"""
    global _persistent_state_manager
    if _persistent_state_manager is None:
        _persistent_state_manager = PersistentStateManager(face_system)
    return _persistent_state_manager