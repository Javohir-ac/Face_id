"""
Simple RTSP Manager - Exactly like working test script
CURRENTLY DISABLED - USING USB CAMERA INSTEAD
"""

# ENTIRE FILE COMMENTED OUT - RTSP SUPPORT DISABLED
# 
# import cv2
# import time
# import threading
# import numpy as np
# from typing import Optional, Tuple
# 
# class SimpleRTSPManager:
#     """Simple RTSP manager - exactly like test script"""
#     
#     def __init__(self, rtsp_url: str):
#         self.rtsp_url = rtsp_url
#         self.cap = None
#         self.is_connected = False
#         self.lock = threading.Lock()
#         
#         print(f"📹 SimpleRTSPManager - URL: {self._mask_url(rtsp_url)}")
#     
#     # ... rest of the class methods commented out ...

print("⚠️  SimpleRTSPManager disabled - using USB camera instead")
    
    def _mask_url(self, url: str) -> str:
        """Mask credentials in URL"""
        try:
            if '@' in url and '://' in url:
                parts = url.split('://')
                if len(parts) == 2:
                    protocol = parts[0]
                    rest = parts[1]
                    if '@' in rest:
                        auth_part, host_part = rest.split('@', 1)
                        return f"{protocol}://***:***@{host_part}"
            return url
        except:
            return url
    
    def connect(self) -> bool:
        """Connect to RTSP - EXACTLY like working test script"""
        with self.lock:
            try:
                print(f"🔄 Connecting to RTSP...")
                
                # EXACTLY like test_rtsp_like_main.py
                import os
                os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'
                os.environ['OPENCV_VIDEOIO_PRIORITY_FFMPEG'] = '1'
                os.environ['OPENCV_FFMPEG_DEBUG'] = '0'
                os.environ['FFMPEG_LOG_LEVEL'] = 'quiet'
                
                # Create VideoCapture exactly like test script
                self.cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                
                # Settings exactly like test script
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FPS, 15)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
                self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 1)
                
                if not self.cap.isOpened():
                    print("❌ Failed to open RTSP stream")
                    return False
                
                # Test frame reading
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("❌ No frame from RTSP")
                    self.cap.release()
                    return False
                
                # Get properties
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = self.cap.get(cv2.CAP_PROP_FPS)
                
                print(f"✅ RTSP connected: {width}x{height} @ {fps:.1f}fps")
                
                self.is_connected = True
                return True
                
            except Exception as e:
                print(f"❌ RTSP connection error: {e}")
                return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read frame - exactly like test script"""
        with self.lock:
            if not self.is_connected or not self.cap:
                return False, None
            
            try:
                ret, frame = self.cap.read()
                
                if not ret or frame is None:
                    print("⚠️  RTSP frame read failed")
                    return False, None
                
                return True, frame
                
            except Exception as e:
                print(f"❌ RTSP read error: {e}")
                return False, None
    
    def is_available(self) -> bool:
        """Check if available"""
        return self.is_connected and self.cap is not None
    
    def get_camera_info(self) -> dict:
        """Get camera info"""
        if not self.is_available():
            return {"status": "disconnected", "type": "RTSP"}
        
        try:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            return {
                "status": "connected",
                "type": "RTSP",
                "width": width,
                "height": height,
                "fps": fps,
                "url": self._mask_url(self.rtsp_url)
            }
        except:
            return {"status": "error", "type": "RTSP"}
    
    def release(self):
        """Release resources"""
        with self.lock:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.is_connected = False
            print("📹 Simple RTSP released")
    
    def __del__(self):
        """Destructor"""
        self.release()