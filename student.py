import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
import database as db
import keyboards as kb

logger = logging.getLogger(__name__)

from bot import ( STUDENT_MAIN, TEACHER_MAIN, ADMIN_MAIN, 
                STUDENT_SCHEDULE, STUDENT_GRADES, STUDENT_SETTINGS, 
                STUDENT_SETTINGS_CHANGE_LOGIN, STUDENT_SETTINGS_CHANGE_PASS
)

MESSAGES = {
    'ru': {
        'schedule_menu': "Выберите, какое расписание вы хотите посмотреть:",
        'grades_menu': "Выберите предмет, чтобы посмотреть оценки:",
        'settings_menu': "Ваши настройки.\nНажимайте на кнопки, чтобы изменить их.",
        'no_grades': "У вас пока нет оценок.",
        'no_subjects': "Не удалось найти предметы. Обратитесь к администратору.",
        'schedule_not_found': "Не удалось найти расписание для вашего класса ({class_letter}).",
        'grades_title': "Оценки по предмету <b>{subject}</b>:",
        'grades_line': "• {date}: <b>{grade}</b>",
        'settings_prompt_login': "Введите ваш новый <b>логин</b>.\n\n(Чтобы отменить, напишите /cancel)",
        'settings_prompt_pass': "Отлично, логин <code>{login}</code>.\nТеперь введите ваш новый <b>пароль</b>.\n\n(Чтобы отменить, напишите /cancel)",
        'settings_changed_success': "✅ Ваш логин и пароль успешно изменены.",
        'settings_change_cancelled': "Изменение отменено.",
        'back_to_main': "Главное меню",
        'schedule_tomorrow_title': "Расписание на завтра ({day_name}):",
        'schedule_full_title': "Полное расписание для {class_letter} класса:",
        'day_monday': "Понедельник",
        'day_tuesday': "Вторник",
        'day_wednesday': "Среда",
        'day_thursday': "Четверг",
        'day_friday': "Пятница",
        'day_saturday': "Суббота",
        'day_sunday': "Воскресенье",
    },
    'en': {
        'schedule_menu': "Select which schedule you want to view:",
        'grades_menu': "Select a subject to view grades:",
        'settings_menu': "Your settings.\nPress the buttons to change them.",
        'no_grades': "You have no grades yet.",
        'no_subjects': "Could not find subjects. Contact the administrator.",
        'schedule_not_found': "Could not find schedule for your class ({class_letter}).",
        'grades_title': "Grades for <b>{subject}</b>:",
        'grades_line': "• {date}: <b>{grade}</b>",
        'settings_prompt_login': "Enter your new <b>username</b>.\n\n(To cancel, type /cancel)",
        'settings_prompt_pass': "Great, username is <code>{login}</code>.\nNow enter your new <b>password</b>.\n\n(To cancel, type /cancel)",
        'settings_changed_success': "✅ Your username and password have been successfully changed.",
        'settings_change_cancelled': "Change cancelled.",
        'back_to_main': "Main menu",
        'schedule_tomorrow_title': "Schedule for tomorrow ({day_name}):",
        'schedule_full_title': "Full schedule for class {class_letter}:",
        'day_monday': "Monday",
        'day_tuesday': "Tuesday",
        'day_wednesday': "Wednesday",
        'day_thursday': "Thursday",
        'day_friday': "Friday",
        'day_saturday': "Saturday",
        'day_sunday': "Sunday",
    },
    'uz': {
        'schedule_menu': "Qaysi dars jadvalini ko'rmoqchisiz:",
        'grades_menu': "Baholarni ko'rish uchun fanni tanlang:",
        'settings_menu': "Sizning sozlamalaringiz.\nO'zgartirish uchun tugmalarni bosing.",
        'no_grades': "Sizda hozircha baholar yo'q.",
        'no_subjects': "Fanlar topilmadi. Ma'muriyatga murojaat qiling.",
        'schedule_not_found': "Sinfingiz ({class_letter}) uchun dars jadvali topilmadi.",
        'grades_title': "<b>{subject}</b> fani bo'yicha baholar:",
        'grades_line': "• {date}: <b>{grade}</b>",
        'settings_prompt_login': "Yangi <b>login</b> kiriting.\n\n(Bekor qilish uchun /cancel yozing)",
        'settings_prompt_pass': "Ajoyib, login <code>{login}</code>.\nEndi yangi <b>parolni</b> kiriting.\n\n(Bekor qilish uchun /cancel yozing)",
        'settings_changed_success': "✅ Login va parolingiz muvaffaqiyatli o'zgartirildi.",
        'settings_change_cancelled': "O'zgartirish bekor qilindi.",
        'back_to_main': "Asosiy menyu",
        'schedule_tomorrow_title': "Ertangi kun uchun dars jadvali ({day_name}):",
        'schedule_full_title': "{class_letter}-sinf uchun to'liq dars jadvali:",
        'day_monday': "Dushanba",
        'day_tuesday': "Seshanba",
        'day_wednesday': "Chorshanba",
        'day_thursday': "Payshanba",
        'day_friday': "Juma",
        'day_saturday': "Shanba",
        'day_sunday': "Yakshanba",
    }
}

def get_std_msg(key, lang='ru'):
    return MESSAGES.get(lang, MESSAGES['ru']).get(key, f"_{key}_")

def get_user_data(context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    user_info = context.user_data.get('user_info', {})
    db_id = context.user_data.get('db_id')
    return lang, user_info, db_id

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_std_msg('back_to_main', lang),
        reply_markup=kb.get_student_main_keyboard(lang)
    )
    return STUDENT_MAIN

async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    await query.message.reply_text(
        get_std_msg('back_to_main', lang),
        reply_markup=kb.get_student_main_keyboard(lang)
    )
    await query.message.delete()
    return STUDENT_MAIN

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_std_msg('schedule_menu', lang),
        reply_markup=kb.get_student_schedule_keyboard(lang)
    )
    return STUDENT_SCHEDULE

async def handle_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, db_id = get_user_data(context)
    
    all_data = db.get_app_data()
    user_grades = all_data.get('grades', {}).get(db_id, {})
    
    subjects_list = list(user_grades.keys())
    
    if not subjects_list:
        await update.message.reply_text(get_std_msg('no_grades', lang))
        return STUDENT_MAIN
        
    await update.message.reply_text(
        get_std_msg('grades_menu', lang),
        reply_markup=kb.generate_subjects_keyboard(subjects_list, lang)
    )
    return STUDENT_GRADES

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, _ = get_user_data(context)
    await update.message.reply_text(
        get_std_msg('settings_menu', lang),
        reply_markup=kb.generate_settings_keyboard(user_info, lang)
    )
    return STUDENT_SETTINGS

def _format_schedule_for_day(schedule_data, day_name_key, lang):
    if not schedule_data:
        return "  (Нет уроков)"
    
    day_name = get_std_msg(day_name_key, lang)
    lines = [f"<b>{day_name}</b>:"]
    for lesson_num in sorted(schedule_data.keys(), key=lambda x: int(x)):
        lesson_name = schedule_data[lesson_num]
        lines.append(f"  {lesson_num}. {lesson_name}")
    return "\n".join(lines)


async def show_schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, _ = get_user_data(context)
    
    user_class = user_info.get('class')
    user_letter = user_info.get('letter')
    if not user_class or not user_letter:
        await update.message.reply_text("Ошибка: Ваш класс не указан в профиле.")
        return STUDENT_SCHEDULE
        
    class_key = f"{user_class}{user_letter}"
    
    schedule_db = db.get_schedule()
    class_schedule = schedule_db.get(class_key)
    
    if not class_schedule:
        await update.message.reply_text(get_std_msg('schedule_not_found', lang).format(class_letter=class_key))
        return STUDENT_SCHEDULE
        
    import datetime
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    day_of_week_index = tomorrow.weekday()
    
    day_keys = ['day_monday', 'day_tuesday', 'day_wednesday', 'day_thursday', 'day_friday', 'day_saturday', 'day_sunday']
    day_db_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    tomorrow_key = day_db_keys[day_of_week_index]
    tomorrow_name_key = day_keys[day_of_week_index]
    
    schedule_for_tomorrow = class_schedule.get(tomorrow_key, {})
    
    formatted_schedule = _format_schedule_for_day(schedule_for_tomorrow, tomorrow_name_key, lang)
    
    await update.message.reply_text(
        get_std_msg('schedule_tomorrow_title', lang).format(day_name=get_std_msg(tomorrow_name_key, lang)) + "\n" + formatted_schedule,
        parse_mode='HTML'
    )
    return STUDENT_SCHEDULE

async def show_schedule_full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, _ = get_user_data(context)
    
    user_class = user_info.get('class')
    user_letter = user_info.get('letter')
    class_key = f"{user_class}{user_letter}"
    
    schedule_db = db.get_schedule()
    class_schedule = schedule_db.get(class_key)
    
    if not class_schedule:
        await update.message.reply_text(get_std_msg('schedule_not_found', lang).format(class_letter=class_key))
        return STUDENT_SCHEDULE

    day_keys = ['day_monday', 'day_tuesday', 'day_wednesday', 'day_thursday', 'day_friday', 'day_saturday', 'day_sunday']
    day_db_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    full_schedule_lines = [get_std_msg('schedule_full_title', lang).format(class_letter=class_key)]
    
    for i in range(len(day_db_keys)):
        day_db_key = day_db_keys[i]
        day_name_key = day_keys[i]
        day_schedule = class_schedule.get(day_db_key, {})
        full_schedule_lines.append(_format_schedule_for_day(day_schedule, day_name_key, lang))
        
    await update.message.reply_text("\n\n".join(full_schedule_lines), parse_mode='HTML')
    return STUDENT_SCHEDULE

async def show_grades_for_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    
    lang, _, db_id = get_user_data(context)
    
    try:
        subject = query.data.split('grade_subj_')[-1]
    except Exception:
        await query.edit_message_text("Ошибка: не удалось распознать предмет.")
        return STUDENT_GRADES
        
    all_data = db.get_app_data()
    user_grades = all_data.get('grades', {}).get(db_id, {})
    subject_grades = user_grades.get(subject, {})
    
    if not subject_grades:
        await query.edit_message_text(get_std_msg('no_grades', lang))
        return STUDENT_GRADES
        
    lines = [get_std_msg('grades_title', lang).format(subject=subject)]
    try:
        sorted_dates = sorted(subject_grades.keys())
    except Exception:
        sorted_dates = subject_grades.keys()

    for date in sorted_dates:
        grade = subject_grades[date]
        lines.append(get_std_msg('grades_line', lang).format(date=date, grade=grade))
    
    subjects_list = list(user_grades.keys())
    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=kb.generate_subjects_keyboard(subjects_list, lang),
        parse_mode='HTML'
    )
    
    return STUDENT_GRADES

async def _toggle_setting(update: Update, context: ContextTypes.DEFAULT_TYPE, setting_key: str) -> str:
    query = update.callback_query
    await query.answer()
    
    lang, user_info, db_id = get_user_data(context)
    
    current_value = user_info.get(setting_key, False)
    new_value = not current_value
    user_info[setting_key] = new_value
    
    context.user_data['user_info'] = user_info
    
    all_students = db.get_all_students()
    if db_id in all_students:
        all_students[db_id][setting_key] = new_value
        db.save_all_students(all_students)
    else:
        logger.error(f"Не удалось сохранить настройку {setting_key} для {db_id}. Пользователь не найден.")
        
    await query.edit_message_reply_markup(
        reply_markup=kb.generate_settings_keyboard(user_info, lang)
    )
    
    return STUDENT_SETTINGS

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
        get_std_msg('settings_prompt_login', lang),
        parse_mode='HTML'
    )
    return STUDENT_SETTINGS_CHANGE_LOGIN

async def receive_new_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    new_login = update.message.text
    
    if len(new_login.split()) > 1:
        await update.message.reply_text("Логин не должен содержать пробелов. Попробуйте еще раз.")
        return STUDENT_SETTINGS_CHANGE_LOGIN

    context.user_data['new_login'] = new_login.lower()
    
    await update.message.reply_text(
        get_std_msg('settings_prompt_pass', lang).format(login=new_login),
        parse_mode='HTML'
    )
    return STUDENT_SETTINGS_CHANGE_PASS
    
async def receive_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, db_id = get_user_data(context)
    
    new_pass = update.message.text
    new_login = context.user_data.pop('new_login', None)
    
    if not new_login:
        logger.warning(f"Ошибка смены пароля: new_login не найден в context. {db_id}")
        await update.message.reply_text("Произошла ошибка, попробуйте снова.")
        return await back_to_main(update, context)

    user_info['username'] = new_login
    user_info['password'] = new_pass
    context.user_data['user_info'] = user_info
    
    all_students = db.get_all_students()
    if db_id in all_students:
        all_students[db_id]['username'] = new_login
        all_students[db_id]['password'] = new_pass
        db.save_all_students(all_students)
    else:
        logger.error(f"Не удалось сохранить новый логин/пароль для {db_id}.")
        
    await update.message.reply_text(get_std_msg('settings_changed_success', lang))
    
    return await back_to_main(update, context)

async def cancel_change_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    context.user_data.pop('new_login', None)
    
    await update.message.reply_text(get_std_msg('settings_change_cancelled', lang))
    return await back_to_main(update, context)

