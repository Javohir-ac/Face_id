"""
Professional Face Recognition tizimi - face_recognition kutubxonasi + MongoDB + Cache + Memory + Fast Search
"""
import cv2
import os
import numpy as np
import pickle
import json
import time
import face_recognition
from datetime import datetime
from pathlib import Path
from .data_manager import DataManager
from .mongodb_manager import MongoDBManager
from .cache_manager import get_cache_manager
from .memory_optimizer import get_memory_optimizer
from .fast_search import get_fast_search
from .performance_monitor import get_performance_monitor
from .scheduler import get_scheduler
from .persistent_state_manager import get_persistent_state_manager

class FaceRecognitionSystem:
    def __init__(self):
        self.data_manager = DataManager()
        
        # STARTUP CHECK - Oldingi sessiya tekshiruvi
        self.check_previous_session()
        
        # Memory Optimizer - Performance boost
        self.memory_optimizer = get_memory_optimizer()
        print("🧠 Memory Optimizer aktiv")
        
        # Cache Manager - Performance boost
        self.cache_manager = get_cache_manager()
        print("🚀 Cache Manager aktiv")
        
        # Fast Search - Algorithm optimization
        self.fast_search = get_fast_search()
        print("⚡ Fast Search aktiv")
        
        # Performance Monitor - System monitoring
        self.performance_monitor = get_performance_monitor()
        print("📊 Performance Monitor aktiv")
        
        # Scheduler - Avtomatik vazifalar
        self.scheduler = get_scheduler(self)
        print("⏰ Scheduler aktiv")
        
        # Persistent State Manager - Robust state management
        self.persistent_state = get_persistent_state_manager(self)
        print("🔄 Persistent State Manager aktiv")
        
        # MongoDB integration - hybrid approach
        try:
            self.mongodb_manager = MongoDBManager()
            self.use_mongodb = True
            print("🗄️  MongoDB integration aktiv")
        except Exception as e:
            print(f"⚠️  MongoDB ulanish xatosi: {e}")
            print("📁 JSON fayllar bilan davom etiladi")
            self.mongodb_manager = None
            self.use_mongodb = False
        
        self.setup_face_recognition()
        
        # Tizim holati
        self.is_running = False
        self.current_users = {}
        self.current_users_file = 'current_users.json'
        
        # Oldingi holatni yuklash - Robust recovery
        self.load_current_users()
        
        # Auto-save boshlash
        self.persistent_state.start_auto_save()
        
        # Yangi sessiya boshlash
        self.start_new_session()
        
        # Memory optimization
        self.memory_optimizer.optimize_system_memory()
        
        print("🚀 Professional Face Recognition System tayyor!")
    
    def setup_face_recognition(self):
        """Professional yuz tanish tizimini sozlash"""
        self.encodings_file = 'face_encodings.pkl'
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_face_encodings()
        
        if len(self.known_face_names) == 0:
            self.auto_train_faces()
        
        print(f"🎯 Professional tizim tayyor! {len(self.known_face_names)} ta encoding")
    
    def load_face_encodings(self):
        """Professional yuz encodinglarini yuklash - Cache First Strategy"""
        # Step 1: Cache dan yuklashga harakat
        print("🔍 Cache dan encodinglarni qidiryapti...")
        cached_data = self.cache_manager.get_encodings()

        if cached_data is not None:
            encodings, names = cached_data
            self.known_face_encodings = encodings
            self.known_face_names = names
            
            # Fast Search ni train qilish
            self.fast_search.train(encodings, names)
            
            unique_users = len(set(names))
            print(f"⚡ Cache HIT: {len(encodings)} ta encoding, {unique_users} ta foydalanuvchi")
            return

        print("💾 Cache MISS - ma'lumotlarni yuklash...")

        # Step 2: MongoDB dan yuklash
        if self.use_mongodb and self.mongodb_manager:
            try:
                encodings, names = self.mongodb_manager.get_all_encodings()
                if encodings:
                    # Memory optimization
                    optimized_encodings = self.memory_optimizer.optimize_numpy_arrays(encodings)
                    self.known_face_encodings = optimized_encodings
                    self.known_face_names = names

                    # Cache ga saqlash
                    self.cache_manager.put_encodings(optimized_encodings, names)
                    
                    # Fast Search ni train qilish
                    self.fast_search.train(optimized_encodings, names)

                    unique_users = len(set(names))
                    self.data_manager.log_system_event('INFO', f"MongoDB: {len(encodings)} ta encoding, {unique_users} ta foydalanuvchi yuklandi")
                    print("💾 Ma'lumotlar cache ga saqlandi")
                    return
                else:
                    print("📁 MongoDB bo'sh, JSON fayldan yuklash...")
            except Exception as e:
                print(f"⚠️  MongoDB yuklashda xatolik: {e}")
                print("📁 JSON fayldan yuklash...")

        # Step 3: JSON fallback
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    raw_encodings = data['encodings']
                    
                    # Memory optimization
                    optimized_encodings = self.memory_optimizer.optimize_numpy_arrays(raw_encodings)
                    self.known_face_encodings = optimized_encodings
                    self.known_face_names = data['names']

                # Cache ga saqlash
                self.cache_manager.put_encodings(self.known_face_encodings, self.known_face_names)
                
                # Fast Search ni train qilish
                self.fast_search.train(self.known_face_encodings, self.known_face_names)

                unique_users = len(set(self.known_face_names))
                self.data_manager.log_system_event('INFO', f"JSON: {len(self.known_face_encodings)} ta encoding, {unique_users} ta foydalanuvchi yuklandi")
                print("💾 JSON ma'lumotlari cache ga saqlandi")
            except Exception as e:
                self.data_manager.log_system_event('ERROR', f"JSON encodinglarni yuklashda xatolik: {e}")
        else:
            # Step 4: face_data papkasidan yaratish
            if os.path.exists('face_data'):
                print("📁 face_data papkasidan encodinglar yaratilmoqda...")
                self.auto_train_faces()
            else:
                self.data_manager.log_system_event('WARNING', "Hech qanday encoding fayli yoki face_data papkasi topilmadi")
    
    def auto_train_faces(self):
        """Professional avtomatik yuz o'qitish - MongoDB/JSON hybrid"""
        self.data_manager.log_system_event('INFO', "Professional yuz o'qitish boshlandi...")
        
        if not os.path.exists('face_data'):
            self.data_manager.log_system_event('WARNING', "face_data papkasi topilmadi")
            return
        
        encodings = []
        names = []
        
        for user_folder in os.listdir('face_data'):
            user_path = os.path.join('face_data', user_folder)
            if not os.path.isdir(user_path):
                continue
            
            user_encodings = []
            image_count = 0
            
            # MongoDB ga user qo'shish
            if self.use_mongodb and self.mongodb_manager:
                self.mongodb_manager.add_user(user_folder)
            
            for image_file in os.listdir(user_path):
                if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_path = os.path.join(user_path, image_file)
                    encoding = self.create_face_encoding(image_path)
                    
                    if encoding is not None:
                        user_encodings.append(encoding)
                        image_count += 1
                        
                        # MongoDB ga encoding saqlash
                        if self.use_mongodb and self.mongodb_manager:
                            # Direction aniqlash
                            direction = None
                            if '_front' in image_file.lower():
                                direction = 'FRONT'
                            elif '_left' in image_file.lower():
                                direction = 'LEFT'
                            elif '_right' in image_file.lower():
                                direction = 'RIGHT'
                            
                            self.mongodb_manager.save_encoding(user_folder, encoding, image_path, direction)
            
            if user_encodings:
                # Professional: har bir rasmning encodingini alohida saqlash
                for encoding in user_encodings:
                    encodings.append(encoding)
                    names.append(user_folder)
                
                self.data_manager.add_user(user_folder)
                self.data_manager.log_system_event('INFO', f"{user_folder}: {image_count} ta professional encoding yaratildi")
        
        self.known_face_encodings = encodings
        self.known_face_names = names
        
        # JSON backup saqlash
        if encodings:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump({'encodings': encodings, 'names': names}, f)
            
            unique_users = len(set(names))
            self.data_manager.log_system_event('INFO', f"Jami {len(encodings)} ta encoding, {unique_users} ta foydalanuvchi saqlandi")
        else:
            self.data_manager.log_system_event('WARNING', "Hech qanday yaroqli yuz rasmi topilmadi")
    
    def create_face_encoding(self, image_path):
        """Professional face encoding yaratish"""
        try:
            # Professional face_recognition kutubxonasi
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                self.data_manager.log_system_event('WARNING', f"Yuz topilmadi: {image_path}")
                return None
            
            # Birinchi (eng katta) yuzni olish
            encoding = face_encodings[0]
            
            return encoding
            
        except Exception as e:
            self.data_manager.log_system_event('ERROR', f"Professional encoding xatoligi {image_path}: {e}")
            return None
    
    def recognize_face(self, face_encoding):
        """Professional yuz tanish algoritmi - Fast Search + Voting system"""
        if len(self.known_face_encodings) == 0:
            return "Unknown", 0.0
        
        # Performance monitoring start
        start_time = time.time()
        
        try:
            # Fast Search algoritmi ishlatish
            if self.fast_search.is_trained:
                name, confidence = self.fast_search.search(face_encoding, threshold=0.55)
                
                # Performance monitoring end
                recognition_time = time.time() - start_time
                self.performance_monitor.record_recognition_time(recognition_time)
                
                return name, confidence
            
            # Fallback - original voting system
            distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            # Threshold - muvozanatlashtirilgan
            distance_threshold = 0.55
            
            # Voting system - har bir nom uchun ovozlar
            votes = {}
            confidences = {}
            
            for i, distance in enumerate(distances):
                if distance < distance_threshold:
                    name = self.known_face_names[i]
                    confidence = 1.0 - distance
                    
                    if name not in votes:
                        votes[name] = 0
                        confidences[name] = []
                    
                    votes[name] += 1
                    confidences[name].append(confidence)
            
            # Agar hech kim ovoz olmasa
            if not votes:
                min_distance = np.min(distances)
                result = "Unknown", 1.0 - min_distance
            else:
                # Handle tie situation in fallback voting system
                max_votes = max(votes.values())
                tied_candidates = [name for name, vote_count in votes.items() if vote_count == max_votes]
                
                if len(tied_candidates) == 1:
                    # Clear winner
                    best_name = tied_candidates[0]
                    avg_confidence = np.mean(confidences[best_name])
                else:
                    # TIE situation - choose by highest average confidence
                    best_name = max(tied_candidates, key=lambda name: np.mean(confidences[name]))
                    avg_confidence = np.mean(confidences[best_name])
                    print(f"🤝 TIE resolved (fallback): {tied_candidates} -> {best_name} (confidence: {avg_confidence:.3f})")
                
                # Minimum ovoz va confidence tekshiruvi
                if votes[best_name] >= 2 and avg_confidence >= 0.5:  # Kamida 2 ta ovoz va 50% confidence
                    result = best_name, avg_confidence
                else:
                    result = "Unknown", avg_confidence if avg_confidence else 0.0
            
            # Performance monitoring end
            recognition_time = time.time() - start_time
            self.performance_monitor.record_recognition_time(recognition_time)
            
            return result
                
        except Exception as e:
            self.data_manager.log_system_event('ERROR', f"Professional yuz tanishda xatolik: {e}")
            
            # Performance monitoring end (even on error)
            recognition_time = time.time() - start_time
            self.performance_monitor.record_recognition_time(recognition_time)
            
            return "Unknown", 0.0
    
    def detect_zone(self, face_x, face_w, frame_width):
        """Zonani aniqlash"""
        face_center = face_x + face_w // 2
        relative_pos = face_center / frame_width
        
        zones = self.data_manager.config['zones']
        
        if relative_pos < zones['entry_zone']['x'] + zones['entry_zone']['width']:
            return 'entry'
        elif relative_pos > zones['exit_zone']['x']:
            return 'exit'
        else:
            return 'neutral'
    
    def get_next_expected_action(self, user_name):
        """Keyingi kutilayotgan action - AQLLI TOGGLE + Current State"""
        # Avval current_users holatini tekshirish
        if user_name in self.current_users:
            # Agar user hozir ichkarida bo'lsa, keyingi action EXIT bo'lishi kerak
            return "exit"
        else:
            # Agar user hozir tashqarida bo'lsa, keyingi action ENTRY bo'lishi kerak
            return "entry"
    
    def process_user_action(self, user_name, confidence):
        """Foydalanuvchi harakatini qayta ishlash - AQLLI TOGGLE + MongoDB"""
        current_time = datetime.now()
        expected_action = self.get_next_expected_action(user_name)
        
        # Ignore tekshiruvi
        if self.data_manager.should_ignore_action(user_name, expected_action):
            return
        
        if expected_action == 'entry':
            # KELDI action - faqat agar ichkarida bo'lmasa
            if user_name not in self.current_users:
                self.current_users[user_name] = current_time
                self.save_current_users()  # Holatni saqlash
                
                # MongoDB va JSON ga yozish
                if self.use_mongodb and self.mongodb_manager:
                    self.mongodb_manager.log_attendance(user_name, 'entry', 'camera', confidence)
                self.data_manager.log_attendance(user_name, 'entry', 'camera', confidence)
                self.data_manager.log_system_event('INFO', f"{user_name} keldi (professional confidence: {confidence:.2f})")
                
        elif expected_action == 'exit':
            # KETDI action - faqat agar ichkarida bo'lsa
            if user_name in self.current_users:
                entry_time = self.current_users[user_name]
                duration = current_time - entry_time
                duration_minutes = int(duration.total_seconds() / 60)
                
                if user_name in self.data_manager.users_data:
                    self.data_manager.users_data[user_name]['total_time_minutes'] += duration_minutes
                    self.data_manager.save_users_data()
                    
                    # MongoDB ga statistika yangilash
                    if self.use_mongodb and self.mongodb_manager:
                        self.mongodb_manager.update_user_stats(
                            user_name, 
                            total_time_minutes=self.data_manager.users_data[user_name]['total_time_minutes']
                        )
                
                del self.current_users[user_name]
                self.save_current_users()  # Holatni saqlash
                
                # MongoDB va JSON ga yozish
                if self.use_mongodb and self.mongodb_manager:
                    self.mongodb_manager.log_attendance(user_name, 'exit', 'camera', confidence)
                self.data_manager.log_attendance(user_name, 'exit', 'camera', confidence)
                self.data_manager.log_system_event('INFO', f"{user_name} ketdi (professional confidence: {confidence:.2f}, davomiyligi: {duration_minutes} daqiqa)")
    
    def force_exit_user(self, user_name, reason="manual"):
        """Foydalanuvchini majburiy chiqarish"""
        if user_name in self.current_users:
            current_time = datetime.now()
            entry_time = self.current_users[user_name]
            duration = current_time - entry_time
            duration_minutes = int(duration.total_seconds() / 60)
            
            if user_name in self.data_manager.users_data:
                self.data_manager.users_data[user_name]['total_time_minutes'] += duration_minutes
                self.data_manager.save_users_data()
            
            del self.current_users[user_name]
            self.save_current_users()  # Holatni saqlash
            self.data_manager.log_attendance(user_name, 'exit', reason, 1.0)
            self.data_manager.log_system_event('INFO', f"{user_name} majburiy chiqarildi ({reason})")
            return True
        return False
    def reset_all_users(self, reason="system_restart"):
        """Barcha userlarni tashqariga chiqarish (system restart)"""
        if not self.current_users:
            print("✅ Hech kim ichkarida emas")
            return 0

        users_to_exit = list(self.current_users.keys())
        exit_count = 0

        print(f"🔄 System reset: {len(users_to_exit)} ta user chiqarilmoqda...")

        for user_name in users_to_exit:
            if self.force_exit_user(user_name, reason):
                exit_count += 1
                print(f"   🚪 {user_name} chiqarildi")

        print(f"✅ System reset tugallandi: {exit_count} ta user chiqarildi")
        self.data_manager.log_system_event('INFO', f"System reset: {exit_count} ta user majburiy chiqarildi")

        return exit_count
    
    def get_user_stats(self):
        """Foydalanuvchilar statistikasi"""
        stats = []
        for user_name, user_data in self.data_manager.users_data.items():
            if user_data['is_active']:
                today_summary = self.data_manager.get_daily_summary()
                today_entries = 0
                if user_name in today_summary['users']:
                    today_entries = len(today_summary['users'][user_name]['sessions'])
                
                is_inside = user_name in self.current_users
                current_duration = 0
                if is_inside:
                    current_duration = int((datetime.now() - self.current_users[user_name]).total_seconds() / 60)
                
                stats.append({
                    'name': user_name,
                    'is_inside': is_inside,
                    'current_duration_minutes': current_duration,
                    'today_entries': today_entries,
                    'total_entries': user_data.get('total_entries', 0),
                    'total_time_minutes': user_data.get('total_time_minutes', 0)
                })
        
        return stats
    
    def load_current_users(self):
        """Joriy foydalanuvchilar holatini yuklash - Robust recovery"""
        try:
            # Persistent State Manager orqali robust recovery
            if hasattr(self, 'persistent_state'):
                if self.persistent_state.load_complete_state():
                    return
            
            # Fallback: Avval MongoDB dan yuklash
            if self.use_mongodb and self.mongodb_manager:
                try:
                    mongodb_users = self.mongodb_manager.load_system_state()
                    if mongodb_users:
                        self.current_users = mongodb_users
                        self.data_manager.log_system_event('INFO', f"MongoDB: {len(self.current_users)} ta foydalanuvchi ichkarida")
                        for user_name in self.current_users.keys():
                            self.data_manager.log_system_event('INFO', f"{user_name} - MongoDB sessiya davom etmoqda")
                        return
                except Exception as e:
                    print(f"⚠️  MongoDB holatni yuklashda xatolik: {e}")
            
            # JSON fallback
            if os.path.exists(self.current_users_file):
                with open(self.current_users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # String formatdagi vaqtni datetime ga aylantirish
                    for user_name, entry_time_str in data.items():
                        self.current_users[user_name] = datetime.fromisoformat(entry_time_str)
                
                if self.current_users:
                    self.data_manager.log_system_event('INFO', f"JSON: {len(self.current_users)} ta foydalanuvchi ichkarida")
                    for user_name in self.current_users.keys():
                        self.data_manager.log_system_event('INFO', f"{user_name} - JSON sessiya davom etmoqda")
        except Exception as e:
            self.data_manager.log_system_event('ERROR', f"Current users yuklashda xatolik: {e}")
            self.current_users = {}
    
    def save_current_users(self):
        """Joriy foydalanuvchilar holatini saqlash - Robust persistence"""
        try:
            # Persistent State Manager orqali saqlash (avtomatik)
            # Bu metod legacy compatibility uchun saqlanadi
            
            # MongoDB ga saqlash
            if self.use_mongodb and self.mongodb_manager:
                try:
                    self.mongodb_manager.save_system_state(self.current_users)
                except Exception as e:
                    print(f"⚠️  MongoDB holatni saqlashda xatolik: {e}")
            
            # JSON backup
            data = {}
            for user_name, entry_time in self.current_users.items():
                data[user_name] = entry_time.isoformat()
            
            with open(self.current_users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Persistent state manager ham trigger qilish
            if hasattr(self, 'persistent_state'):
                # Force save qilmaslik, auto-save ishlaydi
                pass
                
        except Exception as e:
            self.data_manager.log_system_event('ERROR', f"Current users saqlashda xatolik: {e}")
    def migrate_to_mongodb(self):
        """JSON ma'lumotlarni MongoDB ga ko'chirish"""
        if not self.use_mongodb or not self.mongodb_manager:
            print("❌ MongoDB mavjud emas")
            return False
        
        try:
            print("🔄 JSON dan MongoDB ga migration boshlandi...")
            
            # Data manager orqali migration
            success = self.mongodb_manager.migrate_from_json(self.data_manager)
            
            if success:
                print("✅ Migration muvaffaqiyatli tugallandi!")
                
                # Encodinglarni ham ko'chirish
                if os.path.exists(self.encodings_file):
                    print("🔄 Encodinglarni ko'chirish...")
                    with open(self.encodings_file, 'rb') as f:
                        data = pickle.load(f)
                        encodings = data['encodings']
                        names = data['names']
                    
                    for i, (encoding, name) in enumerate(zip(encodings, names)):
                        self.mongodb_manager.save_encoding(name, encoding, f"migrated_{i}.jpg")
                    
                    print(f"✅ {len(encodings)} ta encoding ko'chirildi!")
                
                return True
            else:
                print("❌ Migration xatosi")
                return False
                
        except Exception as e:
            print(f"❌ Migration xatosi: {e}")
            return False
    def check_previous_session(self):
        """Oldingi sessiya tekshiruvi va avtomatik tozalash"""
        try:
            print("🔍 Oldingi sessiya tekshirilmoqda...")

            # Session tracking fayli
            session_file = 'system_session.json'
            current_time = datetime.now()

            # Oldingi sessiya ma'lumotlari
            previous_session = None
            if os.path.exists(session_file):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        previous_session = json.load(f)
                except:
                    pass

            # Current users tekshirish
            stuck_users = []
            if os.path.exists('current_users.json'):
                try:
                    with open('current_users.json', 'r', encoding='utf-8') as f:
                        current_users_data = json.load(f)
                        if current_users_data:
                            stuck_users = list(current_users_data.keys())
                except:
                    pass

            # Agar oldingi sessiya noto'g'ri tugagan bo'lsa
            improper_shutdown = False
            if previous_session:
                last_start = datetime.fromisoformat(previous_session.get('start_time', current_time.isoformat()))
                last_status = previous_session.get('status', 'unknown')

                # Agar oldingi sessiya "running" holatida qolgan bo'lsa
                if last_status == 'running':
                    time_diff = current_time - last_start
                    if time_diff.total_seconds() > 300:  # 5 daqiqadan ko'p
                        improper_shutdown = True

            # Avtomatik tozalash kerakmi?
            need_cleanup = stuck_users or improper_shutdown

            if need_cleanup:
                print("⚠️  OLDINGI SESSIYA NOTO'G'RI TUGAGAN!")
                print(f"   👥 Ichkarida qolgan userlar: {len(stuck_users)}")
                if stuck_users:
                    print(f"   📝 Userlar: {', '.join(stuck_users)}")

                # Avtomatik tozalash
                self.auto_cleanup_stuck_users(stuck_users)
            else:
                print("✅ Oldingi sessiya to'g'ri tugagan")

            # Yangi sessiya boshlash
            self.start_new_session()

        except Exception as e:
            print(f"❌ Session check error: {e}")
            # Xatolik bo'lsa ham yangi sessiya boshlash
            self.start_new_session()

    def auto_cleanup_stuck_users(self, stuck_users: list):
        """Qolib ketgan userlarni avtomatik tozalash"""
        try:
            print("🧹 AVTOMATIK TOZALASH BOSHLANDI...")

            cleanup_count = 0
            current_time = datetime.now()

            # Current users faylini yuklash
            if os.path.exists('current_users.json'):
                with open('current_users.json', 'r', encoding='utf-8') as f:
                    current_users_data = json.load(f)

                # Har bir stuck user uchun
                for user_name in stuck_users:
                    if user_name in current_users_data:
                        entry_time_str = current_users_data[user_name]
                        entry_time = datetime.fromisoformat(entry_time_str)

                        # Chiqish vaqtini hisoblash (oldingi sessiya tugash vaqti)
                        exit_time = current_time

                        # Attendance ga yozish
                        self.data_manager.log_attendance(user_name, "exit", exit_time, reason="auto_cleanup")

                        cleanup_count += 1
                        print(f"   🚪 {user_name} - avtomatik chiqarildi")

                # Current users faylini tozalash
                with open('current_users.json', 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=2)

            print(f"✅ Avtomatik tozalash tugallandi: {cleanup_count} ta user")

            # Log yozish
            self.data_manager.log_system_event(
                'INFO',
                f"Auto cleanup: {cleanup_count} stuck users cleaned up"
            )

        except Exception as e:
            print(f"❌ Auto cleanup error: {e}")

    def start_new_session(self):
        """Yangi sessiya boshlash - Robust startup"""
        try:
            self.session_start_time = datetime.now().isoformat()
            
            session_data = {
                'start_time': self.session_start_time,
                'status': 'running',
                'pid': os.getpid(),
                'robust_mode': True,
                'auto_save_enabled': True
            }

            with open('system_session.json', 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)

            # Statistics tracking
            self.total_recognitions = 0
            self.successful_recognitions = 0
            self.failed_recognitions = 0
            self.start_time = time.time()

            print("🚀 Robust sessiya boshlandi")

        except Exception as e:
            print(f"❌ Session start error: {e}")

    def end_session(self):
        """Sessiyani to'g'ri tugash - Robust shutdown"""
        try:
            print("🔄 Robust session shutdown boshlandi...")
            
            # 1. Auto-save to'xtatish va oxirgi marta saqlash
            if hasattr(self, 'persistent_state'):
                self.persistent_state.force_save_state()
            
            # 2. Barcha userlarni chiqarish
            if hasattr(self, 'current_users') and self.current_users:
                exit_count = self.reset_all_users("session_end")
                print(f"🚪 Sessiya tugashi: {exit_count} ta user chiqarildi")

            # 3. Scheduler to'xtatish
            if hasattr(self, 'scheduler'):
                self.scheduler.stop_scheduler()

            # 4. Session faylini yangilash
            session_data = {
                'start_time': getattr(self, 'session_start_time', datetime.now().isoformat()),
                'status': 'stopped',
                'end_time': datetime.now().isoformat(),
                'graceful_shutdown': True
            }

            with open('system_session.json', 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)

            print("✅ Robust session shutdown tugallandi")

        except Exception as e:
            print(f"❌ Session end error: {e}")
            # Emergency save
            try:
                if hasattr(self, 'persistent_state'):
                    self.persistent_state.force_save_state()
            except:
                pass
