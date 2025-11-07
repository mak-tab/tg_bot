from telegram import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton
)
translations = {
    'ru': {
        'role_student': "Ученик(ца) 🧑‍🎓",
        'role_teacher': "Учитель 🧑‍🏫",
        'role_admin': "Администрация 💼",
        'main_schedule': "Расписание 🗓️",
        'main_grades': "Оценки 📊",
        'main_settings': "Настройки ⚙️",
        'main_attendance': "Присутствие ✅",
        'schedule_today': "На сегодня",
        'schedule_tomorrow': "На завтра",
        'schedule_full': "Всё расписание",
        'settings_next_lesson_on': "🔔 Следующий урок (ВКЛ)",
        'settings_next_lesson_off': "🔕 Следующий урок (ВЫКЛ)",
        'settings_daily_schedule_on': "📅 Расписание утром (ВКЛ)",
        'settings_daily_schedule_off': "🔕 Расписание утром (ВЫКЛ)",
        'settings_change_login': "Сменить логин/пароль 🔑",
        'admin_reg_student': "Регистрация ученика ➕",
        'admin_edit_schedule': "Изменить расписание ✏️",
        'attendance_present': "✅ Присутствует",
        'attendance_absent': "❌ Отсутствует",
        'back': "⬅️ Назад"
    },
    'en': {
        'role_student': "Student 🧑‍🎓",
        'role_teacher': "Teacher 🧑‍🏫",
        'role_admin': "Administration 💼",
        'main_schedule': "Schedule 🗓️",
        'main_grades': "Grades 📊",
        'main_settings': "Settings ⚙️",
        'main_attendance': "Attendance ✅",
        'schedule_today': "For today",
        'schedule_tomorrow': "For tomorrow",
        'schedule_full': "Full schedule",
        'settings_next_lesson_on': "🔔 Next lesson (ON)",
        'settings_next_lesson_off': "🔕 Next lesson (OFF)",
        'settings_daily_schedule_on': "📅 Daily schedule (ON)",
        'settings_daily_schedule_off': "🔕 Daily schedule (OFF)",
        'settings_change_login': "Change login/password 🔑",
        'admin_reg_student': "Register student ➕",
        'admin_edit_schedule': "Edit schedule ✏️",
        'attendance_present': "✅ Present",
        'attendance_absent': "❌ Absent",
        'back': "⬅️ Back"
    },
    'uz': {
        'role_student': "O'quvchi 🧑‍🎓",
        'role_teacher': "O'qituvchi 🧑‍🏫",
        'role_admin': "Ma'muriyat 💼",
        'main_schedule': "Dars jadvali 🗓️",
        'main_grades': "Baholar 📊",
        'main_settings': "Sozlamalar ⚙️",
        'main_attendance': "Davomat ✅",
        'schedule_today': "Bugungi",
        'schedule_tomorrow': "Ertangi",
        'schedule_full': "To'liq jadval",
        'settings_next_lesson_on': "🔔 Keyingi dars (YONIQ)",
        'settings_next_lesson_off': "🔕 Keyingi dars (O'CHIQ)",
        'settings_daily_schedule_on': "📅 Ertalabki jadval (YONIQ)",
        'settings_daily_schedule_off': "🔕 Ertalabki jadval (O'CHIQ)",
        'settings_change_login': "Login/parolni o'zgartirish 🔑",
        'admin_reg_student': "O'quvchini ro'yxatga olish ➕",
        'admin_edit_schedule': "Jadvalni tahrirlash ✏️",
        'attendance_present': "✅ Qatnashdi",
        'attendance_absent': "❌ Qatnashmadi",
        'back': "⬅️ Orqaga"
    }
}

def get_text(key, lang='ru'):
    return translations.get(lang, translations['ru']).get(key, f"_{key}_")

def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("O'zbekcha 🇺🇿", callback_data='set_lang_uz')],
        [InlineKeyboardButton("Русский 🇷🇺", callback_data='set_lang_ru')],
        [InlineKeyboardButton("English 🇬🇧", callback_data='set_lang_en')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_role_keyboard(lang='ru'):
    keyboard = [
        [KeyboardButton(get_text('role_student', lang))],
        [KeyboardButton(get_text('role_teacher', lang))],
        [KeyboardButton(get_text('role_admin', lang))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_student_main_keyboard(lang='ru'):
    keyboard = [
        [KeyboardButton(get_text('main_schedule', lang))],
        [KeyboardButton(get_text('main_grades', lang))],
        [KeyboardButton(get_text('main_settings', lang))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_student_schedule_keyboard(lang='ru'):
    keyboard = [
        [KeyboardButton(get_text('schedule_tomorrow', lang)),
         KeyboardButton(get_text('schedule_full', lang))],
        [KeyboardButton(get_text('back', lang))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_teacher_main_keyboard(lang='ru'):
    keyboard = [
        [KeyboardButton(get_text('main_schedule', lang)),
         KeyboardButton(get_text('main_attendance', lang))],
        [KeyboardButton(get_text('main_grades', lang)),
         KeyboardButton(get_text('main_settings', lang))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_teacher_schedule_keyboard(lang='ru'):
    keyboard = [
        [KeyboardButton(get_text('schedule_today', lang)),
         KeyboardButton(get_text('schedule_tomorrow', lang))],
        [KeyboardButton(get_text('schedule_full', lang))],
        [KeyboardButton(get_text('back', lang))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_attendance_markup(lang='ru'):
    keyboard = [
        [
            InlineKeyboardButton(get_text('attendance_present', lang), callback_data='att_present'),
            InlineKeyboardButton(get_text('attendance_absent', lang), callback_data='att_absent')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_grades_markup(lang='ru'):
    keyboard = [
        [
            InlineKeyboardButton("2", callback_data='grade_2'),
            InlineKeyboardButton("3", callback_data='grade_3'),
            InlineKeyboardButton("4", callback_data='grade_4'),
            InlineKeyboardButton("5", callback_data='grade_5'),
        ],
        [InlineKeyboardButton(get_text('back', lang), callback_data='grade_back_to_student_list')] # Пример
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_main_keyboard(lang='ru'):
    keyboard = [
        [KeyboardButton(get_text('admin_reg_student', lang))],
        [KeyboardButton(get_text('admin_edit_schedule', lang))],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def generate_subjects_keyboard(subjects_list, lang='ru'):
    keyboard = []
    for subject in subjects_list:
        keyboard.append([InlineKeyboardButton(subject, callback_data=f'grade_subj_{subject}')])
    
    keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data='back_to_main_menu')])
    return InlineKeyboardMarkup(keyboard)

def generate_settings_keyboard(user_data, lang='ru'):
    next_lesson_status = user_data.get('warning_about_next_lesson', False)
    next_lesson_text = get_text('settings_next_lesson_on' if next_lesson_status else 'settings_next_lesson_off', lang)
    next_lesson_callback = 'settings_toggle_next_lesson'
    daily_schedule_status = user_data.get('warning_everyday_about_lessons', False)
    daily_schedule_text = get_text('settings_daily_schedule_on' if daily_schedule_status else 'settings_daily_schedule_off', lang)
    daily_schedule_callback = 'settings_toggle_daily_schedule'
    keyboard = [
        [InlineKeyboardButton(next_lesson_text, callback_data=next_lesson_callback)],
        [InlineKeyboardButton(daily_schedule_text, callback_data=daily_schedule_callback)],
        [InlineKeyboardButton(get_text('settings_change_login', lang), callback_data='settings_change_login')],
        [InlineKeyboardButton(get_text('back', lang), callback_data='back_to_main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def generate_class_list_keyboard(classes_list, callback_prefix, lang='ru'):
    keyboard = []
    row = []
    for class_num in classes_list:
        row.append(InlineKeyboardButton(class_num, callback_data=f'{callback_prefix}{class_num}'))
        if len(row) >= 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data='back_to_main_menu')])
    return InlineKeyboardMarkup(keyboard)

def generate_letter_list_keyboard(letters_list, class_num, callback_prefix, lang='ru'):
    keyboard = []
    row = []
    for letter in letters_list:
        row.append(InlineKeyboardButton(letter, callback_data=f'{callback_prefix}{class_num}_{letter}'))
        if len(row) >= 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data=f'{callback_prefix}back_to_class')])
    return InlineKeyboardMarkup(keyboard)

def generate_students_list_keyboard(students_data, class_num, letter, callback_prefix, lang='ru'):
    keyboard = []
    for student in students_data:
        name = f"{student.get('first_name', '')} {student.get('last_name', '')}"
        student_id = student.get('id') 
        keyboard.append([InlineKeyboardButton(name, callback_data=f'{callback_prefix}{student_id}')])
    
    keyboard.append([InlineKeyboardButton(get_text('back', lang), callback_data=f'{callback_prefix}back_to_letter_{class_num}')])
    return InlineKeyboardMarkup(keyboard)

