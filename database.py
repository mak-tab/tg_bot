import json, os

USERS_FILE = 'users.json'
TEACHERS_FILE = 'teachers.json'
ADMINS_FILE = 'admins.json'
SCHEDULE_FILE = 'schedule.json'
DATA_FILE = 'data.json'

ALL_DB_FILES = [USERS_FILE, TEACHERS_FILE, ADMINS_FILE, SCHEDULE_FILE, DATA_FILE]

def init_database():
    for file_path in ALL_DB_FILES:
        if not os.path.exists(file_path):
            safe_save(file_path, {})
        else:
            safe_load(file_path, default_data={})

def safe_load(file_path, default_data={}):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if not content:
            safe_save(file_path, default_data)
            return default_data
        return json.loads(content)

def safe_save(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_all_students(): 
    return safe_load(USERS_FILE)

def save_all_students(data): 
    safe_save(USERS_FILE, data)

def get_all_teachers(): 
    return safe_load(TEACHERS_FILE)

def save_all_teachers(data): 
    safe_save(TEACHERS_FILE, data)

def get_all_admins(): 
    return safe_load(ADMINS_FILE)

def save_all_admins(data): 
    safe_save(ADMINS_FILE, data)

def get_schedule(): 
    return safe_load(SCHEDULE_FILE)

def save_schedule(data): 
    safe_save(SCHEDULE_FILE, data)

def get_app_data(): 
    return safe_load(DATA_FILE)

def save_app_data(data): 
    safe_save(DATA_FILE, data)

def get_user_by_telegram_id(telegram_id):
    telegram_id = str(telegram_id)
    students = get_all_students()
    if telegram_id in students: 
        return students[telegram_id], 'student'
    teachers = get_all_teachers()
    if telegram_id in teachers: 
        return teachers[telegram_id], 'teacher'
    admins = get_all_admins()
    if telegram_id in admins: 
        return admins[telegram_id], 'admin'
    return None, None

def find_user_by_username(username, role):
    username = username.lower()
    data_loader = None
    if role == 'student': 
        data_loader = get_all_students
    elif role == 'teacher': 
        data_loader = get_all_teachers
    elif role == 'admin': 
        data_loader = get_all_admins
    else: 
        return None, None
    all_users = data_loader()
    for tg_id, user_data in all_users.items():
        if user_data.get('username') == username:
            return tg_id, user_data
    return None, None

if __name__ == "__main__":
    init_database()
    admins = get_all_admins()
    if not admins:
        test_admin = {
            "123456789": {
                "lang": "ru",
                "username": "admin",
                "password": "password123",
                "first_name": "Admin",
                "last_name": "Glavniy"
            }
        }
        save_all_admins(test_admin)

