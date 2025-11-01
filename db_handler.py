import json
import logging
import os
import re
from threading import Lock

logger = logging.getLogger(__name__)

USERS_FILE = "users.json"
SCHEDULE_FILE = "schedule.json"
DATA_FILE = "data.json"

locks = {
    USERS_FILE: Lock(),
    SCHEDULE_FILE: Lock(),
    DATA_FILE: Lock(),
}

def _load_data(filename):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return {}
        
    with locks[filename]:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {filename}. Returning empty dict.")
            return {}
        except FileNotFoundError:
            logger.warning(f"File {filename} not found. Creating.")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            return {}

def _save_data(filename, data):
    with locks[filename]:
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {e}")
            return False

def check_user(username, password):
    users = _load_data(USERS_FILE)
    user_key = username.lower()
    if user_key in users and users[user_key]["password"] == password:
        details = users[user_key]
        return details.get("role"), details
    return None, None

def update_user_credentials(username, new_username, new_password):
    users = _load_data(USERS_FILE)
    username_low = username.lower()
    new_username_low = new_username.lower()
    
    if username_low not in users:
        return False, "User not found"
        
    if username_low != new_username_low and new_username_low in users:
         return False, "New username already exists"

    user_data = users.pop(username_low)
    user_data["password"] = new_password
    users[new_username_low] = user_data
    
    _save_data(USERS_FILE, users)
    return True, "Success"

def get_schedule_for_class(class_id):
    schedule = _load_data(SCHEDULE_FILE)
    return schedule.get(class_id, {})

def get_teacher_schedule(teacher_username):
    users = _load_data(USERS_FILE)
    teacher_details = users.get(teacher_username.lower(), {})
    teacher_name = teacher_details.get("full_name")
    
    if not teacher_name:
        logger.warning(f"Teacher {teacher_username} has no 'full_name' in users.json.")
        teacher_name = teacher_details.get("subject", teacher_username)
        
    full_schedule = _load_data(SCHEDULE_FILE)
    teacher_personal_schedule = {}

    for class_id, class_schedule in full_schedule.items():
        for day, lessons in class_schedule.items():
            for lesson_str in lessons:
                if teacher_name.lower() in lesson_str.lower():
                    if day not in teacher_personal_schedule:
                        teacher_personal_schedule[day] = []
                    teacher_personal_schedule[day].append(f"({class_id}) {lesson_str}")

    for day in teacher_personal_schedule:
         teacher_personal_schedule[day].sort()

    return teacher_personal_schedule

def update_schedule(class_id, day, lessons):
    schedule = _load_data(SCHEDULE_FILE)
    if class_id not in schedule:
        schedule[class_id] = {}
    schedule[class_id][day] = lessons
    _save_data(SCHEDULE_FILE, schedule)
    logger.info(f"Schedule updated for {class_id} on {day}.")

def get_class_letters(class_num):
    schedule = _load_data(SCHEDULE_FILE)
    letters = set()
    for class_id in schedule.keys():
        if class_id.startswith(str(class_num)):
            letter = re.sub(r'^\d+', '', class_id)
            if letter:
                letters.add(letter)
    return sorted(list(letters))

def parse_lesson_time(lesson_str: str) -> str | None:
    match = re.search(r'(\d{1,2}:\d{2})', lesson_str)
    if match:
        return match.group(1)
    return None

def get_grades_by_subject(student_username, subject):
    data = _load_data(DATA_FILE)
    grades = data.get("grades", {}).get(student_username.lower(), {}).get(subject, [])
    return grades 

def get_subjects_for_student(student_username):
    data = _load_data(DATA_FILE)
    subjects = data.get("grades", {}).get(student_username.lower(), {}).keys()
    return list(subjects)

def set_grade(student_username, subject, grade, date_str):
    data = _load_data(DATA_FILE)
    if "grades" not in data: data["grades"] = {}
    
    student_key = student_username.lower()
    if student_key not in data["grades"]:
        data["grades"][student_key] = {}
    
    if subject not in data["grades"][student_key]:
        data["grades"][student_key][subject] = []
        
    data["grades"][student_key][subject].append(f"{date_str}: {grade}")
    _save_data(DATA_FILE, data)

def get_students_by_class(class_id):
    users = _load_data(USERS_FILE)
    students = []
    for username, details in users.items():
        if details.get("role") == "student" and details.get("class_id") == class_id:
            students.append(username)
    
    return sorted(students)

def mark_attendance(student_username, date_str, status):
    data = _load_data(DATA_FILE)
    if "attendance" not in data: data["attendance"] = {}
    
    student_key = student_username.lower()
    if student_key not in data["attendance"]:
        data["attendance"][student_key] = {}
        
    data["attendance"][student_key][date_str] = status
    _save_data(DATA_FILE, data)

def get_user_settings(user_id):
    data = _load_data(DATA_FILE)
    default_settings = {"notify_lesson": False, "notify_schedule": False}
    return data.get("user_settings", {}).get(str(user_id), default_settings)

def get_all_user_settings():
    data = _load_data(DATA_FILE)
    return data.get("user_settings", {})

def update_user_settings(user_id, setting_key, value):
    data = _load_data(DATA_FILE)
    if "user_settings" not in data:
        data["user_settings"] = {}
    
    user_id_str = str(user_id)
    if user_id_str not in data["user_settings"]:
        data["user_settings"][user_id_str] = {"notify_lesson": False, "notify_schedule": False}
        
    data["user_settings"][user_id_str][setting_key] = value
    _save_data(DATA_FILE, data)
