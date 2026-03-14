#!/usr/bin/env python3
"""
🔄 AUTO RECOVERY SYSTEM - Face ID uchun
Script to'xtab qolsa avtomatik tiklash
"""

import os
import sys
import time
import json
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

class FaceIDRecovery:
    def __init__(self):
        self.face_id_dir = Path(__file__).parent
        self.pid_file = self.face_id_dir / "face_id.pid"
        self.log_file = self.face_id_dir / "recovery.log"
        self.current_users_file = self.face_id_dir / "current_users.json"
        
    def log(self, message):
        """Recovery log yozish"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        print(log_entry.strip())
    
    def is_face_id_running(self):
        """Face ID ishlab turganini tekshirish"""
        try:
            # PID file orqali tekshirish
            if self.pid_file.exists():
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    if "python" in process.name().lower() and "main.py" in " ".join(process.cmdline()):
                        return True
            
            # Process name orqali tekshirish
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if (proc.info['name'] and 'python' in proc.info['name'].lower() and
                        proc.info['cmdline'] and any('main.py' in cmd for cmd in proc.info['cmdline'])):
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
            
        except Exception as e:
            self.log(f"❌ Process tekshirishda xatolik: {e}")
            return False
    
    def check_stuck_users(self):
        """Ichkaridagi userlarni tekshirish"""
        try:
            if not self.current_users_file.exists():
                return []
            
            with open(self.current_users_file, "r", encoding="utf-8") as f:
                current_users = json.load(f)
            
            if not current_users:
                return []
            
            # 12 soatdan ortiq ichkarida bo'lgan userlar
            stuck_users = []
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
            
            return stuck_users
            
        except Exception as e:
            self.log(f"❌ Stuck users tekshirishda xatolik: {e}")
            return []
    
    def reset_stuck_users(self):
        """Stuck userlarni reset qilish"""
        try:
            stuck_users = self.check_stuck_users()
            
            if stuck_users:
                self.log(f"🔄 {len(stuck_users)} ta stuck user topildi:")
                for user_info in stuck_users:
                    self.log(f"   - {user_info['user']}: {user_info['duration_hours']:.1f} soat")
                
                # Current users faylini tozalash
                with open(self.current_users_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                
                self.log("✅ Stuck userlar tozalandi")
                return len(stuck_users)
            
            return 0
            
        except Exception as e:
            self.log(f"❌ Stuck users reset qilishda xatolik: {e}")
            return 0
    
    def start_face_id(self):
        """Face ID ni ishga tushirish"""
        try:
            self.log("🚀 Face ID ishga tushirilmoqda...")
            
            # Virtual environment aktivlashtirish
            venv_python = self.face_id_dir / "venv" / "bin" / "python"
            if not venv_python.exists():
                venv_python = "python3"  # System python
            
            # Face ID ishga tushirish
            process = subprocess.Popen(
                [str(venv_python), "main.py"],
                cwd=str(self.face_id_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # PID saqlash
            with open(self.pid_file, "w") as f:
                f.write(str(process.pid))
            
            self.log(f"✅ Face ID ishga tushdi (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.log(f"❌ Face ID ishga tushirishda xatolik: {e}")
            return False
    
    def cleanup_old_processes(self):
        """Eski processlarni tozalash"""
        try:
            killed_count = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    if (proc.info['name'] and 'python' in proc.info['name'].lower() and
                        proc.info['cmdline'] and any('main.py' in cmd for cmd in proc.info['cmdline'])):
                        
                        # 1 soatdan ortiq ishlab turgan processlar
                        create_time = datetime.fromtimestamp(proc.info['create_time'])
                        if datetime.now() - create_time > timedelta(hours=1):
                            proc.terminate()
                            killed_count += 1
                            self.log(f"🔪 Eski process o'chirildi: PID {proc.info['pid']}")
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                time.sleep(5)  # Processlar to'xtashini kutish
            
            return killed_count
            
        except Exception as e:
            self.log(f"❌ Process tozalashda xatolik: {e}")
            return 0
    
    def recovery_check(self):
        """Asosiy recovery tekshiruvi"""
        self.log("🔍 Recovery tekshiruvi boshlandi")
        
        # 1. Face ID ishlab turganini tekshirish
        if self.is_face_id_running():
            self.log("✅ Face ID ishlab turibdi")
            
            # Stuck userlarni tekshirish
            stuck_count = len(self.check_stuck_users())
            if stuck_count > 0:
                self.log(f"⚠️  {stuck_count} ta stuck user topildi")
                reset_count = self.reset_stuck_users()
                if reset_count > 0:
                    self.log(f"🔄 {reset_count} ta user reset qilindi")
            
            return True
        
        # 2. Face ID ishlamayapti - recovery
        self.log("❌ Face ID ishlamayapti, recovery boshlandi")
        
        # 3. Eski processlarni tozalash
        killed_count = self.cleanup_old_processes()
        if killed_count > 0:
            self.log(f"🧹 {killed_count} ta eski process tozalandi")
        
        # 4. Stuck userlarni reset qilish
        reset_count = self.reset_stuck_users()
        if reset_count > 0:
            self.log(f"🔄 {reset_count} ta stuck user reset qilindi")
        
        # 5. Face ID ni qayta ishga tushirish
        if self.start_face_id():
            self.log("✅ Recovery muvaffaqiyatli tugallandi")
            return True
        else:
            self.log("❌ Recovery muvaffaqiyatsiz tugadi")
            return False

def main():
    """Asosiy funksiya"""
    recovery = FaceIDRecovery()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "check":
            recovery.recovery_check()
        elif command == "start":
            recovery.start_face_id()
        elif command == "reset-users":
            count = recovery.reset_stuck_users()
            print(f"Reset qilindi: {count} ta user")
        elif command == "status":
            if recovery.is_face_id_running():
                print("✅ Face ID ishlab turibdi")
            else:
                print("❌ Face ID ishlamayapti")
        else:
            print("Usage: python auto_recovery.py [check|start|reset-users|status]")
    else:
        # Default: recovery check
        recovery.recovery_check()

if __name__ == "__main__":
    main()