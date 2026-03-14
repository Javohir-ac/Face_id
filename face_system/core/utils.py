"""
Yordamchi funksiyalar
"""
from datetime import datetime, date

def get_uzbek_day_name(english_day):
    """Inglizcha kun nomini o'zbekchaga o'girish"""
    days = {
        'Monday': 'Dushanba',
        'Tuesday': 'Seshanba', 
        'Wednesday': 'Chorshanba',
        'Thursday': 'Payshanba',
        'Friday': 'Juma',
        'Saturday': 'Shanba',
        'Sunday': 'Yakshanba'
    }
    return days.get(english_day, english_day)

def format_duration(minutes):
    """Daqiqalarni soat:daqiqa formatiga o'girish"""
    if minutes < 60:
        return f"{minutes} daqiqa"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours} soat"
    else:
        return f"{hours} soat {remaining_minutes} daqiqa"

def log_with_timestamp(level, message):
    """Vaqt bilan log yozish"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")