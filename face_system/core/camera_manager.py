"""
Robust Camera Manager - Automatic reconnection and fallback
Enhanced with RTSP support for IP cameras - SIMPLE VERSION (RTSP DISABLED)
"""
import cv2
import time
import threading
from typing import Optional, Tuple, Union
import numpy as np
# from .simple_rtsp_manager import SimpleRTSPManager  # RTSP disabled

class CameraManager:
    """Professional camera management with auto-reconnection and RTSP support"""
    
    def __init__(self, camera_source: Union[int, str], backup_cameras: list = None):
        self.camera_source = camera_source
        self.backup_cameras = backup_cameras or []
        self.is_rtsp = isinstance(camera_source, str) and camera_source.startswith('rtsp://')
        
        # Camera instances
        self.cap = None
        self.rtsp_manager = None
        
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2.0
        self.lock = threading.Lock()
        
        # Frame properties
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        
        camera_type = "RTSP" if self.is_rtsp else "USB"
        print(f"📹 CameraManager initialized - Type: {camera_type}")
        if self.is_rtsp:
            print(f"   RTSP URL: {self._mask_rtsp_credentials(camera_source)}")
        else:
            print(f"   Camera Index: {camera_source}")
    
    def _mask_rtsp_credentials(self, url: str) -> str:
        """Mask RTSP credentials for logging"""
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
        """Connect to camera with fallback options"""
        with self.lock:
            if self.is_rtsp:
                return self._connect_rtsp()
            else:
                return self._connect_usb()
    
    def _connect_rtsp(self) -> bool:
        """Connect to RTSP camera - DISABLED FOR NOW"""
        print("⚠️  RTSP support temporarily disabled - using USB camera")
        return False
        
        # RTSP CODE COMMENTED OUT:
        # try:
        #     # Use simple RTSP manager - exactly like test script
        #     self.rtsp_manager = SimpleRTSPManager(self.camera_source)
        #     
        #     # Connect
        #     if self.rtsp_manager.connect():
        #         self.is_connected = True
        #         self.reconnect_attempts = 0
        #         
        #         # Get stream properties
        #         stream_info = self.rtsp_manager.get_camera_info()
        #         self.frame_width = stream_info.get('width', 640)
        #         self.frame_height = stream_info.get('height', 360)
        #         self.fps = stream_info.get('fps', 25)
        #         
        #         return True
        #     
        #     return False
        #     
        # except Exception as e:
        #     print(f"❌ Simple RTSP connection error: {e}")
        #     return False
    
    def _connect_usb(self) -> bool:
        """Connect to USB camera"""
        # Try primary camera
        if self._try_connect_camera(self.camera_source):
            print(f"✅ Primary camera connected: {self.camera_source}")
            return True
        
        # Try backup cameras
        for backup_index in self.backup_cameras:
            if isinstance(backup_index, int) and self._try_connect_camera(backup_index):
                print(f"✅ Backup camera connected: {backup_index}")
                self.camera_source = backup_index
                return True
        
        print("❌ No USB cameras available")
        return False
    
    def _try_connect_camera(self, camera_index: int) -> bool:
        """Try to connect to specific camera"""
        try:
            cap = cv2.VideoCapture(camera_index)
            
            # Test camera
            if not cap.isOpened():
                cap.release()
                return False
            
            # Test frame capture
            ret, frame = cap.read()
            if not ret or frame is None:
                cap.release()
                return False
            
            # Configure camera
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
            
            # Success
            if self.cap:
                self.cap.release()
            
            self.cap = cap
            self.is_connected = True
            self.reconnect_attempts = 0
            
            return True
            
        except Exception as e:
            print(f"❌ Camera {camera_index} connection error: {e}")
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read frame with automatic reconnection"""
        with self.lock:
            if not self.is_connected:
                if not self._attempt_reconnect():
                    return False, self._get_fallback_frame()
            
            try:
                if self.is_rtsp:
                    return self.rtsp_manager.read_frame()
                else:
                    ret, frame = self.cap.read()
                    
                    if not ret or frame is None:
                        print("⚠️  Frame read failed, attempting reconnection...")
                        self.is_connected = False
                        
                        if self._attempt_reconnect():
                            ret, frame = self.cap.read()
                            if ret and frame is not None:
                                return True, frame
                        
                        return False, self._get_fallback_frame()
                    
                    return True, frame
                    
            except Exception as e:
                print(f"❌ Frame read error: {e}")
                self.is_connected = False
                return False, self._get_fallback_frame()
    
    def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect camera"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"❌ Max reconnection attempts reached ({self.max_reconnect_attempts})")
            return False
        
        print(f"🔄 Reconnecting camera... (attempt {self.reconnect_attempts + 1})")
        self.reconnect_attempts += 1
        
        time.sleep(self.reconnect_delay)
        
        if self.connect():
            print("✅ Camera reconnected successfully")
            return True
        
        return False
    
    def _get_fallback_frame(self) -> np.ndarray:
        """Generate fallback frame when camera is unavailable"""
        frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)
        
        # Add "NO CAMERA" text
        cv2.putText(frame, "CAMERA DISCONNECTED", (50, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, "Attempting reconnection...", (50, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f"Attempt: {self.reconnect_attempts}/{self.max_reconnect_attempts}", 
                   (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def is_available(self) -> bool:
        """Check if camera is available"""
        if self.is_rtsp:
            return self.rtsp_manager and self.rtsp_manager.is_available()
        else:
            return self.is_connected and self.cap is not None

    def get_camera_info(self) -> dict:
        """Get camera information"""
        if not self.is_available():
            return {
                "status": "disconnected", 
                "type": "RTSP" if self.is_rtsp else "USB",
                "source": self._mask_rtsp_credentials(str(self.camera_source)) if self.is_rtsp else self.camera_source
            }

        try:
            if self.is_rtsp:
                info = self.rtsp_manager.get_stream_info()
                info["type"] = "RTSP"
                return info
            else:
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(self.cap.get(cv2.CAP_PROP_FPS))

                return {
                    "status": "connected",
                    "type": "USB",
                    "source": self.camera_source,
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "reconnect_attempts": self.reconnect_attempts
                }
        except:
            return {
                "status": "error", 
                "type": "RTSP" if self.is_rtsp else "USB",
                "source": self._mask_rtsp_credentials(str(self.camera_source)) if self.is_rtsp else self.camera_source
            }
    
    def get_camera_info(self) -> dict:
        """Get camera information"""
        if not self.is_available():
            return {
                "status": "disconnected", 
                "type": "RTSP" if self.is_rtsp else "USB",
                "source": self._mask_rtsp_credentials(str(self.camera_source)) if self.is_rtsp else self.camera_source
            }

        try:
            if self.is_rtsp:
                return self.rtsp_manager.get_camera_info()
            else:
                width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(self.cap.get(cv2.CAP_PROP_FPS))

                return {
                    "status": "connected",
                    "type": "USB",
                    "source": self.camera_source,
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "reconnect_attempts": self.reconnect_attempts
                }
        except:
            return {
                "status": "error", 
                "type": "RTSP" if self.is_rtsp else "USB",
                "source": self._mask_rtsp_credentials(str(self.camera_source)) if self.is_rtsp else self.camera_source
            }
    
    def reset_reconnect_counter(self):
        """Reset reconnection counter"""
        self.reconnect_attempts = 0
        print("🔄 Reconnection counter reset")
    
    def release(self):
        """Release camera resources"""
        with self.lock:
            if self.is_rtsp and self.rtsp_manager:
                self.rtsp_manager.release()
                self.rtsp_manager = None
            elif self.cap:
                self.cap.release()
                self.cap = None
            
            self.is_connected = False
            print("📹 Camera released")
    
    def __del__(self):
        """Destructor"""
        self.release()

# Global camera manager instance
_camera_manager = None

def get_camera_manager(camera_source: Union[int, str] = 0, backup_cameras: list = None) -> CameraManager:
    """Get global camera manager instance"""
    global _camera_manager
    if _camera_manager is None:
        _camera_manager = CameraManager(camera_source, backup_cameras)
    return _camera_manager