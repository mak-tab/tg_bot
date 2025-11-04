import logging
import datetime
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# --- Импорты из наших модулей ---
import database as db
import keyboards as kb

from bot import (
    STUDENT_MAIN, 
    TEACHER_MAIN, 
    ADMIN_MAIN,
    TEACHER_SCHEDULE,
    TEACHER_ATTENDANCE_SELECT_CLASS,
    TEACHER_ATTENDANCE_SELECT_LETTER,
    TEACHER_ATTENDANCE_MARK_STUDENT,
    TEACHER_GRADES_SELECT_CLASS,
    TEACHER_GRADES_SELECT_LETTER,
    TEACHER_GRADES_SELECT_STUDENT,
    TEACHER_GRADES_MARK_STUDENT,
    TEACHER_SETTINGS,
    TEACHER_SETTINGS_CHANGE_LOGIN,
    TEACHER_SETTINGS_CHANGE_PASS
)

# --- Настройка логирования ---
logger = logging.getLogger(__name__)

# --- Локализация ---
MESSAGES = {
    'ru': {
        'back_to_main': "Главное меню",
        'feature_in_development': "Этот раздел в разработке.",
        'schedule_menu': "Выберите, какое расписание вы хотите посмотреть:",
        'attendance_select_class': "Посещаемость: Выберите класс",
        'attendance_select_letter': "Посещаемость: Выберите букву",
        'attendance_select_student': "Посещаемость: Выберите ученика ({class_letter})",
        'attendance_marking': "Отметьте присутствие для <b>{name}</b>:",
        'attendance_marked': "✅ <b>{name}</b>: {status_icon}",
        'grades_select_class': "Оценки: Выберите класс",
        'grades_select_letter': "Оценки: Выберите букву",
        'grades_select_student': "Оценки: Выберите ученика ({class_letter})",
        'grades_marking': "Выставьте оценку для <b>{name}</b> по предмету <b>{subject}</b>:",
        'grades_marked_success': "✅ Оценка <b>{grade}</b> для <b>{name}</b> по предмету <b>{subject}</b> сохранена на {date}.",
        'settings_menu': "Ваши настройки.\nНажимайте на кнопки, чтобы изменить их.",
        'settings_prompt_login': "Введите ваш новый <b>логин</b>.\n\n(Чтобы отменить, напишите /cancel)",
        'settings_prompt_pass': "Отлично, логин <code>{login}</code>.\nТеперь введите ваш новый <b>пароль</b>.\n\n(Чтобы отменить, напишите /cancel)",
        'settings_changed_success': "✅ Ваш логин и пароль успешно изменены.",
        'settings_change_cancelled': "Изменение отменено.",
    },
    'en': {
        'back_to_main': "Main menu",
        'feature_in_development': "This section is under development.",
        'schedule_menu': "Select which schedule you want to view:",
        'attendance_select_class': "Attendance: Select class",
        'attendance_select_letter': "Attendance: Select letter",
        'attendance_select_student': "Attendance: Select student ({class_letter})",
        'attendance_marking': "Mark attendance for <b>{name}</b>:",
        'attendance_marked': "✅ <b>{name}</b>: {status_icon}",
        'grades_select_class': "Grades: Select class",
        'grades_select_letter': "Grades: Select letter",
        'grades_select_student': "Grades: Select student ({class_letter})",
        'grades_marking': "Set grade for <b>{name}</b> in <b>{subject}</b>:",
        'grades_marked_success': "✅ Grade <b>{grade}</b> for <b>{name}</b> in <b>{subject}</b> saved for {date}.",
        'settings_menu': "Your settings.\nPress the buttons to change them.",
        'settings_prompt_login': "Enter your new <b>username</b>.\n\n(To cancel, type /cancel)",
        'settings_prompt_pass': "Great, username is <code>{login}</code>.\nNow enter your new <b>password</b>.\n\n(To cancel, type /cancel)",
        'settings_changed_success': "✅ Your username and password have been successfully changed.",
        'settings_change_cancelled': "Change cancelled.",
    },
    'uz': {
        'back_to_main': "Asosiy menyu",
        'feature_in_development': "Ushbu bo'lim ishlab chiqilmoqda.",
        'schedule_menu': "Qaysi dars jadvalini ko'rmoqchisiz:",
        'attendance_select_class': "Davomat: Sinfni tanlang",
        'attendance_select_letter': "Davomat: Harfni tanlang",
        'attendance_select_student': "Davomat: O'quvchini tanlang ({class_letter})",
        'attendance_marking': "<b>{name}</b> uchun davomatni belgilang:",
        'attendance_marked': "✅ <b>{name}</b>: {status_icon}",
        'grades_select_class': "Baholar: Sinfni tanlang",
        'grades_select_letter': "Baholar: Harfni tanlang",
        'grades_select_student': "Baholar: O'quvchini tanlang ({class_letter})",
        'grades_marking': "<b>{name}</b> uchun <b>{subject}</b> fani bo'yicha baho qo'ying:",
        'grades_marked_success': "✅ <b>{name}</b> uchun <b>{subject}</b> fanidan <b>{grade}</b> bahosi {date} sanasiga saqlandi.",
        'settings_menu': "Sizning sozlamalaringiz.\nO'zgartirish uchun tugmalarni bosing.",
        'settings_prompt_login': "Yangi <b>login</b> kiriting.\n\n(Bekor qilish uchun /cancel yozing)",
        'settings_prompt_pass': "Ajoyib, login <code>{login}</code>.\nEndi yangi <b>parolni</b> kiriting.\n\n(Bekor qilish uchun /cancel yozing)",
        'settings_changed_success': "✅ Login va parolingiz muvaffaqiyatli o'zgartirildi.",
        'settings_change_cancelled': "O'zgartirish bekor qilindi.",
    }
}

def get_tchr_msg(key, lang='ru'):
    return MESSAGES.get(lang, MESSAGES['ru']).get(key, f"_{key}_")

# --- Вспомогательные функции ---

def get_user_data(context: ContextTypes.DEFAULT_TYPE):
    """Возвращает (lang, user_info, db_id) из context."""
    lang = context.user_data.get('lang', 'ru')
    user_info = context.user_data.get('user_info', {})
    db_id = context.user_data.get('db_id')
    return lang, user_info, db_id

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Возвращает пользователя в главное меню учителя."""
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_tchr_msg('back_to_main', lang),
        reply_markup=kb.get_teacher_main_keyboard(lang)
    )
    return TEACHER_MAIN

async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Обрабатывает нажатие Inline-кнопки 'Назад' и возвращает в гл. меню."""
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    await query.message.reply_text(
        get_tchr_msg('back_to_main', lang),
        reply_markup=kb.get_teacher_main_keyboard(lang)
    )
    await query.message.delete()
    return TEACHER_MAIN

def _get_all_classes_and_letters():
    """
    Собирает словарь всех классов и букв из базы учеников.
    Возвращает: {'9': ['А', 'Б'], '10': ['А']}
    """
    students = db.get_all_students()
    classes = {}
    for student_data in students.values():
        class_num = student_data.get('class')
        letter = student_data.get('letter')
        if class_num and letter:
            if class_num not in classes:
                classes[class_num] = set()
            classes[class_num].add(letter)
    
    # Конвертируем в отсортированные списки
    sorted_classes = {k: sorted(list(v)) for k, v in classes.items()}
    # Сортируем сами классы (9, 10, 11)
    sorted_keys = sorted(sorted_classes.keys(), key=lambda x: int(x))
    return {k: sorted_classes[k] for k in sorted_keys}

def _get_students_by_class(class_num, letter):
    """
    Получает список учеников (id, first_name, last_name) 
    по номеру класса и букве.
    """
    students = db.get_all_students()
    matches = []
    for student_id, student_data in students.items():
        if student_data.get('class') == class_num and student_data.get('letter') == letter:
            matches.append({
                'id': student_id, # Это db_id ученика
                'first_name': student_data.get('first_name', ''),
                'last_name': student_data.get('last_name', '')
            })
    # Сортируем по Фамилии, затем по Имени
    return sorted(matches, key=lambda x: (x.get('last_name', ''), x.get('first_name', '')))

# --- 1. Обработчики главного меню (TEACHER_MAIN) ---

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Переводит в меню 'Расписание'."""
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_tchr_msg('schedule_menu', lang),
        reply_markup=kb.get_teacher_schedule_keyboard(lang)
    )
    return TEACHER_SCHEDULE

async def handle_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Начинает процесс 'Посещаемость' - выбор класса."""
    lang, _, _ = get_user_data(context)
    classes_dict = _get_all_classes_and_letters()
    
    if not classes_dict:
        await update.message.reply_text("В базе нет учеников.")
        return TEACHER_MAIN
        
    await update.message.reply_text(
        get_tchr_msg('attendance_select_class', lang),
        reply_markup=kb.generate_class_list_keyboard(
            classes_list=classes_dict.keys(),
            callback_prefix='att_class_',
            lang=lang
        )
    )
    return TEACHER_ATTENDANCE_SELECT_LETTER

async def handle_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Начинает процесс 'Оценки' - выбор класса."""
    lang, _, _ = get_user_data(context)
    classes_dict = _get_all_classes_and_letters()
    
    if not classes_dict:
        await update.message.reply_text("В базе нет учеников.")
        return TEACHER_MAIN
        
    await update.message.reply_text(
        get_tchr_msg('grades_select_class', lang),
        reply_markup=kb.generate_class_list_keyboard(
            classes_list=classes_dict.keys(),
            callback_prefix='grade_class_',
            lang=lang
        )
    )
    return TEACHER_GRADES_SELECT_LETTER

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Переводит в меню 'Настройки'."""
    lang, user_info, _ = get_user_data(context)
    await update.message.reply_text(
        get_tchr_msg('settings_menu', lang),
        reply_markup=kb.generate_settings_keyboard(user_info, lang)
    )
    return TEACHER_SETTINGS

# --- 2. Обработчики 'Расписание' (TEACHER_SCHEDULE) ---
# (Заглушка, т.к. нет данных для персонального расписания)

async def show_schedule_placeholder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Заглушка для кнопок 'Сегодня', 'Завтра', 'Полностью'."""
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(get_tchr_msg('feature_in_development', lang))
    return TEACHER_SCHEDULE

# --- 3. Обработчики 'Посещаемость' (CallbackQuery) ---

async def select_attendance_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Выбрали класс. Показываем буквы."""
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    class_num = query.data.split('att_class_')[-1]
    classes_dict = _get_all_classes_and_letters()
    letters_list = classes_dict.get(class_num, [])
    
    await query.edit_message_text(
        get_tchr_msg('attendance_select_letter', lang),
        reply_markup=kb.generate_letter_list_keyboard(
            letters_list=letters_list,
            class_num=class_num,
            callback_prefix='att_letter_',
            lang=lang
        )
    )
    return TEACHER_ATTENDANCE_SELECT_LETTER

async def select_attendance_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Выбрали букву. Показываем учеников."""
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    # 'att_letter_10_А'
    class_num, letter = query.data.split('att_letter_')[-1].split('_')
    
    students_list = _get_students_by_class(class_num, letter)
    
    await query.edit_message_text(
        get_tchr_msg('attendance_select_student', lang).format(class_letter=f"{class_num}{letter}"),
        reply_markup=kb.generate_students_list_keyboard(
            students_data=students_list,
            class_num=class_num,
            letter=letter,
            callback_prefix='att_student_',
            lang=lang
        )
    )
    return TEACHER_ATTENDANCE_MARK_STUDENT
    
async def select_attendance_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Выбрали ученика. Показываем кнопки 'Присутствует/Отсутствует'."""
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    student_id = query.data.split('att_student_')[-1]
    
    # Нам нужно имя ученика
    all_students = db.get_all_students()
    student_data = all_students.get(student_id)
    if not student_data:
        await query.edit_message_text("Ошибка: Ученик не найден.")
        return TEACHER_MAIN
        
    name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
    
    # Сохраняем ID ученика во временный context
    context.user_data['selected_student_id'] = student_id
    context.user_data['selected_student_name'] = name
    
    await query.edit_message_text(
        get_tchr_msg('attendance_marking', lang).format(name=name),
        reply_markup=kb.get_attendance_markup(lang),
        parse_mode='HTML'
    )
    # Остаемся в том же состоянии, ждем нажатия 'att_present'/'att_absent'
    return TEACHER_ATTENDANCE_MARK_STUDENT

async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Сохраняет отметку о посещаемости."""
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    status = query.data # 'att_present' или 'att_absent'
    student_id = context.user_data.pop('selected_student_id', None)
    student_name = context.user_data.pop('selected_student_name', 'N/A')
    
    if not student_id:
        await query.edit_message_text("Ошибка: ID ученика не найден. Попробуйте снова.")
        return TEACHER_MAIN
        
    status_text = 'present' if status == 'att_present' else 'absent'
    status_icon = '✅' if status == 'att_present' else '❌'
    
    # Сохранение в data.json
    # Структура: data['attendance']['YYYY-MM-DD']['student_id'] = 'present'/'absent'
    today_str = datetime.date.today().isoformat()
    
    app_data = db.get_app_data()
    if 'attendance' not in app_data:
        app_data['attendance'] = {}
    if today_str not in app_data['attendance']:
        app_data['attendance'][today_str] = {}
        
    app_data['attendance'][today_str][student_id] = status_text
    db.save_app_data(app_data)
    
    # Редактируем сообщение, как просил пользователь
    await query.edit_message_text(
        get_tchr_msg('attendance_marked', lang).format(name=student_name, status_icon=status_icon),
        parse_mode='HTML'
    )
    
    # TODO: Нужно вернуть пользователя к списку учеников
    # (Это требует запоминания class_num и letter в context)
    # Пока вернем в главное меню для простоты
    return await back_to_main_callback(update, context)

# --- 4. Обработчики 'Оценки' (CallbackQuery) ---

async def select_grades_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Выбрали класс. Показываем буквы."""
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    class_num = query.data.split('grade_class_')[-1]
    classes_dict = _get_all_classes_and_letters()
    letters_list = classes_dict.get(class_num, [])
    
    await query.edit_message_text(
        get_tchr_msg('grades_select_letter', lang),
        reply_markup=kb.generate_letter_list_keyboard(
            letters_list=letters_list,
            class_num=class_num,
            callback_prefix='grade_letter_',
            lang=lang
        )
    )
    return TEACHER_GRADES_SELECT_LETTER

async def select_grades_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Выбрали букву. Показываем учеников."""
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    class_num, letter = query.data.split('grade_letter_')[-1].split('_')
    
    students_list = _get_students_by_class(class_num, letter)
    
    await query.edit_message_text(
        get_tchr_msg('grades_select_student', lang).format(class_letter=f"{class_num}{letter}"),
        reply_markup=kb.generate_students_list_keyboard(
            students_data=students_list,
            class_num=class_num,
            letter=letter,
            callback_prefix='grade_student_',
            lang=lang
        )
    )
    return TEACHER_GRADES_SELECT_STUDENT

async def select_grades_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Выбрали ученика. Показываем кнопки '2, 3, 4, 5'."""
    query = update.callback_query
    await query.answer()
    lang, user_info, _ = get_user_data(context)
    
    student_id = query.data.split('grade_student_')[-1]
    
    all_students = db.get_all_students()
    student_data = all_students.get(student_id)
    if not student_data:
        await query.edit_message_text("Ошибка: Ученик не найден.")
        return TEACHER_MAIN
        
    name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
    teacher_subject = user_info.get('subject', 'N/A')
    
    context.user_data['selected_student_id'] = student_id
    context.user_data['selected_student_name'] = name
    
    await query.edit_message_text(
        get_tchr_msg('grades_marking', lang).format(name=name, subject=teacher_subject),
        reply_markup=kb.get_grades_markup(lang),
        parse_mode='HTML'
    )
    return TEACHER_GRADES_MARK_STUDENT

async def set_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Сохраняет оценку."""
    query = update.callback_query
    await query.answer()
    lang, user_info, _ = get_user_data(context)
    
    grade = query.data.split('grade_')[-1] # '2', '3', '4', '5'
    student_id = context.user_data.pop('selected_student_id', None)
    student_name = context.user_data.pop('selected_student_name', 'N/A')
    teacher_subject = user_info.get('subject')
    
    if not student_id or not teacher_subject:
        await query.edit_message_text("Ошибка: ID ученика или предмет учителя не найден. Попробуйте снова.")
        return TEACHER_MAIN
        
    # Сохранение в data.json
    # Структура: data['grades']['student_db_id']['subject']['YYYY-MM-DD'] = 'grade'
    today_str = datetime.date.today().isoformat()
    
    app_data = db.get_app_data()
    if 'grades' not in app_data:
        app_data['grades'] = {}
    if student_id not in app_data['grades']:
        app_data['grades'][student_id] = {}
    if teacher_subject not in app_data['grades'][student_id]:
        app_data['grades'][student_id][teacher_subject] = {}
        
    # Записываем оценку (перезаписываем, если в этот день уже была)
    app_data['grades'][student_id][teacher_subject][today_str] = grade
    db.save_app_data(app_data)
    
    await query.edit_message_text(
        get_tchr_msg('grades_marked_success', lang).format(
            grade=grade, 
            name=student_name, 
            subject=teacher_subject, 
            date=today_str
        ),
        parse_mode='HTML'
    )
    
    # TODO: Вернуть к списку учеников
    return await back_to_main_callback(update, context)

# --- 5. Обработчики 'Настройки' (TEACHER_SETTINGS) ---
# (Этот код почти идентичен student.py, но работает с teachers.json)

async def _toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, setting_key: str) -> str:
    query = update.callback_query
    await query.answer()
    lang, user_info, db_id = get_user_data(context)
    
    current_value = user_info.get(setting_key, False)
    new_value = not current_value
    user_info[setting_key] = new_value
    context.user_data['user_info'] = user_info
    
    all_teachers = db.get_all_teachers()
    if db_id in all_teachers:
        all_teachers[db_id][setting_key] = new_value
        db.save_all_teachers(all_teachers)
    else:
        logger.error(f"Не удалось сохранить настройку {setting_key} для {db_id} (учитель).")
        
    await query.edit_message_reply_markup(
        reply_markup=kb.generate_settings_keyboard(user_info, lang)
    )
    return TEACHER_SETTINGS

async def toggle_next_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    return await _toggle_setting(update, context, 'warning_about_next_lesson')

async def toggle_daily_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    return await _toggle_setting(update, context, 'warning_everyday_about_lessons')

async def start_change_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    await query.delete_message()
    await query.message.reply_text(
        get_tchr_msg('settings_prompt_login', lang),
        parse_mode='HTML'
    )
    return TEACHER_SETTINGS_CHANGE_LOGIN

async def receive_new_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    new_login = update.message.text
    
    if len(new_login.split()) > 1:
        await update.message.reply_text("Логин не должен содержать пробелов. Попробуйте еще раз.")
        return TEACHER_SETTINGS_CHANGE_LOGIN

    context.user_data['new_login'] = new_login.lower()
    await update.message.reply_text(
        get_tchr_msg('settings_prompt_pass', lang).format(login=new_login),
        parse_mode='HTML'
    )
    return TEACHER_SETTINGS_CHANGE_PASS
    
async def receive_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, db_id = get_user_data(context)
    new_pass = update.message.text
    new_login = context.user_data.pop('new_login', None)
    
    if not new_login:
        await update.message.reply_text("Произошла ошибка, попробуйте снова.")
        return await back_to_main(update, context)

    user_info['username'] = new_login
    user_info['password'] = new_pass
    context.user_data['user_info'] = user_info
    
    all_teachers = db.get_all_teachers()
    if db_id in all_teachers:
        all_teachers[db_id]['username'] = new_login
        all_teachers[db_id]['password'] = new_pass
        db.save_all_teachers(all_teachers)
    else:
        logger.error(f"Не удалось сохранить новый логин/пароль для {db_id} (учитель).")
        
    await update.message.reply_text(get_tchr_msg('settings_changed_success', lang))
    return await back_to_main(update, context)

async def cancel_change_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    context.user_data.pop('new_login', None)
    await update.message.reply_text(get_tchr_msg('settings_change_cancelled', lang))
    return await back_to_main(update, context)
