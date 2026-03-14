#!/usr/bin/env python3
"""
🔄 User Reset Script - Barcha userlarni tashqariga chiqarish
"""
import json
import os
from datetime import datetime
from face_system.core.face_system import FaceRecognitionSystem

def show_current_users():
    """Hozirgi ichkaridagi userlarni ko'rsatish"""
    if os.path.exists('current_users.json'):
        with open('current_users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if data:
            print("👥 Hozir ichkaridagi userlar:")
            for user_name, entry_time_str in data.items():
                entry_time = datetime.fromisoformat(entry_time_str)
                duration = datetime.now() - entry_time
                hours = int(duration.total_seconds() / 3600)
                minutes = int((duration.total_seconds() % 3600) / 60)
                print(f"   🔹 {user_name}: {hours}h {minutes}m ichkarida")
            return len(data)
        else:
            print("✅ Hech kim ichkarida emas")
            return 0
    else:
        print("📁 current_users.json fayli topilmadi")
        return 0

def manual_reset():
    """Manual reset - barcha userlarni chiqarish"""
    print("🔄 Manual reset boshlanyapti...")
    
    try:
        # Face system yaratish
        face_system = FaceRecognitionSystem()
        
        # Barcha userlarni chiqarish
        exit_count = face_system.reset_all_users("manual_reset")
        
        if exit_count > 0:
            print(f"✅ {exit_count} ta user muvaffaqiyatli chiqarildi")
        else:
            print("ℹ️  Hech kim ichkarida emas edi")
            
    except Exception as e:
        print(f"❌ Reset xatoligi: {e}")

def main():
    """Asosiy funksiya"""
    print("="*50)
    print("🔄 USER RESET UTILITY")
    print("="*50)
    
    # Hozirgi holatni ko'rsatish
    user_count = show_current_users()
    print()
    
    if user_count == 0:
        print("✅ Reset kerak emas")
        return
    
    # Tasdiqlash
    print(f"⚠️  {user_count} ta user ichkarida qolgan")
    print("🔄 Ularni barcha tashqariga chiqarasizmi?")
    
    choice = input("Davom etish uchun 'yes' yozing: ").lower().strip()
    
    if choice in ['yes', 'y', 'ha', 'xa']:
        manual_reset()
    else:
        print("❌ Reset bekor qilindi")
    
    print("="*50)

if __name__ == "__main__":
    main()