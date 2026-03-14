#!/usr/bin/env python3
"""
🎯 FACE RECOGNITION SYSTEM - Universal Launcher
Automatic fallback: RTSP -> USB -> Error handling
"""

import subprocess
import sys
import os
import shutil

def test_rtsp_connection():
    """Test if RTSP camera is working - DISABLED"""
    print("⚠️  RTSP test disabled - using USB camera")
    return False
    
    # RTSP TEST CODE COMMENTED OUT:
    # try:
    #     from face_system.core.simple_rtsp_manager import SimpleRTSPManager
    #     
    #     rtsp_url = "rtsp://admin:9911800292%23%23@192.168.1.3:554/cam/realmonitor?channel=1&subtype=1"
    #     
    #     # Quick test with simple manager
    #     rtsp_manager = SimpleRTSPManager(rtsp_url)
    #     if rtsp_manager.connect():
    #         ret, frame = rtsp_manager.read_frame()
    #         rtsp_manager.release()
    #         return ret and frame is not None
    #     return False
    # except Exception as e:
    #     print(f"RTSP test error: {e}")
    #     return False

def test_usb_camera():
    """Test if USB camera is working"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        return False
    except:
        return False

def switch_to_usb():
    """Switch configuration to USB camera"""
    try:
        if os.path.exists('config_usb.json'):
            # Backup current config
            if os.path.exists('config.json'):
                shutil.copy('config.json', 'config_rtsp_backup.json')
            
            # Switch to USB config
            shutil.copy('config_usb.json', 'config.json')
            print("✅ USB kameraga o'tkazildi")
            return True
    except Exception as e:
        print(f"❌ USB config o'tkazishda xatolik: {e}")
    return False

def main():
    """Universal system launcher with automatic fallback"""
    print("🚀 Universal Face Recognition System Launcher")
    print("=" * 50)
    
    # Test cameras
    print("🔍 Kameralar tekshirilmoqda...")
    
    rtsp_works = test_rtsp_connection()
    usb_works = test_usb_camera()
    
    print(f"📹 RTSP Camera: {'✅ OK' if rtsp_works else '❌ FAILED'}")
    print(f"📷 USB Camera: {'✅ OK' if usb_works else '❌ FAILED'}")
    
    # Choose best option
    if rtsp_works:
        print("🎯 RTSP kamera bilan ishga tushirilmoqda...")
        launcher = 'start_silent.py'  # Silent to suppress HEVC errors
    elif usb_works:
        print("🎯 USB kameraga o'tkazilmoqda...")
        if switch_to_usb():
            launcher = 'start_optimized.py'
        else:
            launcher = 'main.py'
    else:
        print("❌ Hech qanday kamera topilmadi!")
        print("💡 USB kamera ulang yoki RTSP sozlamalarini tekshiring")
        return
    
    # Launch system
    try:
        if os.path.exists(launcher):
            print(f"🚀 {launcher} ishga tushirilmoqda...")
            subprocess.run([sys.executable, launcher], check=True)
        else:
            print(f"❌ {launcher} fayli topilmadi, main.py ishlatilmoqda...")
            subprocess.run([sys.executable, 'main.py'], check=True)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Tizim ishga tushmadi: {e}")
        print("💡 Dependencies o'rnatilganligini tekshiring:")
        print("   pip install opencv-python face-recognition numpy flask psutil")
    except KeyboardInterrupt:
        print("\n👋 Tizim to'xtatildi")
    except Exception as e:
        print(f"❌ Kutilmagan xatolik: {e}")

if __name__ == "__main__":
    main()