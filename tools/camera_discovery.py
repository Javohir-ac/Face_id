#!/usr/bin/env python3
"""
IP Camera Discovery Tool - DH-C4K-P va boshqa kameralar uchun
"""
import socket
import subprocess
import re
import requests
from urllib.parse import urlparse
import cv2
import time

def scan_network_for_cameras(network_base="192.168.1"):
    """Network da IP kameralarni qidirish"""
    print(f"🔍 {network_base}.0/24 network da kameralar qidirilmoqda...")
    
    found_devices = []
    
    for i in range(1, 255):
        ip = f"{network_base}.{i}"
        
        # Ping test
        try:
            result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                print(f"📡 {ip} - Device found")
                
                # Check common camera ports
                camera_info = check_camera_ports(ip)
                if camera_info:
                    found_devices.append({
                        'ip': ip,
                        'info': camera_info
                    })
                    
        except (subprocess.TimeoutExpired, Exception):
            continue
    
    return found_devices

def check_camera_ports(ip):
    """Kamera portlarini tekshirish"""
    camera_ports = [80, 554, 8080, 8000, 37777, 34567]
    open_ports = []
    
    for port in camera_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        
        try:
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
                print(f"   ✅ Port {port} open")
        except:
            pass
        finally:
            sock.close()
    
    if open_ports:
        return {
            'open_ports': open_ports,
            'likely_camera': 554 in open_ports or 37777 in open_ports
        }
    
    return None

def test_rtsp_urls(ip, username="admin", password="admin"):
    """RTSP URL larni test qilish"""
    print(f"\n🎥 {ip} da RTSP URLs test qilinmoqda...")
    
    # DH-C4K-P uchun RTSP URL variantlari
    rtsp_urls = [
        f"rtsp://{username}:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
        f"rtsp://{username}:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=1",
        f"rtsp://{username}:{password}@{ip}:554/live",
        f"rtsp://{username}:{password}@{ip}:554/h264Preview_01_main",
        f"rtsp://{username}:{password}@{ip}:554/h264Preview_01_sub",
        f"rtsp://{username}:{password}@{ip}:554/stream1",
        f"rtsp://{username}:{password}@{ip}:554/stream2",
        f"rtsp://{ip}:554/live",  # Without auth
    ]
    
    working_urls = []
    
    for url in rtsp_urls:
        print(f"   Testing: {url}")
        
        try:
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Try to read a frame
            ret, frame = cap.read()
            
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"   ✅ SUCCESS: {width}x{height}")
                
                working_urls.append({
                    'url': url,
                    'resolution': f"{width}x{height}",
                    'frame_test': True
                })
            else:
                print(f"   ❌ No frame received")
                
            cap.release()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return working_urls

def get_camera_info_web(ip, username="admin", password="admin"):
    """Web interface orqali kamera ma'lumotlarini olish"""
    try:
        # Common web interface URLs
        web_urls = [
            f"http://{ip}",
            f"http://{ip}:80",
            f"http://{ip}:8080",
            f"https://{ip}",
        ]
        
        for url in web_urls:
            try:
                response = requests.get(url, timeout=3, auth=(username, password))
                if response.status_code == 200:
                    print(f"   ✅ Web interface: {url}")
                    
                    # Look for camera model in response
                    content = response.text.lower()
                    if 'dahua' in content or 'dh-' in content:
                        print(f"   📹 Dahua camera detected")
                        return {'web_url': url, 'brand': 'Dahua'}
                        
            except:
                continue
                
    except Exception as e:
        print(f"   ❌ Web check error: {e}")
    
    return None

def main():
    """Asosiy funksiya"""
    print("="*60)
    print("📹 IP CAMERA DISCOVERY TOOL")
    print("="*60)
    
    # Network scan
    network = input("Network base (default: 192.168.1): ").strip() or "192.168.1"
    
    devices = scan_network_for_cameras(network)
    
    if not devices:
        print("❌ Hech qanday kamera topilmadi")
        return
    
    print(f"\n✅ {len(devices)} ta device topildi")
    
    # Test each device
    for device in devices:
        ip = device['ip']
        print(f"\n" + "="*40)
        print(f"📹 Testing {ip}")
        print("="*40)
        
        # Get credentials
        username = input(f"Username for {ip} (default: admin): ").strip() or "admin"
        password = input(f"Password for {ip} (default: admin): ").strip() or "admin"
        
        # Test RTSP
        working_urls = test_rtsp_urls(ip, username, password)
        
        if working_urls:
            print(f"\n✅ {len(working_urls)} working RTSP URLs found:")
            for i, url_info in enumerate(working_urls, 1):
                print(f"   {i}. {url_info['url']}")
                print(f"      Resolution: {url_info['resolution']}")
        
        # Test web interface
        web_info = get_camera_info_web(ip, username, password)
        if web_info:
            print(f"   Web interface: {web_info['web_url']}")
    
    print("\n" + "="*60)
    print("🎯 DISCOVERY COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()