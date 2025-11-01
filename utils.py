import pytz
from datetime import datetime, timedelta

# Часовой пояс
TZ = pytz.timezone('Asia/Tashkent')

def get_day_of_week_str(target_day='today') -> str:
    """Возвращает 'monday', 'tuesday' и т.д. для 'today' или 'tomorrow'."""
    now = datetime.now(TZ)
    if target_day == 'tomorrow':
        target_date = now + timedelta(days=1)
    else:
        target_date = now
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return days[target_date.weekday()]

def get_today_date_str() -> str:
    """Возвращает сегодняшнюю дату в Asia/Tashkent (ДД.ММ.ГГГГ)."""
    return datetime.now(TZ).strftime('%d.%m.%Y')

def get_tomorrow_date_str() -> str:
    """Возвращает завтрашнюю дату в Asia/Tashkent (ДД.ММ.ГГГГ)."""
    tomorrow = datetime.now(TZ) + timedelta(days=1)
    return tomorrow.strftime('%d.%m.%Y')