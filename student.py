from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import db_handler
import keyboards
from utils import TZ, get_day_of_week_str 
from states import (
    STATE_MENU_STUDENT, STATE_STUDENT_SCHEDULE, STATE_STUDENT_GRADES, 
    STATE_STUDENT_SETTINGS, STATE_SETTINGS_CHANGE_CREDS
)

from datetime import datetime, timedelta
from localization import get_text

# --- Роутеры (Маршрутизаторы) ---

async def route_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Маршрутизатор для главного меню ученика."""
    lang = context.user_data.get('lang', 'uz')
    text = update.message.text

    # Сравниваем текст с локализованными кнопками
    if text == get_text(lang, 'btn_schedule'):
        return await handle_schedule(update, context)
    elif text == get_text(lang, 'btn_grades'):
        return await handle_grades(update, context)
    elif text == get_text(lang, 'btn_settings'):
        return await handle_settings(update, context)
    else:
        # ИЗМЕНЕНО: Ответ на неизвестную команду
        await update.message.reply_text(get_text(lang, 'unknown_command'))
        return STATE_MENU_STUDENT

# ИЗМЕНЕНО: Добавлен НОВЫЙ роутер для подменю "Расписание"
async def route_schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Маршрутизатор для меню 'Расписание'."""
    lang = context.user_data.get('lang', 'uz')
    text = update.message.text

    if text == get_text(lang, 'btn_schedule_tomorrow'):
        return await send_schedule_tomorrow(update, context)
    elif text == get_text(lang, 'btn_schedule_full'):
        return await send_schedule_full(update, context)
    elif text == get_text(lang, 'btn_back'):
        return await back_to_main_menu(update, context)
    else:
        await update.message.reply_text(get_text(lang, 'unknown_command'))
        return STATE_STUDENT_SCHEDULE

# --- Обработка главного меню ---

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает кнопки выбора расписания."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    await update.message.reply_text(
        # ИЗМЕНЕНО: Используем get_text
        get_text(lang, 'choose_schedule_type'),
        # ИЗМЕНЕНО: Передаем lang в клавиатуру
        reply_markup=keyboards.get_student_schedule_menu(lang)
    )
    return STATE_STUDENT_SCHEDULE

async def handle_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает Inline кнопки с предметами."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    username = context.user_data.get("username")
    subjects = db_handler.get_subjects_for_student(username)
    
    if not subjects:
        # ИЗМЕНЕНО: Используем get_text
        await update.message.reply_text(get_text(lang, 'no_grades_found'))
        return STATE_MENU_STUDENT
        
    await update.message.reply_text(
        # ИЗМЕНЕНО: Используем get_text
        get_text(lang, 'choose_subject_grades'),
        # ИЗМЕНЕНО: Передаем lang в клавиатуру
        reply_markup=keyboards.get_subjects_keyboard(subjects, lang)
    )
    return STATE_STUDENT_GRADES

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает Inline кнопки настроек."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    user_id = update.effective_user.id
    settings = db_handler.get_user_settings(user_id)
    
    await update.message.reply_text(
        # ИЗМЕНЕНО: Используем get_text
        get_text(lang, 'your_settings'),
        # ИЗМЕНЕНО: Передаем lang в клавиатуру
        reply_markup=keyboards.get_settings_keyboard(settings, lang)
    )
    return STATE_STUDENT_SETTINGS

# --- Обработка подменю ---

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат в главное меню (для Reply кнопок)."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    await update.message.reply_text(
        # ИЗМЕНЕНО: Используем get_text
        get_text(lang, 'main_menu'),
        # ИЗМЕНЕНО: Передаем lang в клавиатуру
        reply_markup=keyboards.get_student_main_menu(lang)
    )
    return STATE_MENU_STUDENT

async def back_to_main_menu_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат в главное меню (для Inline кнопок)."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    await query.delete_message()
    
    await query.message.reply_text(
        # ИЗМЕНЕНО: Используем get_text
        get_text(lang, 'main_menu'),
        # ИЗМЕНЕНО: Передаем lang в клавиатуру
        reply_markup=keyboards.get_student_main_menu(lang)
    )
    return STATE_MENU_STUDENT

async def send_schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет расписание на завтра."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    class_id = context.user_data.get("class_id")
    
    day_key = get_day_of_week_str('tomorrow')
    tomorrow_date = (datetime.now(TZ) + timedelta(days=1)).strftime('%d.%m.%Y')
    
    schedule = db_handler.get_schedule_for_class(class_id)
    # ИЗМЕНЕНО: Используем get_text для запасного варианта
    lessons_list = schedule.get(day_key, [get_text(lang, 'no_lessons_tomorrow')])
    lessons_str = "\n".join(lessons_list)
    
    # ИЗМЕНЕНО: Используем get_text для форматирования
    text = get_text(lang, 'schedule_for_tomorrow').format(
        class_id=class_id, 
        day_key=day_key.capitalize(), 
        date=tomorrow_date, 
        lessons=lessons_str
    )
    
    await update.message.reply_text(text)
    return STATE_STUDENT_SCHEDULE

async def send_schedule_full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет полное расписание."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    class_id = context.user_data.get("class_id")
    schedule = db_handler.get_schedule_for_class(class_id)
    
    if not schedule:
        # ИЗМЕНЕНО: Используем get_text
        await update.message.reply_text(get_text(lang, 'schedule_full_empty').format(class_id=class_id))
        return STATE_STUDENT_SCHEDULE

    # ИЗМЕНЕНО: Используем get_text
    text = get_text(lang, 'schedule_full_header').format(class_id=class_id)
    days_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    found_lessons = False
    for day in days_order:
        lessons = schedule.get(day)
        if lessons:
            found_lessons = True
            text += f"\n*{day.capitalize()}*:\n" + "\n".join(lessons) + "\n"
        
    if not found_lessons:
        # ИЗМЕНЕНО: Используем get_text
        text = get_text(lang, 'schedule_full_empty').format(class_id=class_id)

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return STATE_STUDENT_SCHEDULE

async def send_grades_for_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет оценки по выбранному предмету."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    subject = query.data.split("_", 1)[1]
    username = context.user_data.get("username")
    grades = db_handler.get_grades_by_subject(username, subject)
    
    if not grades:
        # ИЗМЕНЕНО: Используем get_text
        text = get_text(lang, 'no_grades_for_subject').format(subject=subject)
    else:
        # ИЗМЕНЕНО: Используем get_text
        text = get_text(lang, 'grades_for_subject').format(subject=subject, grades="\n".join(grades))
    
    await query.edit_message_text(text, reply_markup=query.message.reply_markup)
    return STATE_STUDENT_GRADES

# --- Обработка настроек ---

async def toggle_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Переключает настройку уведомлений."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    key = query.data.split("_", 1)[1] # notify_lesson или notify_schedule
    
    current_settings = db_handler.get_user_settings(user_id)
    new_value = not current_settings.get(key, False)
    db_handler.update_user_settings(user_id, key, new_value)
    
    # Обновляем клавиатуру
    new_settings = db_handler.get_user_settings(user_id)
    # ИЗМЕНЕНО: Передаем lang в клавиатуру
    await query.edit_message_reply_markup(reply_markup=keyboards.get_settings_keyboard(new_settings, lang))
    
    # ИЗМЕНЕНО: Используем get_text
    if key == 'notify_lesson' and new_value:
        await query.message.reply_text(get_text(lang, 'notify_lesson_toggled_on'), reply_markup=None) # type: ignore
    elif key == 'notify_schedule' and new_value:
         await query.message.reply_text(get_text(lang, 'notify_schedule_toggled_on'), reply_markup=None) # type: ignore
    
    return STATE_STUDENT_SETTINGS


async def change_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает новый логин и пароль."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    await query.delete_message()
    
    # ИЗМЕНЕНО: Используем get_text
    await query.message.reply_text(
        get_text(lang, 'ask_new_credentials'),
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_SETTINGS_CHANGE_CREDS

async def update_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обновляет логин и пароль."""
    # ИЗМЕНЕНО: Получаем lang
    lang = context.user_data.get('lang', 'uz')
    parts = update.message.text.split()
    
    if len(parts) != 2:
        # ИЗМЕНЕНО: Используем get_text
        await update.message.reply_text(get_text(lang, 'invalid_credentials_format'))
        return STATE_SETTINGS_CHANGE_CREDS
        
    new_username, new_password = parts[0], parts[1]
    current_username = context.user_data.get("username")
    
    success, message = db_handler.update_user_credentials(current_username, new_username, new_password)
    
    if success:
        # ИЗМЕНЕНО: Используем get_text
        await update.message.reply_text(get_text(lang, 'credentials_updated_success'))
        context.user_data["username"] = new_username.lower() # Обновляем в сессии
    else:
        # ИЗМЕНЕНО: Используем get_text
        await update.message.reply_text(get_text(lang, 'credentials_update_error').format(message=message))
        return STATE_SETTINGS_CHANGE_CREDS
        
    return await back_to_main_menu(update, context)