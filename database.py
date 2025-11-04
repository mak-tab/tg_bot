import json
import os

# --- Константы с именами файлов ---
USERS_FILE = 'users.json'
TEACHERS_FILE = 'teachers.json'
ADMINS_FILE = 'admins.json'
SCHEDULE_FILE = 'schedule.json'
DATA_FILE = 'data.json'  # Для доп. данных, например, оценок или посещаемости

# Список всех файлов для инициализации
ALL_DB_FILES = [USERS_FILE, TEACHERS_FILE, ADMINS_FILE, SCHEDULE_FILE, DATA_FILE]

# --- Основные функции I/O (Ввода/Вывода) ---

def init_database():
    """
    Проверяет наличие всех файлов БД. Если файл отсутствует,
    создает его с пустым словарем {}.
    """
    for file_path in ALL_DB_FILES:
        if not os.path.exists(file_path):
            safe_save(file_path, {})
            print(f"Файл {file_path} не найден, создан новый.")
        else:
            # Проверяем, что файл не пустой и содержит JSON
            safe_load(file_path, default_data={})


def safe_load(file_path, default_data={}):
    """
    Безопасно загружает данные из JSON-файла.
    В случае ошибки (файл не найден, пуст или содержит некорректный JSON),
    сохраняет и возвращает данные по умолчанию (default_data).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Если файл пустой, json.load() выдаст ошибку
            content = f.read()
            if not content:
                print(f"Предупреждение: Файл {file_path} пуст. Будет использован default.")
                safe_save(file_path, default_data)
                return default_data
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при чтении {file_path}: {e}. Файл будет перезаписан.")
        safe_save(file_path, default_data)
        return default_data

def safe_save(file_path, data):
    """
    Безопасно сохраняет данные в JSON-файл.
    Использует отступы (indent=4) и `ensure_ascii=False` для
    корректного отображения кириллицы.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except (IOError, TypeError) as e:
        print(f"Критическая ошибка при сохранении в {file_path}: {e}")

# --- Функции-хелперы для работы с конкретными файлами ---

# --- Ученики (users.json) ---
def get_all_students():
    return safe_load(USERS_FILE)

def save_all_students(data):
    safe_save(USERS_FILE, data)

# --- Учителя (teachers.json) ---
def get_all_teachers():
    return safe_load(TEACHERS_FILE)

def save_all_teachers(data):
    safe_save(TEACHERS_FILE, data)

# --- Админы (admins.json) ---
def get_all_admins():
    return safe_load(ADMINS_FILE)

def save_all_admins(data):
    safe_save(ADMINS_FILE, data)

# --- Расписание (schedule.json) ---
def get_schedule():
    return safe_load(SCHEDULE_FILE)

def save_schedule(data):
    safe_save(SCHEDULE_FILE, data)

# --- Прочие данные (data.json) ---
def get_app_data():
    return safe_load(DATA_FILE)

def save_app_data(data):
    safe_save(DATA_FILE, data)

# --- Вспомогательные функции для логики бота ---

def get_user_by_telegram_id(telegram_id):
    """
    Ищет пользователя (любой роли) по его ID в Telegram.
    Ключи в JSON должны быть строками.
    Возвращает (user_data, role) или (None, None).
    """
    telegram_id = str(telegram_id) # ID в JSON всегда строки

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
    """
    Ищет пользователя по username среди всех записей.
    Это медленная операция (полный перебор), но необходимая для логина.
    Возвращает (telegram_id, user_data) если найден, иначе (None, None).
    """
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

# --- Блок для инициализации ---
if __name__ == "__main__":
    print("Инициализация базы данных...")
    init_database()
    print("Проверка файлов завершена.")
    
    # Пример добавления тестового админа, если файл пуст
    # (для первичной настройки)
    admins = get_all_admins()
    if not admins:
        print("Файл админов пуст. Добавление тестового админа...")
        test_admin = {
            "123456789": { # Условный Telegram ID
                "lang": "ru",
                "username": "admin",
                "password": "password123",
                "first_name": "Admin",
                "last_name": "Glavniy"
            }
        }
        save_all_admins(test_admin)
        print("Тестовый админ 'admin' с паролем 'password123' добавлен.")
    else:
        print("Файл админов уже содержит данные.")
