#!/usr/bin/env python3
"""
🚀 ULTRA-OPTIMIZED FACE RECOGNITION SYSTEM LAUNCHER
Professional Face Recognition with RTSP Camera Support
Maximum Performance with Threading and Optimizations
"""

import os
import sys
import time
import psutil
import subprocess
from datetime import datetime

def print_banner():
    """Professional system banner"""
    print("=" * 60)
    print("🚀 PROFESSIONAL FACE RECOGNITION SYSTEM")
    print("=" * 60)
    print(f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def check_system_requirements():
    """System requirements check"""
    print("🔍 System requirements tekshirilmoqda...")
    
    # Memory check
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    print(f"✅ Xotira: {memory_gb:.1f} GB mavjud")
    
    # CPU check
    cpu_count = psutil.cpu_count()
    print(f"✅ CPU: {cpu_count} ta core")
    
    # Disk space check
    disk = psutil.disk_usage('.')
    disk_gb = disk.free / (1024**3)
    print(f"✅ Disk: {disk_gb:.1f} GB bo'sh")
    
    return True

def check_dependencies():
    """Check required dependencies"""
    print("📦 Dependencies tekshirilmoqda...")
    
    required_packages = [
        'cv2', 'face_recognition', 'numpy', 'flask', 
        'threading', 'queue', 'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'face_recognition':
                import face_recognition
            elif package == 'numpy':
                import numpy
            elif package == 'flask':
                import flask
            elif package == 'threading':
                import threading
            elif package == 'queue':
                import queue
            elif package == 'psutil':
                import psutil
            print(f"✅ {package} - OK")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - MISSING")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install opencv-python face-recognition numpy flask psutil")
        return False
    
    print("✅ Barcha dependencies mavjud")
    return True

def check_previous_session():
    """Check for previous session data"""
    print("🔍 Oldingi sessiya tekshirilmoqda...")
    
    if os.path.exists('current_users.json'):
        print("⚠️  Oldingi sessiya topildi - current_users.json")
        
        # Read and show current users
        try:
            import json
            with open('current_users.json', 'r', encoding='utf-8') as f:
                current_users = json.load(f)
            
            if current_users:
                print(f"📋 Ichkarida qolgan userlar: {len(current_users)}")
                for user in current_users:
                    print(f"   - {user}")
                
                response = input("🤔 Ularni chiqarib yuborishni xohlaysizmi? (y/n): ").lower()
                if response == 'y':
                    # Clear current users
                    with open('current_users.json', 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
                    print("✅ Barcha userlar chiqarildi")
                else:
                    print("ℹ️  Userlar o'z holatida qoldirildi")
            else:
                print("ℹ️  Hech kim ichkarida emas")
        except Exception as e:
            print(f"⚠️  current_users.json o'qishda xatolik: {e}")
    else:
        print("✅ Yangi sessiya - oldingi ma'lumotlar yo'q")

def optimize_environment():
    """Optimize system environment for maximum performance"""
    print("⚡ Environment optimizatsiya qilinmoqda...")
    
    try:
        # Set environment variables for OpenCV optimization
        os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'
        os.environ['OPENCV_VIDEOIO_PRIORITY_FFMPEG'] = '1'
        
        # Suppress HEVC/H.265 codec errors
        os.environ['OPENCV_FFMPEG_DEBUG'] = '0'
        os.environ['FFMPEG_LOG_LEVEL'] = 'quiet'
        
        # Remove codec forcing to avoid mismatch
        # os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'video_codec;h264'
        
        # Threading optimization
        os.environ['OMP_NUM_THREADS'] = str(min(4, psutil.cpu_count()))
        
        # Memory optimization
        os.environ['MALLOC_ARENA_MAX'] = '2'
        
        print("✅ Environment optimizatsiya tugallandi")
        return True
    except Exception as e:
        print(f"⚠️  Environment optimizatsiya xatoligi: {e}")
        return False

def start_main_system():
    """Start the main face recognition system"""
    print("🎯 Asosiy tizim ishga tushirilmoqda...")
    
    try:
        # Import and run main system
        from main import main
        main()
    except KeyboardInterrupt:
        print("\n👋 Tizim foydalanuvchi tomonidan to'xtatildi")
    except Exception as e:
        print(f"❌ Tizim ishga tushirishda xatolik: {e}")
        print("🔧 Debugging ma'lumotlari:")
        import traceback
        traceback.print_exc()

def main():
    """Main launcher function"""
    start_time = time.time()
    
    # Print banner
    print_banner()
    
    try:
        # System checks
        if not check_system_requirements():
            print("❌ System requirements bajarilmadi")
            return
        
        if not check_dependencies():
            print("❌ Dependencies yetishmayapti")
            return
        
        # Check previous session
        check_previous_session()
        
        # Optimize environment
        if not optimize_environment():
            print("⚠️  Environment optimizatsiya muvaffaqiyatsiz, lekin davom etamiz...")
        
        # Show startup time
        startup_time = time.time() - start_time
        print(f"⏱️  Startup vaqti: {startup_time:.1f} soniya")
        print("=" * 60)
        
        # Start main system
        start_main_system()
        
    except KeyboardInterrupt:
        print("\n👋 Launcher to'xtatildi")
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Show total runtime
        total_time = time.time() - start_time
        print("=" * 60)
        print(f"⏱️  Umumiy ish vaqti: {total_time:.1f} soniya")
        print("=" * 60)

if __name__ == "__main__":
    main()