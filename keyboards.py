from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from localization import get_text

def get_language_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(get_text('uz', 'btn_lang_uz'), callback_data="lang_uz")],
        [InlineKeyboardButton(get_text('ru', 'btn_lang_ru'), callback_data="lang_ru")],
        [InlineKeyboardButton(get_text('en', 'btn_lang_en'), callback_data="lang_en")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_class_number_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(str(i), callback_data=f"class_num_{i}") for i in range(1, 5)],
        [InlineKeyboardButton(str(i), callback_data=f"class_num_{i}") for i in range(5, 9)],
        [InlineKeyboardButton(str(i), callback_data=f"class_num_{i}") for i in range(9, 12)],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_class_letter_keyboard(letters: list) -> InlineKeyboardMarkup:
    keyboard = [
        letters[i:i + 4] for i in range(0, len(letters), 4)
    ]
    inline_keyboard = [
        [InlineKeyboardButton(letter, callback_data=f"class_letter_{letter}") for letter in row]
        for row in keyboard
    ]
    return InlineKeyboardMarkup(inline_keyboard)

def get_student_main_menu(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [get_text(lang, 'btn_schedule'), get_text(lang, 'btn_grades')],
        [get_text(lang, 'btn_settings')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder=get_text(lang, 'main_menu'))

def get_student_schedule_menu(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [get_text(lang, 'btn_schedule_tomorrow'), get_text(lang, 'btn_schedule_full')],
        [get_text(lang, 'btn_back')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_subjects_keyboard(subjects: list, lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(subject, callback_data=f"subject_{subject}")]
        for subject in subjects
    ]
    # ИСПРАВЛЕНО: Вызываем get_text()
    keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back_inline'), callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(settings: dict, lang: str) -> InlineKeyboardMarkup:
    # ИСПРАВЛЕНО: Убраны списки [], теперь это просто строки
    notify_lesson_text = get_text(lang, 'btn_notify_lesson_on') if settings.get("notify_lesson") else get_text(lang, 'btn_notify_lesson_off')
    notify_schedule_text = get_text(lang, 'btn_notify_schedule_on') if settings.get("notify_schedule") else get_text(lang, 'btn_notify_schedule_off')
    
    keyboard = [
        [InlineKeyboardButton(notify_lesson_text, callback_data="toggle_notify_lesson")],
        [InlineKeyboardButton(notify_schedule_text, callback_data="toggle_notify_schedule")],
        # ИСПРАВЛЕНО: Вызываем get_text()
        [InlineKeyboardButton(get_text(lang, 'btn_change_creds'), callback_data="change_creds")],
        [InlineKeyboardButton(get_text(lang, 'btn_back_inline'), callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_teacher_main_menu(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [get_text(lang, 'btn_schedule'), get_text(lang, 'btn_attendance')],
        [get_text(lang, 'btn_grades'), get_text(lang, 'btn_settings')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder=get_text(lang, 'main_menu'))

def get_teacher_schedule_menu(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [get_text(lang, 'btn_schedule_today'), get_text(lang, 'btn_schedule_tomorrow')],
        [get_text(lang, 'btn_schedule_full')],
        [get_text(lang, 'btn_back')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_teacher_class_list(class_list: list, callback_prefix: str, lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(class_id, callback_data=f"{callback_prefix}{class_id}")]
        for class_id in class_list
    ]
    keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back_inline'), callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_student_list_keyboard(student_list: list, callback_prefix: str, lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(username, callback_data=f"{callback_prefix}{username}")]
        for username in student_list
    ]
    keyboard.append([InlineKeyboardButton(get_text(lang, 'btn_back_inline'), callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_attendance_keyboard(student_username: str, lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(get_text(lang, 'btn_att_present'), callback_data=f"att_mark_present_{student_username}"),
            InlineKeyboardButton(get_text(lang, 'btn_att_absent'), callback_data=f"att_mark_absent_{student_username}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_grades_set_keyboard(student_username: str, subject: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("2", callback_data=f"grade_set_2_{subject}_{student_username}"),
            InlineKeyboardButton("3", callback_data=f"grade_set_3_{subject}_{student_username}"),
        ],
        [
            InlineKeyboardButton("4", callback_data=f"grade_set_4_{subject}_{student_username}"),
            InlineKeyboardButton("5", callback_data=f"grade_set_5_{subject}_{student_username}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_main_menu(lang: str) -> ReplyKeyboardMarkup:
    keyboard = [
        [get_text(lang, 'btn_admin_schedule')],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder=get_text(lang, 'main_menu'))
