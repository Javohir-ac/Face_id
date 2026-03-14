"""
Scheduler - Avtomatik kun oxiri reset va boshqa vazifalar
"""
import schedule
import time
import threading
from datetime import datetime, time as dt_time
from typing import Callable, Optional

class SystemScheduler:
    """Tizim vazifalarini rejalashtirish"""
    
    def __init__(self, face_system):
        self.face_system = face_system
        self.is_running = False
        self.scheduler_thread = None
        
        print("⏰ SystemScheduler initialized")
    
    def setup_daily_tasks(self, end_of_day_time: str = "23:59"):
        """Kunlik vazifalarni sozlash"""
        try:
            # Kun oxiri reset
            schedule.every().day.at(end_of_day_time).do(self.end_of_day_reset)
            
            # Haftalik cache tozalash (yakshanba kuni)
            schedule.every().sunday.at("02:00").do(self.weekly_cleanup)
            
            # Kunlik performance log saqlash
            schedule.every().day.at("23:58").do(self.daily_performance_log)
            
            print(f"📅 Kunlik vazifalar sozlandi:")
            print(f"   🕚 End-of-day reset: {end_of_day_time}")
            print(f"   🧹 Weekly cleanup: Yakshanba 02:00")
            print(f"   📊 Performance log: Har kuni 23:58")
            
        except Exception as e:
            print(f"❌ Scheduler setup error: {e}")
    
    def end_of_day_reset(self):
        """Kun oxiri barcha userlarni chiqarish"""
        try:
            print("\n" + "="*50)
            print("🌙 END-OF-DAY RESET BOSHLANDI")
            print("="*50)
            
            # Barcha userlarni chiqarish
            exit_count = self.face_system.reset_all_users("end_of_day")
            
            # Performance hisoboti saqlash
            self.face_system.performance_monitor.save_performance_log(
                f"performance_log_{datetime.now().strftime('%Y%m%d')}.json"
            )
            
            # Memory optimization
            freed_memory = self.face_system.memory_optimizer.optimize_system_memory()
            
            print(f"✅ End-of-day reset tugallandi:")
            print(f"   👥 {exit_count} ta user chiqarildi")
            print(f"   🧠 {freed_memory:.1f} MB xotira tozalandi")
            print(f"   📊 Performance log saqlandi")
            print("="*50)
            
            # Log yozish
            self.face_system.data_manager.log_system_event(
                'INFO', 
                f"End-of-day reset: {exit_count} users, {freed_memory:.1f}MB freed"
            )
            
        except Exception as e:
            print(f"❌ End-of-day reset error: {e}")
            self.face_system.data_manager.log_system_event('ERROR', f"End-of-day reset error: {e}")
    
    def weekly_cleanup(self):
        """Haftalik tozalash"""
        try:
            print("\n🧹 HAFTALIK TOZALASH BOSHLANDI")
            
            # Cache tozalash
            self.face_system.cache_manager.clear()
            
            # Memory optimization
            freed_memory = self.face_system.memory_optimizer.optimize_system_memory()
            
            # Performance statistics
            self.face_system.performance_monitor.print_performance_report()
            
            print(f"✅ Haftalik tozalash tugallandi: {freed_memory:.1f}MB tozalandi")
            
        except Exception as e:
            print(f"❌ Weekly cleanup error: {e}")
    
    def daily_performance_log(self):
        """Kunlik performance log saqlash"""
        try:
            filename = f"logs/performance_{datetime.now().strftime('%Y%m%d')}.json"
            self.face_system.performance_monitor.save_performance_log(filename)
            print(f"📊 Kunlik performance log saqlandi: {filename}")
            
        except Exception as e:
            print(f"❌ Performance log error: {e}")
    
    def start_scheduler(self):
        """Scheduler ni ishga tushirish"""
        if self.is_running:
            print("⚠️  Scheduler allaqachon ishlamoqda")
            return
        
        self.is_running = True
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Har daqiqada tekshirish
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("⏰ Scheduler ishga tushdi")
    
    def stop_scheduler(self):
        """Scheduler ni to'xtatish"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        print("⏰ Scheduler to'xtatildi")
    
    def get_next_tasks(self):
        """Keyingi vazifalar ro'yxati"""
        jobs = schedule.get_jobs()
        if not jobs:
            return "Hech qanday vazifa rejalashtirilmagan"
        
        next_tasks = []
        for job in jobs:
            next_run = job.next_run
            if next_run:
                next_tasks.append(f"{job.job_func.__name__}: {next_run.strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(next_tasks)
    
    def manual_end_of_day(self):
        """Manual kun oxiri reset"""
        print("🌙 Manual end-of-day reset...")
        self.end_of_day_reset()

# Global scheduler instance
_scheduler = None

def get_scheduler(face_system) -> SystemScheduler:
    """Get global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SystemScheduler(face_system)
    return _scheduler