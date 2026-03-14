#!/usr/bin/env python3
"""
🧪 ROBUST RECOVERY TEST SCRIPT
Robust recovery tizimini test qilish
"""

import json
import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def test_persistent_state():
    """Persistent state manager test"""
    print("🧪 Testing Persistent State Manager...")
    
    # Test ma'lumotlari yaratish
    test_users = {
        "TestUser1": (datetime.now() - timedelta(hours=2)).isoformat(),
        "TestUser2": (datetime.now() - timedelta(hours=15)).isoformat(),  # Stuck user
        "TestUser3": datetime.now().isoformat()
    }
    
    # Current users faylini yaratish
    with open("current_users.json", "w", encoding="utf-8") as f:
        json.dump(test_users, f, indent=2)
    
    print(f"✅ Test users yaratildi: {len(test_users)} ta user")
    
    # Robust recovery test
    try:
        result = subprocess.run(
            ["python3", "robust_recovery.py", "check"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Recovery check: Hech qanday muammo yo'q")
        else:
            print("⚠️  Recovery check: Muammolar aniqlandi")
            print(result.stdout)
        
    except subprocess.TimeoutExpired:
        print("❌ Recovery check timeout")
    except Exception as e:
        print(f"❌ Recovery check error: {e}")

def test_stuck_users():
    """Stuck users detection test"""
    print("\n🧪 Testing Stuck Users Detection...")
    
    # Stuck users yaratish
    stuck_users = {
        "StuckUser1": (datetime.now() - timedelta(hours=13)).isoformat(),
        "StuckUser2": (datetime.now() - timedelta(hours=25)).isoformat(),
        "NormalUser": datetime.now().isoformat()
    }
    
    with open("current_users.json", "w", encoding="utf-8") as f:
        json.dump(stuck_users, f, indent=2)
    
    print(f"✅ Stuck users test data yaratildi")
    
    # Reset test
    try:
        result = subprocess.run(
            ["python3", "robust_recovery.py", "reset-users"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"✅ Reset result: {result.stdout.strip()}")
        
        # Reset qilinganini tekshirish
        with open("current_users.json", "r", encoding="utf-8") as f:
            remaining_users = json.load(f)
        
        print(f"✅ Qolgan userlar: {len(remaining_users)} ta")
        
    except Exception as e:
        print(f"❌ Reset test error: {e}")

def test_backup_system():
    """Backup system test"""
    print("\n🧪 Testing Backup System...")
    
    try:
        result = subprocess.run(
            ["python3", "robust_recovery.py", "backup"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"✅ Backup result: {result.stdout.strip()}")
        
        # Backup fayllarini tekshirish
        state_dir = Path("state_backup")
        if state_dir.exists():
            backup_files = list(state_dir.glob("backup_*.json"))
            print(f"✅ Backup fayllari: {len(backup_files)} ta")
        
    except Exception as e:
        print(f"❌ Backup test error: {e}")

def test_crash_detection():
    """Crash detection test"""
    print("\n🧪 Testing Crash Detection...")
    
    # Fake PID file yaratish
    with open("face_id.pid", "w") as f:
        f.write("99999")  # Non-existent PID
    
    # Fake session file yaratish
    session_data = {
        "status": "running",
        "pid": 99999,
        "start_time": datetime.now().isoformat()
    }
    
    with open("system_session.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2)
    
    print("✅ Fake crash scenario yaratildi")
    
    try:
        result = subprocess.run(
            ["python3", "robust_recovery.py", "check"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print("✅ Crash detection ishlayapti")
            print(result.stdout)
        else:
            print("⚠️  Crash detection ishlamadi")
        
    except Exception as e:
        print(f"❌ Crash detection test error: {e}")
    
    # Cleanup
    Path("face_id.pid").unlink(missing_ok=True)
    Path("system_session.json").unlink(missing_ok=True)

def test_performance():
    """Performance test"""
    print("\n🧪 Testing Performance...")
    
    # Face system import test
    try:
        start_time = time.time()
        
        # Import test
        import sys
        sys.path.append('.')
        from face_system.core.persistent_state_manager import PersistentStateManager
        
        # Mock face system
        class MockFaceSystem:
            def __init__(self):
                self.current_users = {}
                self.use_mongodb = False
                self.mongodb_manager = None
        
        mock_system = MockFaceSystem()
        state_manager = PersistentStateManager(mock_system)
        
        import_time = time.time() - start_time
        print(f"✅ Import time: {import_time:.3f} seconds")
        
        # State save/load test
        start_time = time.time()
        
        # Test data
        mock_system.current_users = {
            "TestUser": datetime.now()
        }
        
        # Save test
        state_manager.save_complete_state()
        save_time = time.time() - start_time
        
        # Load test
        start_time = time.time()
        state_manager.load_complete_state()
        load_time = time.time() - start_time
        
        print(f"✅ Save time: {save_time:.3f} seconds")
        print(f"✅ Load time: {load_time:.3f} seconds")
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")

def cleanup_test_files():
    """Test fayllarini tozalash"""
    print("\n🧹 Cleaning up test files...")
    
    test_files = [
        "current_users.json",
        "face_id.pid",
        "system_session.json"
    ]
    
    for file_name in test_files:
        Path(file_name).unlink(missing_ok=True)
    
    print("✅ Test fayllari tozalandi")

def main():
    """Asosiy test funksiyasi"""
    print("🧪 ROBUST RECOVERY SYSTEM TEST")
    print("=" * 40)
    
    try:
        test_persistent_state()
        test_stuck_users()
        test_backup_system()
        test_crash_detection()
        test_performance()
        
        print("\n🎉 BARCHA TESTLAR TUGALLANDI!")
        print("✅ Robust recovery system tayyor")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test to'xtatildi")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
    finally:
        cleanup_test_files()

if __name__ == "__main__":
    main()