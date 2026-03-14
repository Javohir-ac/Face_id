#!/usr/bin/env python3
"""
Tez yuz qo'shish - OpenCV + face_recognition + MongoDB
"""
import cv2
import os
import sys
import time
import numpy as np
import face_recognition
from face_system.core.mongodb_manager import MongoDBManager

def create_face_encoding(image_path):
    """Professional yuz encoding yaratish"""
    try:
        # Professional face_recognition kutubxonasi
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            print(f"❌ Yuz topilmadi: {image_path}")
            return None
        
        # Birinchi yuzni olish
        encoding = face_encodings[0]
        print(f"✅ Professional encoding yaratildi: {len(encoding)} dimensional")
        return encoding
        
    except Exception as e:
        print(f"❌ Encoding yaratishda xatolik: {e}")
        return None

def load_existing_encodings():
    """Mavjud professional yuz encodinglarini yuklash"""
    encodings = []
    names = []
    
    if not os.path.exists("face_data"):
        return encodings, names
    
    print("🔍 Mavjud yuzlarni professional usul bilan yuklayapman...")
    
    for user_folder in os.listdir("face_data"):
        user_path = os.path.join("face_data", user_folder)
        if not os.path.isdir(user_path):
            continue
        
        user_encodings = []
        for image_file in os.listdir(user_path):
            if image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(user_path, image_file)
                encoding = create_face_encoding(image_path)
                if encoding is not None:
                    user_encodings.append(encoding)
        
        if user_encodings:
            # Har bir rasmning encodingini alohida saqlash
            for encoding in user_encodings:
                encodings.append(encoding)
                names.append(user_folder)
            print(f"📋 {user_folder}: {len(user_encodings)} ta professional encoding yuklandi")
    
    return encodings, names

def check_face_similarity(image_path, existing_encodings, existing_names, threshold=0.5):
    """Professional yuz taqqoslash - yumshoqroq threshold"""
    new_encoding = create_face_encoding(image_path)
    if new_encoding is None:
        print("❌ Yangi encoding yaratilmadi")
        return False, None, 1.0
    
    if len(existing_encodings) == 0:
        return False, None, 1.0
    
    # Professional face_distance
    distances = face_recognition.face_distance(existing_encodings, new_encoding)
    
    # Eng yaqin masofani topish
    min_distance = np.min(distances)
    best_match_index = np.argmin(distances)
    
    print(f"   Professional masofa: {min_distance:.3f}")
    print(f"   Threshold: {threshold}")
    
    # Agar masofa threshold dan kichik bo'lsa, o'xshash deb hisoblaymiz
    if min_distance < threshold:
        similar_name = existing_names[best_match_index]
        return True, similar_name, min_distance
    else:
        return False, None, min_distance

def add_new_face():
    """Tez yuz qo'shish + MongoDB integration"""
    # MongoDB Manager initialization
    try:
        mongodb_manager = MongoDBManager()
        use_mongodb = True
        print("🗄️  MongoDB integration aktiv")
    except Exception as e:
        print(f"⚠️  MongoDB ulanish xatosi: {e}")
        print("📁 Faqat lokal fayllar bilan davom etiladi")
        mongodb_manager = None
        use_mongodb = False
    
    # Mavjud yuz encodinglarini yuklash
    print("� Professional tizim bilan mavjud yuzlarni tekshirmoqda...")
    existing_encodings, existing_names = load_existing_encodings()
    unique_users = list(set(existing_names))
    print(f"📋 {len(unique_users)} ta mavjud foydalanuvchi: {unique_users}")
    
    # Foydalanuvchi nomini so'rash
    user_name = input("Foydalanuvchi nomini kiriting: ").strip()
    if not user_name:
        print("❌ Nom kiritilmadi!")
        return
    
    # MUHIM: Avval barcha mavjud yuzlar bilan taqqoslash
    print(f"🔍 {user_name} nomini tekshirmoqda...")
    
    # Test rasmi olish - birinchi yuzni olish
    print("📸 Test rasmi uchun kameraga qarang...")
    cap_test = cv2.VideoCapture(0)
    if not cap_test.isOpened():
        print("❌ Test uchun kamera ochilmadi!")
        return
    
    test_encoding = None
    test_attempts = 0
    max_test_attempts = 30  # 30 ta urinish
    
    while test_encoding is None and test_attempts < max_test_attempts:
        ret, frame = cap_test.read()
        if ret:
            frame = cv2.flip(frame, 1)
            
            # Test rasmi saqlash
            test_filename = f"temp_test_{user_name}.jpg"
            cv2.imwrite(test_filename, frame)
            
            # Encoding yaratish
            test_encoding = create_face_encoding(test_filename)
            
            if test_encoding is not None:
                print("✅ Test encoding yaratildi!")
                break
            else:
                test_attempts += 1
                cv2.putText(frame, f"Yuz aniqlanmadi... {test_attempts}/{max_test_attempts}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame, "Kameraga to'g'ri qarang", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Test Rasmi', frame)
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break
    
    cap_test.release()
    cv2.destroyAllWindows()
    
    # Test faylini o'chirish
    if os.path.exists(test_filename):
        os.remove(test_filename)
    
    if test_encoding is None:
        print("❌ Test rasmi uchun yuz aniqlanmadi!")
        return
    
    # Mavjud barcha yuzlar bilan taqqoslash
    if len(existing_encodings) > 0:
        distances = face_recognition.face_distance(existing_encodings, test_encoding)
        min_distance = np.min(distances)
        best_match_index = np.argmin(distances)
        
        # Qattiq threshold - 0.4 dan kichik bo'lsa bir xil odam
        if min_distance < 0.4:
            existing_user = existing_names[best_match_index]
            print(f"🚫 XATOLIK: Bu yuz allaqachon {existing_user} nomi bilan ro'yxatdan o'tgan!")
            print(f"   Masofa: {min_distance:.3f} (0.4 dan kichik)")
            print(f"   Bir xil odamni ikki xil nom bilan ro'yxatdan o'tkazib bo'lmaydi!")
            
            choice = input(f"Davom etishni xohlaysizmi? Bu xavfli! (yes/no): ").strip().lower()
            if choice != 'yes':
                print("❌ Ro'yxatdan o'tish bekor qilindi!")
                return
            else:
                print("⚠️  Xavfli rejimda davom etilmoqda...")
        else:
            print(f"✅ Yangi yuz tasdiqlandi! Eng yaqin masofa: {min_distance:.3f}")
    else:
        print("✅ Birinchi foydalanuvchi - taqqoslash shart emas")
    
    # Papka yaratish
    user_dir = f"face_data/{user_name}"
    
    # Agar avval rasmga olingan bo'lsa
    if os.path.exists(user_dir) and os.listdir(user_dir):
        print(f"⚠️  {user_name} uchun rasmlar allaqachon mavjud!")
        choice = input("Qaytadan rasmga olishni xohlaysizmi? (y/n): ").strip().lower()
        if choice != 'y':
            print("❌ Bekor qilindi!")
            return
        else:
            # Eski rasmlarni o'chirish
            for file in os.listdir(user_dir):
                os.remove(os.path.join(user_dir, file))
            print("�️  Eski rasmlar o'chirildi!")
    
    os.makedirs(user_dir, exist_ok=True)
    
    # MongoDB ga user qo'shish
    if use_mongodb and mongodb_manager:
        try:
            mongodb_manager.add_user(user_name)
            print(f"✅ {user_name} MongoDB ga qo'shildi")
        except Exception as e:
            print(f"⚠️  MongoDB user qo'shishda xatolik: {e}")
    
    # Kamerani ochish
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Kamera ochilmadi!")
        return
    
    print(f"� {user_name} uchun tez avtomatik yuz rasmlarini olish...")
    print("Tez avtomatik rejim:")
    print("🎯 5 ta TO'G'RI qaragan (FRONT) - kameraga to'g'ri qarang")
    print("🎯 5 ta O'NGA qaragan (RIGHT) - boshingizni o'nga burish")  
    print("🎯 5 ta CHAPGA qaragan (LEFT) - boshingizni chapga burish")
    print("💡 Yo'nalish o'zgartirish uchun boshingizni sekin burib turing")
    print("SPACE - manual rasm olish, ESC - chiqish")
    
    # OpenCV yuz aniqlash - tezroq + profil yuzlar uchun
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
    
    # Mavjud rasmlarni hisoblash
    existing_images = []
    if os.path.exists(user_dir):
        existing_images = [f for f in os.listdir(user_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    direction_counts = {"FRONT": 0, "RIGHT": 0, "LEFT": 0}
    
    # Mavjud rasmlarni hisoblash
    for img in existing_images:
        img_lower = img.lower()
        if '_front.' in img_lower or '_front_' in img_lower:
            direction_counts["FRONT"] += 1
        elif '_right.' in img_lower or '_right_' in img_lower:
            direction_counts["RIGHT"] += 1
        elif '_left.' in img_lower or '_left_' in img_lower:
            direction_counts["LEFT"] += 1
    
    total_count = sum(direction_counts.values())
    last_capture_time = 0
    capture_interval = 0.8  # Tezroq - 0.8 soniya
    
    print(f"📊 Mavjud rasmlar: FRONT={direction_counts['FRONT']}, LEFT={direction_counts['LEFT']}, RIGHT={direction_counts['RIGHT']}")
    print(f"📊 Jami mavjud: {total_count}/15")
    
    while total_count < 15:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Oynani aylantirish
        frame = cv2.flip(frame, 1)
        
        current_time = time.time()
        
        # Tez yuz aniqlash - OpenCV (har 3-frameda bir marta)
        if not hasattr(add_new_face, 'frame_skip_counter'):
            add_new_face.frame_skip_counter = 0
        add_new_face.frame_skip_counter += 1
        
        if add_new_face.frame_skip_counter % 3 != 0:  # Har 3-frameda bir marta
            # Faqat ramka chizish, yuz aniqlash emas
            cv2.putText(frame, f"Jami: {total_count}/15", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"FRONT: {direction_counts['FRONT']}/5", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"RIGHT: {direction_counts['RIGHT']}/5", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            cv2.putText(frame, f"LEFT: {direction_counts['LEFT']}/5", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, "Tez rejim - SPACE: manual, ESC: chiqish", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow('Tez Yuz Qo\'shish', frame)
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Frontal va profil yuzlarni aniqlash
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(80, 80))
        profile_faces = profile_cascade.detectMultiScale(gray, 1.1, 4, minSize=(80, 80))
        
        # Barcha yuzlarni birlashtirish
        all_faces = list(faces)
        for pf in profile_faces:
            all_faces.append(pf)
        
        detected_direction = "UNKNOWN"
        
        # Har bir yuzni qayta ishlash
        for (x, y, w, h) in all_faces:
            # Yaxshilangan yo'nalish aniqlash
            face_center_x = x + w // 2
            frame_center_x = frame.shape[1] // 2
            frame_width = frame.shape[1]
            
            # Yuz pozitsiyasi
            left_edge = x
            right_edge = x + w
            
            # Sodda va aniq yo'nalish aniqlash
            if left_edge < frame_width * 0.3:  # Chap tomonda
                detected_direction = "RIGHT"  # Chap tomonda bo'lsa o'nga qaragan
                color = (255, 0, 0)  # Ko'k
            elif right_edge > frame_width * 0.7:  # O'ng tomonda  
                detected_direction = "LEFT"   # O'ng tomonda bo'lsa chapga qaragan
                color = (0, 255, 255)  # Sariq
            else:  # Markazda
                detected_direction = "FRONT"  # Markazda bo'lsa to'g'ri qaragan
                color = (0, 255, 0)  # Yashil
            
            # Ramka chizish
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, f"{user_name}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(frame, detected_direction, (x, y+h+25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Debug ma'lumotlari
            debug_text = f"X:{left_edge}-{right_edge}"
            cv2.putText(frame, debug_text, (x, y+h+45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            break  # Faqat birinchi yuzni olish
        
        # Ma'lumot ko'rsatish
        cv2.putText(frame, f"Jami: {total_count}/15", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"FRONT: {direction_counts['FRONT']}/5", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"RIGHT: {direction_counts['RIGHT']}/5", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, f"LEFT: {direction_counts['LEFT']}/5", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, "Tez rejim - SPACE: manual, ESC: chiqish", (10, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Avtomatik rasm olish
        if (len(all_faces) > 0 and detected_direction != "UNKNOWN" and 
            direction_counts[detected_direction] < 5 and
            current_time - last_capture_time > capture_interval):
            
            # Rasmni saqlash
            filename = f"{user_dir}/{user_name}_{total_count+1:03d}_{detected_direction.lower()}.jpg"
            cv2.imwrite(filename, frame)
            
            # Professional taqqoslash - faqat agar mavjud encodinglar bo'lsa
            should_keep = True
            if len(existing_encodings) > 0:
                is_similar, similar_name, distance = check_face_similarity(filename, existing_encodings, existing_names, threshold=0.4)  # Qattiqroq threshold
                print(f"🔍 {detected_direction} rasm taqqoslash: o'xshash={is_similar}, masofa={distance:.3f}")
                
                if is_similar and similar_name != user_name:  # Boshqa odamga o'xshasa
                    print(f"🚫 XATOLIK: {detected_direction} rasm {similar_name} ga o'xshaydi! (masofa: {distance:.3f})")
                    print(f"   Bir xil yuzni ikki xil nom bilan saqlab bo'lmaydi!")
                    os.remove(filename)
                    print(f"🗑️  Xavfli {detected_direction} rasm o'chirildi")
                    should_keep = False
                elif is_similar and similar_name == user_name:
                    print(f"✅ {detected_direction} rasm o'sha odamga tegishli (masofa: {distance:.3f})")
            
            if should_keep:
                print(f"✅ {detected_direction} rasm saqlandi: {filename}")
                
                # Yangi encoding ni ro'yxatga qo'shish
                new_encoding = create_face_encoding(filename)
                if new_encoding is not None:
                    existing_encodings.append(new_encoding)
                    existing_names.append(user_name)
                    
                    # MongoDB ga encoding saqlash
                    if use_mongodb and mongodb_manager:
                        try:
                            mongodb_manager.save_encoding(user_name, new_encoding, filename, detected_direction)
                            print(f"✅ {detected_direction} encoding MongoDB ga saqlandi")
                        except Exception as e:
                            print(f"⚠️  MongoDB encoding saqlashda xatolik: {e}")
                    
                    # Rasmni o'chirish - encoding saqlangandan keyin
                    try:
                        os.remove(filename)
                        print(f"🗑️  {detected_direction} rasm o'chirildi (encoding saqlandi)")
                    except Exception as e:
                        print(f"⚠️  Rasmni o'chirishda xatolik: {e}")
                
                # Hisoblagichlarni yangilash
                direction_counts[detected_direction] += 1
                total_count += 1
                last_capture_time = current_time
        
        # Manual rasm olish
        key = cv2.waitKey(1) & 0xFF
        
        if key == 32:  # SPACE tugmasi
            if len(all_faces) > 0 and detected_direction != "UNKNOWN":
                if direction_counts[detected_direction] < 5:
                    # Rasmni saqlash
                    filename = f"{user_dir}/{user_name}_{total_count+1:03d}_{detected_direction.lower()}.jpg"
                    cv2.imwrite(filename, frame)
                    
                    # Professional taqqoslash
                    should_keep = True
                    if len(existing_encodings) > 0:
                        is_similar, similar_name, distance = check_face_similarity(filename, existing_encodings, existing_names, threshold=0.4)
                        print(f"🔍 Manual {detected_direction} rasm: o'xshash={is_similar}, masofa={distance:.3f}")
                        
                        if is_similar and similar_name != user_name:
                            print(f"🚫 XATOLIK: Manual {detected_direction} rasm {similar_name} ga o'xshaydi!")
                            print(f"   Bir xil yuzni ikki xil nom bilan saqlab bo'lmaydi!")
                            os.remove(filename)
                            print(f"🗑️  Xavfli manual {detected_direction} rasm o'chirildi")
                            should_keep = False
                        elif is_similar and similar_name == user_name:
                            print(f"✅ Manual {detected_direction} rasm o'sha odamga tegishli")
                    
                    if should_keep:
                        print(f"✅ Manual {detected_direction} rasm saqlandi: {filename}")
                        
                        # Yangi encoding ni ro'yxatga qo'shish
                        new_encoding = create_face_encoding(filename)
                        if new_encoding is not None:
                            existing_encodings.append(new_encoding)
                            existing_names.append(user_name)
                            
                            # MongoDB ga encoding saqlash
                            if use_mongodb and mongodb_manager:
                                try:
                                    mongodb_manager.save_encoding(user_name, new_encoding, filename, detected_direction)
                                    print(f"✅ Manual {detected_direction} encoding MongoDB ga saqlandi")
                                except Exception as e:
                                    print(f"⚠️  MongoDB manual encoding saqlashda xatolik: {e}")
                            
                            # Rasmni o'chirish - encoding saqlangandan keyin
                            try:
                                os.remove(filename)
                                print(f"🗑️  Manual {detected_direction} rasm o'chirildi (encoding saqlandi)")
                            except Exception as e:
                                print(f"⚠️  Manual rasmni o'chirishda xatolik: {e}")
                        
                        # Hisoblagichlarni yangilash
                        direction_counts[detected_direction] += 1
                        total_count += 1
                else:
                    print(f"⚠️  {detected_direction} yo'nalishdan yetarli rasm bor!")
            else:
                print("❌ Yuz aniqlanmadi yoki yo'nalish noma'lum!")
        
        elif key == 27:  # ESC
            break
        
        # Kerakli yo'nalishlarni ko'rsatish
        needed_directions = [d for d, count in direction_counts.items() if count < 5]
        if needed_directions:
            needed_str = ", ".join(needed_directions)
            cv2.putText(frame, f"Kerak: {needed_str}", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Yo'nalish ko'rsatkichi
        if detected_direction != "UNKNOWN":
            direction_color = (0, 255, 0) if direction_counts[detected_direction] < 5 else (0, 0, 255)
            cv2.putText(frame, f"Hozirgi yo'nalish: {detected_direction}", (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, direction_color, 2)
        
        # Yo'nalish ko'rsatmasi
        cv2.putText(frame, "LEFT: o'ng tomonga o'tiring, RIGHT: chap tomonga o'tiring", (10, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "FRONT: markazda turing", (10, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Tez Yuz Qo\'shish', frame)
    
    cap.release()
    cv2.destroyAllWindows()
    
    # MongoDB cleanup
    if use_mongodb and mongodb_manager:
        try:
            mongodb_manager.disconnect()
            print("🔌 MongoDB dan uzildi")
        except Exception as e:
            print(f"⚠️  MongoDB uzilishda xatolik: {e}")
    
    if total_count >= 15:
        print(f"🎉 {user_name} uchun {total_count} ta encoding yaratildi!")
        print("📊 Encoding taqsimoti:")
        print(f"   - {direction_counts['FRONT']} ta TO'G'RI qaragan (FRONT)")
        print(f"   - {direction_counts['RIGHT']} ta O'NGA qaragan (RIGHT)")
        print(f"   - {direction_counts['LEFT']} ta CHAPGA qaragan (LEFT)")
        
        # Papkani o'chirish - barcha encodinglar MongoDB da saqlandi
        try:
            import shutil
            shutil.rmtree(user_dir)
            print(f"🗑️  {user_dir} papkasi o'chirildi (encodinglar MongoDB da)")
        except Exception as e:
            print(f"⚠️  Papkani o'chirishda xatolik: {e}")
        
        print("🔄 Endi main.py ni ishga tushiring va professional tizimni test qiling!")
    elif total_count > 0:
        print(f"✅ {user_name} uchun {total_count} ta encoding yaratildi!")
        print("📊 Encoding taqsimoti:")
        print(f"   - {direction_counts['FRONT']} ta TO'G'RI qaragan (FRONT)")
        print(f"   - {direction_counts['RIGHT']} ta O'NGA qaragan (RIGHT)")
        print(f"   - {direction_counts['LEFT']} ta CHAPGA qaragan (LEFT)")
        
        # Papkani o'chirish
        try:
            import shutil
            shutil.rmtree(user_dir)
            print(f"🗑️  {user_dir} papkasi o'chirildi (encodinglar MongoDB da)")
        except Exception as e:
            print(f"⚠️  Papkani o'chirishda xatolik: {e}")
    else:
        print("❌ Hech qanday encoding yaratilmadi!")
        # Bo'sh papkani o'chirish
        try:
            os.rmdir(user_dir)
            print(f"🗑️  Bo'sh {user_dir} papkasi o'chirildi")
        except Exception as e:
            print(f"⚠️  Bo'sh papkani o'chirishda xatolik: {e}")

if __name__ == "__main__":
    add_new_face()