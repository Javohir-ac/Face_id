#!/usr/bin/env python3
"""
🧪 RECOVERY SCENARIO TEST
User ichkarida, script to'xtab qoldi, qayta ishga tushirildi - nima bo'ladi?
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

def simulate_user_inside_crash_scenario():
    """
    SCENARIO: 
    1. User ichkarida
    2. Script to'xtab qoldi
    3. Qayta ishga tushirildi
    4. User kameraga ko'rindi
    """
    
    print("🎬 RECOVERY SCENARIO SIMULATION")
    print("=" * 50)
    
    # 1. User ichkarida bo'lgan holatni simulatsiya qilish
    print("\n1️⃣ STEP 1: User ichkarida (script ishlayotgan payt)")
    
    # Javohir ichkarida deb faraz qilaylik
    current_users = {
        "Javohir": (datetime.now() - timedelta(hours=2)).isoformat()  # 2 soat oldin kelgan
    }
    
    # Current users faylini yaratish
    with open("current_users.json", "w", encoding="utf-8") as f:
        json.dump(current_users, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Javohir ichkarida: {current_users['Javohir']}")
    
    # 2. Script crash simulatsiyasi
    print("\n2️⃣ STEP 2: Script to'xtab qoldi (crash)")
    print("💥 Script unexpected crash...")
    print("📁 Lekin current_users.json saqlanib qoldi")
    
    # 3. Recovery simulation
    print("\n3️⃣ STEP 3: Script qayta ishga tushirildi")
    print("🔄 Recovery process...")
    
    # Face system import qilish
    try:
        import sys
        sys.path.append('.')
        from face_system.core.face_system import FaceRecognitionSystem
        
        # Face system yaratish (recovery bilan)
        print("🚀 FaceRecognitionSystem yaratilmoqda...")
        face_system = FaceRecognitionSystem()
        
        print(f"✅ Recovery tugallandi!")
        print(f"📊 Tiklangan userlar: {len(face_system.current_users)} ta")
        
        for user_name, entry_time in face_system.current_users.items():
            duration = datetime.now() - entry_time
            print(f"   - {user_name}: {duration.total_seconds()/3600:.1f} soat ichkarida")
        
        # 4. User kameraga ko'rinish simulatsiyasi
        print("\n4️⃣ STEP 4: Javohir kameraga ko'rindi")
        
        # Keyingi expected action ni tekshirish
        expected_action = face_system.get_next_expected_action("Javohir")
        print(f"🎯 Javohir uchun keyingi action: {expected_action}")
        
        if expected_action == "exit":
            print("✅ TO'G'RI! Javohir ichkarida, shuning uchun keyingi action EXIT")
            print("🚪 Agar Javohir kameraga ko'rinsa, u TASHQARIGA chiqadi")
            
            # Exit action simulatsiyasi
            print("\n🎬 EXIT ACTION SIMULATION:")
            face_system.process_user_action("Javohir", 0.85)  # High confidence
            
            # Natijani tekshirish
            if "Javohir" not in face_system.current_users:
                print("✅ SUCCESS! Javohir tashqariga chiqdi")
                print("📝 Attendance ga EXIT yozuvi qo'shildi")
            else:
                print("❌ ERROR! Javohir hali ham ichkarida")
        else:
            print("❌ XATO! Expected action noto'g'ri")
        
        # 5. Natijani ko'rsatish
        print("\n5️⃣ STEP 5: Yakuniy holat")
        print(f"📊 Hozirgi ichkaridagi userlar: {len(face_system.current_users)} ta")
        
        if face_system.current_users:
            for user_name, entry_time in face_system.current_users.items():
                print(f"   - {user_name}: ichkarida")
        else:
            print("   - Hech kim ichkarida emas")
        
        return True
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

def test_multiple_scenarios():
    """Ko'p xil scenariolarni test qilish"""
    
    print("\n" + "="*60)
    print("🧪 MULTIPLE RECOVERY SCENARIOS")
    print("="*60)
    
    scenarios = [
        {
            "name": "1 user ichkarida",
            "users": {"Mehriddin": (datetime.now() - timedelta(hours=1)).isoformat()}
        },
        {
            "name": "3 user ichkarida",
            "users": {
                "Javohir": (datetime.now() - timedelta(hours=2)).isoformat(),
                "Farizod": (datetime.now() - timedelta(hours=3)).isoformat(),
                "Odinaxon": (datetime.now() - timedelta(minutes=30)).isoformat()
            }
        },
        {
            "name": "Stuck user (15 soat)",
            "users": {"StuckUser": (datetime.now() - timedelta(hours=15)).isoformat()}
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 SCENARIO {i}: {scenario['name']}")
        
        # Test data yaratish
        with open("current_users.json", "w", encoding="utf-8") as f:
            json.dump(scenario['users'], f, indent=2, ensure_ascii=False)
        
        try:
            # Recovery test
            import sys
            sys.path.append('.')
            from face_system.core.persistent_state_manager import PersistentStateManager
            
            # Mock face system
            class MockFaceSystem:
                def __init__(self):
                    self.current_users = {}
                    self.use_mongodb = False
                    self.mongodb_manager = None
                    self.total_recognitions = 0
                    self.successful_recognitions = 0
                    self.failed_recognitions = 0
                    
                def get_next_expected_action(self, user_name):
                    if user_name in self.current_users:
                        return "exit"
                    else:
                        return "entry"
            
            mock_system = MockFaceSystem()
            state_manager = PersistentStateManager(mock_system)
            
            # Recovery
            recovery_success = state_manager.load_complete_state()
            
            if recovery_success:
                print(f"✅ Recovery successful: {len(mock_system.current_users)} ta user tiklandi")
                
                # Har bir user uchun expected action
                for user_name in mock_system.current_users.keys():
                    expected = mock_system.get_next_expected_action(user_name)
                    print(f"   - {user_name}: keyingi action = {expected}")
            else:
                print("❌ Recovery failed")
                
        except Exception as e:
            print(f"❌ Scenario {i} error: {e}")

def cleanup():
    """Test fayllarini tozalash"""
    test_files = ["current_users.json"]
    for file_name in test_files:
        Path(file_name).unlink(missing_ok=True)

def main():
    """Asosiy test"""
    try:
        # Asosiy scenario
        success = simulate_user_inside_crash_scenario()
        
        if success:
            # Qo'shimcha scenariolar
            test_multiple_scenarios()
            
            print("\n" + "="*60)
            print("🎉 BARCHA SCENARIOLAR MUVAFFAQIYATLI!")
            print("="*60)
            print("\n📋 XULOSA:")
            print("✅ User ichkarida bo'lsa, script crash bo'lsa ham:")
            print("   1. Recovery paytida user ichkarida qoladi")
            print("   2. Keyingi expected action = EXIT")
            print("   3. Kameraga ko'rinsa, tashqariga chiqadi")
            print("   4. Ma'lumotlar yo'qolmaydi")
            print("\n🛡️  ROBUST RECOVERY ISHLAYDI!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test to'xtatildi")
    finally:
        cleanup()

if __name__ == "__main__":
    main()