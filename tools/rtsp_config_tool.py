#!/usr/bin/env python3
"""
RTSP Configuration Tool - DH-C4K-P va boshqa IP kameralar uchun
"""
import json
import os
import cv2
from urllib.parse import urlparse

def get_rtsp_url_from_user():
    """Foydalanuvchidan RTSP ma'lumotlarini olish"""
    print("="*60)
    print("📹 RTSP CAMERA CONFIGURATION")
    print("="*60)
    
    # Camera IP
    ip = input("Camera IP address: ").strip()
    if not ip:
        print("❌ IP address required")
        return None
    
    # Credentials
    username = input("Username (default: admin): ").strip() or "admin"
    password = input("Password (default: admin): ").strip() or "admin"
    
    # Port
    port = input("RTSP Port (default: 554): ").strip() or "554"
    
    print("\n📋 DH-C4K-P RTSP URL Options:")
    print("1. Main stream (high quality)")
    print("2. Sub stream (low quality, faster)")
    print("3. Live stream")
    print("4. Custom path")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    # Generate RTSP URL based on choice
    if choice == "1":
        path = "/cam/realmonitor?channel=1&subtype=0"
    elif choice == "2":
        path = "/cam/realmonitor?channel=1&subtype=1"
    elif choice == "3":
        path = "/live"
    elif choice == "4":
        path = input("Enter custom path (e.g., /h264Preview_01_main): ").strip()
    else:
        path = "/cam/realmonitor?channel=1&subtype=0"  # Default
    
    # Build RTSP URL
    rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{path}"
    
    return rtsp_url

def test_rtsp_connection(rtsp_url):
    """RTSP ulanishni test qilish"""
    print(f"\n🔄 Testing RTSP connection...")
    print(f"URL: {mask_credentials(rtsp_url)}")
    
    try:
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        
        if not cap.isOpened():
            print("❌ Failed to open RTSP stream")
            cap.release()
            return False
        
        # Try to read frame
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("❌ Failed to read frame from RTSP stream")
            cap.release()
            return False
        
        # Get stream info
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print("✅ RTSP connection successful!")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {fps:.1f}")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ RTSP test error: {e}")
        return False

def mask_credentials(url):
    """RTSP URL dagi parolni yashirish"""
    try:
        parsed = urlparse(url)
        if parsed.username and parsed.password:
            return url.replace(f"{parsed.username}:{parsed.password}@", "***:***@")
        return url
    except:
        return url

def update_config_file(rtsp_url):
    """config.json faylini yangilash"""
    config_file = "../config.json"
    
    try:
        # Load existing config
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Update camera configuration
        config["camera_source"] = rtsp_url
        config["camera_type"] = "RTSP"
        
        # Update RTSP config
        parsed = urlparse(rtsp_url)
        config["rtsp_config"] = {
            "primary_url": rtsp_url,
            "backup_urls": [],
            "username": parsed.username or "admin",
            "password": parsed.password or "admin",
            "timeout_seconds": 10,
            "buffer_size": 1
        }
        
        # Save config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration saved to {config_file}")
        return True
        
    except Exception as e:
        print(f"❌ Config update error: {e}")
        return False

def show_usage_instructions():
    """Ishlatish yo'riqnomasi"""
    print("\n" + "="*60)
    print("📖 USAGE INSTRUCTIONS")
    print("="*60)
    print("1. Run the face recognition system:")
    print("   python3 start_optimized.py")
    print()
    print("2. The system will automatically use RTSP camera")
    print()
    print("3. Monitor camera status with 'I' key during operation")
    print()
    print("4. If connection fails, check:")
    print("   - Camera IP address")
    print("   - Username/password")
    print("   - Network connectivity")
    print("   - RTSP port (usually 554)")
    print("="*60)

def main():
    """Asosiy funksiya"""
    print("🎥 Welcome to RTSP Configuration Tool")
    print("This tool will help you configure DH-C4K-P camera")
    
    # Get RTSP URL from user
    rtsp_url = get_rtsp_url_from_user()
    
    if not rtsp_url:
        print("❌ Configuration cancelled")
        return
    
    print(f"\n📋 Generated RTSP URL: {mask_credentials(rtsp_url)}")
    
    # Test connection
    if not test_rtsp_connection(rtsp_url):
        retry = input("\n❓ Connection failed. Try different settings? (y/n): ").lower()
        if retry == 'y':
            return main()  # Restart
        else:
            print("❌ Configuration cancelled")
            return
    
    # Update config file
    if update_config_file(rtsp_url):
        show_usage_instructions()
    else:
        print("❌ Failed to update configuration")

if __name__ == "__main__":
    main()