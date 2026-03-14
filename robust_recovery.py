#!/usr/bin/env python3
"""
🛡️ ROBUST RECOVERY SYSTEM - Face ID uchun
Script to'xtab qolsa ham ma'lumotlarni himoya qilish va tiklash
"""

import os
import sys
import time
import json
import psutil
import subprocess
import signal
from datetime import datetime, timedelta
from pathlib import Path

class RobustRecovery:
    def __init__(self):
        self.face_id_dir = Path(__file__).parent
        self.state_dir = self.face_id_dir / "state_backup"
        self.state_dir.mkdir(exist_ok=True)
        
        # Recovery fayllari
        self.recovery_log = self.state_dir / "robust_recovery.log"
        self.crash_report = self.state_dir / "crash_report.json"
        self.pid_file = self.face_id_dir / "face_id.pid"
        
        # State fayllari
        self.current_users_file = self.face_id_dir / "current_users.json"
        self.system_state_file = self.state_dir / "system_state.json"
        
    def log(self, message, level="INFO"):
        """Robust recovery log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.recovery_log, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass
        
        print(f"🛡️  {log_entry.strip()}")
    
    def detect_crash(self):
        """Crash holatini aniqlash"""
        crash_indicators = []
        
        # 1. PID file mavjud lekin process yo'q
        if self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                
                if not psutil.pid_exists(pid):
                    crash_indicators.append("PID file mavjud lekin process topilmadi")
                else:
                    # Process mavjud lekin Face ID emas
                    try:
                        proc = psutil.Process(pid)
                        if "python" not in proc.name().lower() or "main.py" not in " ".join(proc.cmdline()):
                            crash_indicators.append("PID file noto'g'ri process ga ishora qilmoqda")
                    except psutil.NoSuchProcess:
                        crash_indicators.append("Process PID orqali topilmadi")
            except Exception as e:
                crash_indicators.append(f"PID file o'qishda xatolik: {e}")
        
        # 2. System session file tekshirish
        session_file = self.face_id_dir / "system_session.json"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                
                if session_data.get("status") == "running":
                    # Session running deb ko'rsatilgan lekin process yo'q
                    session_pid = session_data.get("pid")
                    if session_pid and not psutil.pid_exists(session_pid):
                        crash_indicators.append("Session running lekin process topilmadi")
            except Exception as e:
                crash_indicators.append(f"Session file o'qishda xatolik: {e}")
        
        # 3. Stuck users tekshirish
        stuck_users = self.find_stuck_users()
        if stuck_users:
            crash_indicators.append(f"{len(stuck_users)} ta user 12+ soat ichkarida")
        
        # 4. Log fayllardagi xatoliklar
        recent_errors = self.check_recent_errors()
        if recent_errors:
            crash_indicators.append(f"{len(recent_errors)} ta yaqinda xatolik")
        
        return crash_indicators
    
    def find_stuck_users(self):
        """12+ soat ichkarida qolgan userlar"""
        stuck_users = []
        
        try:
            if self.current_users_file.exists():
                with open(self.current_users_file, "r", encoding="utf-8") as f:
                    current_users = json.load(f)
                
                now = datetime.now()
                for user, entry_time_str in current_users.items():
                    entry_time = datetime.fromisoformat(entry_time_str)
                    duration = now - entry_time
                    
                    if duration > timedelta(hours=12):
                        stuck_users.append({
                            'user': user,
                            'entry_time': entry_time_str,
                            'duration_hours': duration.total_seconds() / 3600
                        })
        except Exception as e:
            self.log(f"Stuck users tekshirishda xatolik: {e}", "ERROR")
        
        return stuck_users
    
    def check_recent_errors(self):
        """Yaqinda bo'lgan xatoliklar"""
        errors = []
        
        try:
            logs_file = self.face_id_dir / "logs.json"
            if logs_file.exists():
                with open(logs_file, "r", encoding="utf-8") as f:
                    logs_data = json.load(f)
                
                # Oxirgi 1 soat ichidagi ERROR loglar
                one_hour_ago = datetime.now() - timedelta(hours=1)
                
                for log_entry in logs_data[-50:]:  # Oxirgi 50 ta log
                    if log_entry.get('level') == 'ERROR':
                        log_time = datetime.fromisoformat(log_entry['timestamp'])
                        if log_time > one_hour_ago:
                            errors.append(log_entry)
        except Exception as e:
            self.log(f"Error logs tekshirishda xatolik: {e}", "ERROR")
        
        return errors
    
    def create_crash_report(self, crash_indicators):
        """Crash hisoboti yaratish"""
        try:
            crash_data = {
                'timestamp': datetime.now().isoformat(),
                'crash_indicators': crash_indicators,
                'system_info': {
                    'python_version': sys.version,
                    'platform': sys.platform,
                    'memory_usage': psutil.virtual_memory()._asdict(),
                    'disk_usage': psutil.disk_usage('.')._asdict()
                },
                'stuck_users': self.find_stuck_users(),
                'recent_errors': self.check_recent_errors()
            }
            
            with open(self.crash_report, "w", encoding="utf-8") as f:
                json.dump(crash_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.log(f"Crash report yaratildi: {len(crash_indicators)} ta indicator")
            return crash_data
            
        except Exception as e:
            self.log(f"Crash report yaratishda xatolik: {e}", "ERROR")
            return None
    
    def backup_current_state(self):
        """Joriy holatni backup qilish"""
        try:
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.state_dir / f"crash_backup_{backup_timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            # Muhim fayllarni backup qilish
            files_to_backup = [
                "current_users.json",
                "users.json", 
                "attendance.json",
                "logs.json",
                "config.json",
                "system_session.json"
            ]
            
            backed_up_files = []
            for file_name in files_to_backup:
                source_file = self.face_id_dir / file_name
                if source_file.exists():
                    backup_file = backup_dir / file_name
                    backup_file.write_bytes(source_file.read_bytes())
                    backed_up_files.append(file_name)
            
            # State backup ham qilish
            if self.system_state_file.exists():
                backup_state = backup_dir / "system_state.json"
                backup_state.write_bytes(self.system_state_file.read_bytes())
                backed_up_files.append("system_state.json")
            
            self.log(f"State backup yaratildi: {len(backed_up_files)} ta fayl")
            return backup_dir
            
        except Exception as e:
            self.log(f"State backup yaratishda xatolik: {e}", "ERROR")
            return None
    
    def force_cleanup(self):
        """Majburiy tozalash"""
        cleaned_items = []
        
        try:
            # 1. Zombie processlarni o'chirish
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['name'] and 'python' in proc.info['name'].lower() and
                        proc.info['cmdline'] and any('main.py' in cmd for cmd in proc.info['cmdline'])):
                        
                        proc.terminate()
                        cleaned_items.append(f"Process PID {proc.info['pid']}")
                        
                        # 5 soniya kutish
                        try:
                            proc.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            proc.kill()  # Force kill
                            cleaned_items.append(f"Force killed PID {proc.info['pid']}")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 2. PID file tozalash
            if self.pid_file.exists():
                self.pid_file.unlink()
                cleaned_items.append("PID file")
            
            # 3. Lock fayllarni tozalash
            lock_files = list(self.face_id_dir.glob("*.lock"))
            for lock_file in lock_files:
                lock_file.unlink()
                cleaned_items.append(f"Lock file: {lock_file.name}")
            
            # 4. Temporary fayllarni tozalash
            temp_files = list(self.face_id_dir.glob("*.tmp"))
            for temp_file in temp_files:
                temp_file.unlink()
                cleaned_items.append(f"Temp file: {temp_file.name}")
            
            self.log(f"Force cleanup: {len(cleaned_items)} ta element tozalandi")
            return cleaned_items
            
        except Exception as e:
            self.log(f"Force cleanup xatolik: {e}", "ERROR")
            return cleaned_items
    
    def reset_stuck_users(self):
        """Stuck userlarni reset qilish"""
        try:
            stuck_users = self.find_stuck_users()
            
            if stuck_users:
                self.log(f"🔄 {len(stuck_users)} ta stuck user reset qilinmoqda")
                
                # Current users faylini tozalash
                empty_users = {}
                with open(self.current_users_file, "w", encoding="utf-8") as f:
                    json.dump(empty_users, f, indent=2)
                
                # Attendance ga exit yozuvlarini qo'shish
                self.add_emergency_exits(stuck_users)
                
                self.log("✅ Stuck userlar reset qilindi")
                return len(stuck_users)
            
            return 0
            
        except Exception as e:
            self.log(f"Stuck users reset xatolik: {e}", "ERROR")
            return 0
    
    def add_emergency_exits(self, stuck_users):
        """Emergency exit yozuvlarini qo'shish"""
        try:
            attendance_file = self.face_id_dir / "attendance.json"
            
            # Attendance ma'lumotini yuklash
            attendance_data = []
            if attendance_file.exists():
                with open(attendance_file, "r", encoding="utf-8") as f:
                    attendance_data = json.load(f)
            
            # Emergency exit yozuvlari qo'shish
            now = datetime.now()
            for user_info in stuck_users:
                exit_record = {
                    'user_name': user_info['user'],
                    'action': 'exit',
                    'timestamp': now.isoformat(),
                    'zone': 'emergency_reset',
                    'confidence': 1.0,
                    'date': now.date().isoformat(),
                    'emergency_exit': True,
                    'reason': f"Stuck for {user_info['duration_hours']:.1f} hours"
                }
                attendance_data.append(exit_record)
            
            # Saqlash
            with open(attendance_file, "w", encoding="utf-8") as f:
                json.dump(attendance_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.log(f"Emergency exit yozuvlari qo'shildi: {len(stuck_users)} ta user")
            
        except Exception as e:
            self.log(f"Emergency exits qo'shishda xatolik: {e}", "ERROR")
    
    def start_face_id(self):
        """Face ID ni ishga tushirish"""
        try:
            self.log("🚀 Face ID ishga tushirilmoqda...")
            
            # Virtual environment
            venv_python = self.face_id_dir / "venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = "python3"
            
            # Environment variables
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.face_id_dir)
            
            # Face ID ishga tushirish
            process = subprocess.Popen(
                [str(venv_python), "main.py"],
                cwd=str(self.face_id_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # PID saqlash
            with open(self.pid_file, "w") as f:
                f.write(str(process.pid))
            
            # 10 soniya kutib, process hali ham ishlayotganini tekshirish
            time.sleep(10)
            
            if process.poll() is None:  # Process hali ham ishlayapti
                self.log(f"✅ Face ID muvaffaqiyatli ishga tushdi (PID: {process.pid})")
                return True
            else:
                # Process to'xtab qolgan
                stdout, stderr = process.communicate()
                self.log(f"❌ Face ID ishga tushmadi. Exit code: {process.returncode}", "ERROR")
                if stderr:
                    self.log(f"STDERR: {stderr.decode()}", "ERROR")
                return False
            
        except Exception as e:
            self.log(f"Face ID ishga tushirishda xatolik: {e}", "ERROR")
            return False
    
    def robust_recovery(self):
        """Asosiy robust recovery jarayoni"""
        self.log("🛡️  ROBUST RECOVERY BOSHLANDI", "INFO")
        
        # 1. Crash detection
        crash_indicators = self.detect_crash()
        
        if not crash_indicators:
            self.log("✅ Hech qanday crash belgisi topilmadi")
            return True
        
        self.log(f"🚨 CRASH ANIQLANDI: {len(crash_indicators)} ta indicator")
        for indicator in crash_indicators:
            self.log(f"   - {indicator}", "WARNING")
        
        # 2. Crash report yaratish
        crash_report = self.create_crash_report(crash_indicators)
        
        # 3. Current state backup
        backup_dir = self.backup_current_state()
        
        # 4. Stuck users reset
        reset_count = self.reset_stuck_users()
        
        # 5. Force cleanup
        cleaned_items = self.force_cleanup()
        
        # 6. Face ID ni qayta ishga tushirish
        if self.start_face_id():
            self.log("🎉 ROBUST RECOVERY MUVAFFAQIYATLI TUGALLANDI")
            self.log(f"📊 Statistika:")
            self.log(f"   - Reset qilingan userlar: {reset_count}")
            self.log(f"   - Tozalangan elementlar: {len(cleaned_items)}")
            self.log(f"   - Backup: {backup_dir.name if backup_dir else 'Yaratilmadi'}")
            return True
        else:
            self.log("❌ ROBUST RECOVERY MUVAFFAQIYATSIZ", "ERROR")
            return False

def main():
    """Asosiy funksiya"""
    recovery = RobustRecovery()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            indicators = recovery.detect_crash()
            if indicators:
                print(f"🚨 CRASH ANIQLANDI: {len(indicators)} ta indicator")
                for indicator in indicators:
                    print(f"   - {indicator}")
                sys.exit(1)
            else:
                print("✅ Hech qanday crash belgisi yo'q")
                sys.exit(0)
                
        elif command == "recover":
            success = recovery.robust_recovery()
            sys.exit(0 if success else 1)
            
        elif command == "cleanup":
            cleaned = recovery.force_cleanup()
            print(f"🧹 {len(cleaned)} ta element tozalandi")
            
        elif command == "reset-users":
            count = recovery.reset_stuck_users()
            print(f"🔄 {count} ta stuck user reset qilindi")
            
        elif command == "backup":
            backup_dir = recovery.backup_current_state()
            print(f"💾 Backup yaratildi: {backup_dir}")
            
        else:
            print("Usage: python robust_recovery.py [check|recover|cleanup|reset-users|backup]")
    else:
        # Default: full recovery
        recovery.robust_recovery()

if __name__ == "__main__":
    main()