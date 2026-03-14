#!/usr/bin/env python3
"""
🎯 Professional Face Recognition System - face_recognition kutubxonasi
Enhanced with robust error handling and camera management
"""

import cv2
import threading
import time
import numpy as np
import face_recognition
from datetime import datetime
from face_system.core.face_system import FaceRecognitionSystem
from face_system.web.app import create_web_app
from face_system.core.camera_manager import get_camera_manager
from face_system.core.error_handler import get_error_handler, handle_errors

class CameraMonitor:
    def __init__(self, face_system):
        self.face_system = face_system
        
        # Determine camera source from config
        camera_source = face_system.data_manager.config.get('camera_source', 0)
        camera_type = face_system.data_manager.config.get('camera_type', 'USB')
        
        # Setup camera manager based on type
        if camera_type == 'RTSP' and isinstance(camera_source, str):
            rtsp_config = face_system.data_manager.config.get('rtsp_config', {})
            backup_urls = rtsp_config.get('backup_urls', [])
            self.camera_manager = get_camera_manager(camera_source, backup_urls)
        else:
            # USB camera (backward compatibility)
            camera_index = face_system.data_manager.config.get('camera_index', camera_source)
            backup_cameras = [1, 2]  # Default backup USB cameras
            self.camera_manager = get_camera_manager(camera_index, backup_cameras)
        
        self.error_handler = get_error_handler()

        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0

    @handle_errors("Camera Monitoring")
    def start_monitoring(self):
        """Professional kamera monitoring with robust error handling"""
        self.error_handler.log_info("Professional kamera monitoring boshlandi", "CameraMonitor")

        # Connect to camera
        if not self.camera_manager.connect():
            self.error_handler.log_error(
                Exception("Camera connection failed"),
                "CameraMonitor"
            )
            return

        self.face_system.is_running = True
        last_recognition = {}
        cooldown = self.face_system.data_manager.config['recognition_cooldown']

        # Memory monitoring
        memory_check_interval = 30  # seconds
        last_memory_check = time.time()

        while self.face_system.is_running:
            try:
                # Read frame with automatic reconnection
                ret, frame = self.camera_manager.read_frame()

                if not ret or frame is None:
                    # Camera manager handles reconnection automatically
                    cv2.imshow('Professional Face Recognition System',
                              self.camera_manager._get_fallback_frame())

                    if cv2.waitKey(1) & 0xFF == 27:  # ESC
                        break
                    continue

                # Flip frame
                frame = cv2.flip(frame, 1)

                # Update FPS counter
                self._update_fps_counter()

                # Memory monitoring - less frequent for RTSP speed
                current_time = time.time()
                memory_interval = 60 if self.camera_manager.is_rtsp else memory_check_interval  # Less frequent for RTSP
                if current_time - last_memory_check > memory_interval:
                    if not self.face_system.memory_optimizer.monitor_memory_threshold(400):
                        self.error_handler.log_warning(
                            "High memory usage detected",
                            "CameraMonitor"
                        )
                    last_memory_check = current_time

                # Professional yuz aniqlash - optimized frame processing
                if not hasattr(self, 'frame_skip_counter'):
                    self.frame_skip_counter = 0
                self.frame_skip_counter += 1

                # Adaptive frame skipping for RTSP (much more aggressive)
                if self.camera_manager.is_rtsp:
                    skip_frames = 8  # Skip many more frames for RTSP
                else:
                    skip_frames = 3 if len(self.face_system.known_face_encodings) > 100 else 2

                if self.frame_skip_counter % skip_frames == 0:  # Optimized frame skipping
                    face_locations, face_encodings = self._process_frame_for_faces(frame)
                else:
                    face_locations = []
                    face_encodings = []

                current_datetime = datetime.now()
                detected_users = set()

                # Record frame processing time
                frame_start_time = time.time()

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Professional yuz tanish
                    name, confidence = self.face_system.recognize_face(face_encoding)

                    # Ramka rangi
                    if name != "Unknown":
                        color = (0, 255, 0)  # Yashil - tanilgan
                        detected_users.add(name)

                        # Professional cooldown
                        user_key = f"{name}_{left}_{top}"

                        # 1 daqiqa interval
                        if (user_key not in last_recognition or
                            (current_datetime - last_recognition[user_key]).total_seconds() >= 60):

                            # Professional toggle action
                            self.face_system.process_user_action(name, confidence)
                            last_recognition[user_key] = current_datetime
                            last_recognition[name] = current_datetime
                    else:
                        color = (0, 0, 255)  # Qizil - noma'lum

                    # Professional ramka chizish
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                    # Professional matn
                    label = f"{name} ({confidence:.2f})"
                    cv2.putText(frame, label, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    # Keyingi kutilayotgan action
                    if name != "Unknown":
                        next_action = self.face_system.get_next_expected_action(name)
                        action_text = "KELISH" if next_action == 'entry' else "KETISH"
                        cv2.putText(frame, f"Keyingi: {action_text}", (left, bottom+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Record frame processing time
                if face_locations:
                    frame_time = time.time() - frame_start_time
                    self.face_system.performance_monitor.record_frame_processing_time(frame_time)

                # Record system metrics periodically - less frequent for RTSP
                if not hasattr(self, 'last_system_check'):
                    self.last_system_check = time.time()

                system_check_interval = 10 if self.camera_manager.is_rtsp else 5  # Less frequent for RTSP
                if time.time() - self.last_system_check > system_check_interval:
                    self.face_system.performance_monitor.record_system_metrics()
                    self.last_system_check = time.time()

                # Joriy foydalanuvchilar ro'yxati
                self.draw_current_users(frame, current_datetime)

                # Add system info to frame
                self._draw_system_info(frame)

                # Professional frameni ko'rsatish
                cv2.imshow('Professional Face Recognition System', frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('p'):  # P tugmasi - Performance report
                    self.face_system.performance_monitor.print_performance_report()
                elif key == ord('c'):  # C tugmasi - Cache stats
                    self.face_system.cache_manager.print_stats()
                elif key == ord('m'):  # M tugmasi - Memory stats
                    self.face_system.memory_optimizer.print_memory_stats()  
                elif key == ord('r'):  # R tugmasi - Reset all users
                    print("\n🔄 Barcha userlarni chiqarish...")
                    exit_count = self.face_system.reset_all_users("manual_reset")
                    if exit_count > 0:
                        print(f"✅ {exit_count} ta user chiqarildi")
                    else:
                        print("ℹ️  Hech kim ichkarida emas edi")
                elif key == ord('s'):  # S tugmasi - Scheduler info
                    print("\n⏰ SCHEDULER MA'LUMOTLARI:")
                    print("Keyingi vazifalar:")
                    print(self.face_system.scheduler.get_next_tasks())
                elif key == ord('e'):  # E tugmasi - Manual end-of-day
                    print("\n🌙 Manual end-of-day reset...")
                    self.face_system.scheduler.manual_end_of_day()
                elif key == ord('i'):  # I tugmasi - Camera info
                    camera_info = self.camera_manager.get_camera_info()
                    print(f"\n📹 CAMERA INFO: {camera_info}")
                elif key == ord('h'):  # H tugmasi - Help
                    self._show_help()

            except Exception as e:
                self.error_handler.log_error(e, "Camera monitoring loop")
                time.sleep(1)  # Prevent rapid error loops

        # Cleanup
        self.camera_manager.release()
        cv2.destroyAllWindows()
        self.error_handler.log_info("Professional kamera monitoring to'xtatildi", "CameraMonitor")

    def _process_frame_for_faces(self, frame):
        """Process frame for face detection with aggressive RTSP optimization"""
        try:
            # Aggressive optimization for RTSP cameras
            if self.camera_manager.is_rtsp:
                # Much smaller frame for RTSP (4x smaller)
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                scale_factor = 4
            else:
                # Standard optimization for USB cameras
                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                scale_factor = 2
            
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Use HOG model for maximum speed
            face_locations = face_recognition.face_locations(
                rgb_frame, 
                model="hog", 
                number_of_times_to_upsample=0  # No upsampling for speed
            )
            
            # Minimal face encodings for speed
            face_encodings = face_recognition.face_encodings(
                rgb_frame, 
                face_locations, 
                num_jitters=1  # Minimal jitters for speed
            )

            # Scale back face locations
            face_locations = [(top*scale_factor, right*scale_factor, bottom*scale_factor, left*scale_factor) 
                            for (top, right, bottom, left) in face_locations]

            return face_locations, face_encodings

        except Exception as e:
            self.error_handler.log_error(e, "Face processing")
            return [], []

    def _update_fps_counter(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = time.time()

        if current_time - self.last_fps_time >= 1.0:  # Update every second
            self.current_fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time

    def _draw_system_info(self, frame):
        """Draw system information on frame"""
        try:
            # Camera info
            camera_info = self.camera_manager.get_camera_info()
            status_color = (0, 255, 0) if camera_info.get('status') == 'connected' else (0, 0, 255)

            # System info
            info_y = frame.shape[0] - 80
            cv2.putText(frame, f"FPS: {self.current_fps:.1f}", (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.putText(frame, f"Camera: {camera_info.get('status', 'unknown')}",
                       (10, info_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)

            cv2.putText(frame, f"Users: {len(self.face_system.known_face_names)}",
                       (10, info_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        except Exception as e:
            self.error_handler.log_error(e, "System info drawing")

    def _show_help(self):
        """Show keyboard shortcuts"""
        print("\n" + "="*50)
        print("⌨️  KEYBOARD SHORTCUTS")
        print("="*50)
        print("P - Performance report")
        print("C - Cache statistics")
        print("M - Memory statistics")
        print("R - Reset all users")
        print("S - Scheduler information")
        print("E - Manual end-of-day reset")
        print("I - Camera information")
        print("H - Show this help")
        print("ESC - Exit system")
        print("="*50)

    def draw_current_users(self, frame, current_time):
        """Joriy foydalanuvchilarni ko'rsatish"""
        y_offset = 30
        cv2.putText(frame, "Hozir ichkarida:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        for i, (user, entry_time) in enumerate(self.face_system.current_users.items()):
            y_offset += 25
            duration = current_time - entry_time
            duration_str = str(duration).split('.')[0]
            text = f"- {user}: {duration_str}"
            cv2.putText(frame, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

def main():
    """Asosiy funksiya - Optimized startup"""
    print("🚀 Professional Face Recognition System ishga tushmoqda...")
    startup_start = time.time()
    
    # Professional face system yaratish
    face_system = FaceRecognitionSystem()
    
    # Scheduler sozlash va ishga tushirish
    face_system.scheduler.setup_daily_tasks("23:59")  # Kun oxiri 23:59 da reset
    face_system.scheduler.start_scheduler()
    
    print("⏰ Avtomatik kun oxiri reset sozlandi (23:59)")
    
    # Startup performance
    startup_time = time.time() - startup_start
    print(f"⚡ Tizim {startup_time:.2f} soniyada ishga tushdi")
    
    # Performance report
    face_system.performance_monitor.print_performance_report()
    
    # Web app yaratish
    web_app = create_web_app(face_system)
    
    # Web server thread
    def run_web_server():
        web_app.run(host='0.0.0.0', port=face_system.data_manager.config['web_port'], debug=False)
    
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    print(f"🌐 Professional web server ishga tushdi: http://localhost:{face_system.data_manager.config['web_port']}")
    
    # Professional kamera monitoring boshlash
    camera_monitor = CameraMonitor(face_system)
    
    try:
        camera_monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n👋 Professional tizim to'xtatilmoqda...")
        face_system.is_running = False
        
        # Scheduler to'xtatish
        face_system.scheduler.stop_scheduler()
        
        # Sessiyani to'g'ri tugash
        face_system.end_session()
        
        print("✅ Tizim to'liq to'xtatildi")

if __name__ == "__main__":
    main()