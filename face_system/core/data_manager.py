"""
Ma'lumotlar boshqaruvi - JSON fayllar bilan ishlash
"""
import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
import shutil
from .utils import get_uzbek_day_name, format_duration, log_with_timestamp

class DataManager:
    def __init__(self):
        self.users_file = 'users.json'
        self.attendance_file = 'attendance.json'
        self.logs_file = 'logs.json'
        self.config_file = 'config.json'
        
        self.users_data = {}
        self.attendance_data = []
        self.logs_data = []
        self.config = {}
        
        self.load_all_data()
    
    def load_all_data(self):
        """Barcha ma'lumotlarni yuklash"""
        self.load_config()
        self.load_users_data()
        self.load_attendance_data()
        self.load_logs_data()
    
    def load_config(self):
        """Konfiguratsiyani yuklash"""
        default_config = {
            'web_port': 8080,
            'confidence_threshold': 0.6,
            'recognition_cooldown': 3,
            'camera_index': 0,
            'zones': {
                'entry_zone': {'x': 0, 'width': 0.3},
                'neutral_zone': {'x': 0.3, 'width': 0.4},
                'exit_zone': {'x': 0.7, 'width': 0.3}
            }
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Konfiguratsiyani saqlash"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def load_users_data(self):
        """Foydalanuvchilar ma'lumotini yuklash"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users_data = json.load(f)
        else:
            self.users_data = {}
            self.save_users_data()
    
    def save_users_data(self):
        """Foydalanuvchilar ma'lumotini saqlash"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users_data, f, indent=2, ensure_ascii=False)
    
    def load_attendance_data(self):
        """Davomat ma'lumotini yuklash"""
        if os.path.exists(self.attendance_file):
            with open(self.attendance_file, 'r', encoding='utf-8') as f:
                self.attendance_data = json.load(f)
        else:
            self.attendance_data = []
            self.save_attendance_data()
    
    def save_attendance_data(self):
        """Davomat ma'lumotini saqlash"""
        with open(self.attendance_file, 'w', encoding='utf-8') as f:
            json.dump(self.attendance_data, f, indent=2, ensure_ascii=False, default=str)
    
    def load_logs_data(self):
        """Log ma'lumotini yuklash"""
        if os.path.exists(self.logs_file):
            with open(self.logs_file, 'r', encoding='utf-8') as f:
                self.logs_data = json.load(f)
        else:
            self.logs_data = []
            self.save_logs_data()
    
    def save_logs_data(self):
        """Log ma'lumotini saqlash"""
        with open(self.logs_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs_data, f, indent=2, ensure_ascii=False, default=str)
    
    def log_system_event(self, level, message):
        """Tizim hodisalarini loglash"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        
        self.logs_data.append(log_entry)
        
        # Faqat oxirgi 1000 ta logni saqlash
        if len(self.logs_data) > 1000:
            self.logs_data = self.logs_data[-1000:]
        
        self.save_logs_data()
        log_with_timestamp(level, message)
    
    def add_user(self, user_name):
        """Foydalanuvchini qo'shish"""
        if user_name not in self.users_data:
            self.users_data[user_name] = {
                'name': user_name,
                'created_at': datetime.now().isoformat(),
                'is_active': True,
                'total_entries': 0,
                'total_time_minutes': 0
            }
            self.save_users_data()
    
    def log_attendance(self, user_name, action, zone, confidence):
        """Davomat yozuvini saqlash"""
        try:
            now = datetime.now()
            
            attendance_record = {
                'user_name': user_name,
                'action': action,
                'timestamp': now.isoformat(),
                'zone': zone,
                'confidence': round(confidence, 3),
                'date': now.date().isoformat()
            }
            
            self.attendance_data.append(attendance_record)
            self.save_attendance_data()
            
            # Foydalanuvchi statistikasini yangilash
            if user_name in self.users_data:
                if action == 'entry':
                    self.users_data[user_name]['total_entries'] += 1
                self.save_users_data()
            
            self.log_system_event('INFO', f"{user_name} - {action.upper()} ({zone} zonasida, confidence: {confidence:.2f})")
            
        except Exception as e:
            self.log_system_event('ERROR', f"Davomat yozuvini saqlashda xatolik: {e}")
    
    def get_today_last_action(self, user_name):
        """Bugungi oxirgi actionni olish"""
        today = date.today().isoformat()
        today_records = [record for record in self.attendance_data 
                        if record['date'] == today and record['user_name'] == user_name]
        
        if today_records:
            sorted_records = sorted(today_records, key=lambda x: x['timestamp'])
            return sorted_records[-1]['action']
        return None
    
    def should_ignore_action(self, user_name, new_action):
        """Actionni ignore qilish kerakmi?"""
        today_records = [record for record in self.attendance_data 
                        if record['date'] == date.today().isoformat() and record['user_name'] == user_name]
        
        if not today_records:
            return False
        
        last_record = sorted(today_records, key=lambda x: x['timestamp'])[-1]
        last_time = datetime.fromisoformat(last_record['timestamp'])
        current_time = datetime.now()
        
        time_diff = (current_time - last_time).total_seconds()
        
        if time_diff < 120:  # 2 daqiqa
            self.log_system_event('WARNING', f"{user_name} - {new_action} ignore qilindi ({time_diff:.0f} soniya)")
            return True
        
        return False
    
    def get_daily_summary(self, target_date=None):
        """Kunlik hisobot"""
        if target_date is None:
            target_date = date.today()
        
        target_date_str = target_date.isoformat()
        day_records = [record for record in self.attendance_data if record['date'] == target_date_str]
        
        users_summary = {}
        
        for record in day_records:
            user_name = record['user_name']
            if user_name not in users_summary:
                users_summary[user_name] = {
                    'entries': [],
                    'total_minutes': 0,
                    'sessions': []
                }
            
            users_summary[user_name]['entries'].append({
                'time': datetime.fromisoformat(record['timestamp']).strftime('%H:%M'),
                'action': record['action'],
                'zone': record['zone']
            })
        
        # Sessiyalarni hisoblash
        for user_name, data in users_summary.items():
            entries = data['entries']
            sessions = []
            current_session = None
            
            for entry in entries:
                if entry['action'] == 'entry':
                    current_session = {'start': entry['time'], 'end': None, 'duration': 0}
                elif entry['action'] == 'exit' and current_session:
                    current_session['end'] = entry['time']
                    
                    start_time = datetime.strptime(current_session['start'], '%H:%M')
                    end_time = datetime.strptime(current_session['end'], '%H:%M')
                    duration = end_time - start_time
                    current_session['duration'] = int(duration.total_seconds() / 60)
                    
                    sessions.append(current_session)
                    data['total_minutes'] += current_session['duration']
                    current_session = None
            
            # Hali ichkarida bo'lsa
            if current_session:
                current_session['end'] = 'Hali ichkarida'
                current_time = datetime.now()
                start_time = datetime.strptime(current_session['start'], '%H:%M').replace(
                    year=current_time.year, month=current_time.month, day=current_time.day
                )
                duration = current_time - start_time
                current_session['duration'] = int(duration.total_seconds() / 60)
                sessions.append(current_session)
                data['total_minutes'] += current_session['duration']
            
            data['sessions'] = sessions
        
        return {
            'date': target_date_str,
            'day_name': target_date.strftime('%A'),
            'day_name_uz': get_uzbek_day_name(target_date.strftime('%A')),
            'users': users_summary
        }
    
    def create_backup(self):
        """Backup yaratish"""
        try:
            backup_dir = f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            
            files_to_backup = [
                'users.json', 'attendance.json', 'logs.json', 
                'config.json', 'face_encodings.pkl'
            ]
            
            for file_name in files_to_backup:
                if os.path.exists(file_name):
                    shutil.copy2(file_name, backup_dir)
            
            if os.path.exists('face_data'):
                shutil.copytree('face_data', f"{backup_dir}/face_data")
            
            self.log_system_event('INFO', f"Backup yaratildi: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            self.log_system_event('ERROR', f"Backup yaratishda xatolik: {e}")
            return None