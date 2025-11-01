from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import db_handler
import keyboards

# ИЗМЕНЕНО: Добавлены импорты
from localization import get_text
import student # Будем использовать student.handle_settings

from utils import TZ, get_day_of_week_str, get_today_date_str, get_tomorrow_date_str
from states import (
    STATE_MENU_TEACHER, STATE_TEACHER_SCHEDULE, STATE_TEACHER_ATTENDANCE_CLASS,
    STATE_TEACHER_ATTENDANCE_STUDENT, STATE_TEACHER_GRADES_CLASS,
    STATE_TEACHER_GRADES_STUDENT, STATE_TEACHER_GRADES_SET
)


# ИЗМЕНЕНО: Добавлен роутер главного меню
async def route_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Маршрутизатор для главного меню учителя."""
    lang = context.user_data.get('lang', 'uz')
    text = update.message.text

    if text == get_text(lang, 'btn_schedule'):
        return await handle_schedule(update, context)
    elif text == get_text(lang, 'btn_attendance'):
        return await handle_attendance(update, context)
    elif text == get_text(lang, 'btn_grades'):
        return await handle_grades(update, context)
    elif text == get_text(lang, 'btn_settings'):
        # Используем ту же функцию, что и у ученика
        return await student.handle_settings(update, context)
    else:
        await update.message.reply_text(get_text(lang, 'unknown_command'))
        return STATE_MENU_TEACHER

# ИЗМЕНЕНО: Добавлен роутер меню расписания
async def route_schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Маршрутизатор для меню 'Расписание' учителя."""
    lang = context.user_data.get('lang', 'uz')
    text = update.message.text

    if text == get_text(lang, 'btn_schedule_today'):
        return await send_schedule_today(update, context)
    elif text == get_text(lang, 'btn_schedule_tomorrow'):
        return await send_schedule_tomorrow(update, context)
    elif text == get_text(lang, 'btn_schedule_full'):
        return await send_schedule_full(update, context)
    elif text == get_text(lang, 'btn_back'):
        return await back_to_main_menu(update, context)
    else:
        await update.message.reply_text(get_text(lang, 'unknown_command'))
        return STATE_TEACHER_SCHEDULE

# --- Обработка главного меню ---

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает кнопки выбора расписания (для учителя)."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    await update.message.reply_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'choose_schedule_type'),
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_teacher_schedule_menu(lang)
    )
    return STATE_TEACHER_SCHEDULE

async def handle_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс отметки посещаемости."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    teacher_details = context.user_data.get("user_details", {})
    teacher_classes = teacher_details.get("classes")
    
    if not teacher_classes:
        # ИЗМЕНЕНО: get_text
        await update.message.reply_text(get_text(lang, 'teacher_no_classes'))
        return STATE_MENU_TEACHER
        
    await update.message.reply_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'teacher_choose_class_attendance'),
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_teacher_class_list(teacher_classes, "att_class_", lang)
    )
    return STATE_TEACHER_ATTENDANCE_CLASS


async def handle_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает процесс выставления оценок."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    teacher_details = context.user_data.get("user_details", {})
    teacher_classes = teacher_details.get("classes")
    
    if not teacher_classes:
        # ИЗМЕНЕНО: get_text
        await update.message.reply_text(get_text(lang, 'teacher_no_classes'))
        return STATE_MENU_TEACHER

    await update.message.reply_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'teacher_choose_class_grades'),
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_teacher_class_list(teacher_classes, "grade_class_", lang)
    )
    return STATE_TEACHER_GRADES_CLASS


# --- Обработка Расписания ---

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возврат в главное меню (для Reply кнопок)."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    await update.message.reply_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'main_menu'),
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_teacher_main_menu(lang)
    )
    return STATE_MENU_TEACHER

async def send_schedule_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет персональное расписание учителя на сегодня."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    username = context.user_data.get("username")
    day_key = get_day_of_week_str('today')
    today_date = get_today_date_str()
    
    schedule = db_handler.get_teacher_schedule(username)
    # ИЗМЕНЕНО: get_text
    lessons_list = schedule.get(day_key, [get_text(lang, 'no_lessons_today')])
    lessons_str = "\n".join(lessons_list)
    
    # ИЗМЕНЕНО: get_text
    text = get_text(lang, 'teacher_schedule_today').format(
        day_key=day_key.capitalize(), 
        date=today_date, 
        lessons=lessons_str
    )
    
    await update.message.reply_text(text)
    return STATE_TEACHER_SCHEDULE

async def send_schedule_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет персональное расписание учителя на завтра."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    username = context.user_data.get("username")
    day_key = get_day_of_week_str('tomorrow')
    tomorrow_date = get_tomorrow_date_str()
    
    schedule = db_handler.get_teacher_schedule(username)
    # ИЗМЕНЕНО: get_text
    lessons_list = schedule.get(day_key, [get_text(lang, 'no_lessons_teacher_tomorrow')])
    lessons_str = "\n".join(lessons_list)
    
    # ИЗМЕНЕНО: get_text
    text = get_text(lang, 'teacher_schedule_tomorrow').format(
        day_key=day_key.capitalize(), 
        date=tomorrow_date, 
        lessons=lessons_str
    )
    
    await update.message.reply_text(text)
    return STATE_TEACHER_SCHEDULE

async def send_schedule_full(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправляет полное персональное расписание учителя."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    username = context.user_data.get("username")
    schedule = db_handler.get_teacher_schedule(username)
    
    if not schedule:
        # ИЗМЕНЕНО: get_text
        await update.message.reply_text(get_text(lang, 'teacher_schedule_full_empty'))
        return STATE_TEACHER_SCHEDULE

    # ИЗМЕНЕНО: get_text
    text = get_text(lang, 'teacher_schedule_full')
    days_order = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    found_lessons = False
    for day in days_order:
        lessons = schedule.get(day)
        if lessons:
            found_lessons = True
            text += f"\n*{day.capitalize()}*:\n" + "\n".join(lessons) + "\n"
        
    if not found_lessons:
        # ИЗМЕНЕНО: get_text
        text = get_text(lang, 'teacher_schedule_full_empty')
        
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return STATE_TEACHER_SCHEDULE


# --- Обработка Посещаемости ---

async def select_student_for_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список учеников для отметки."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    class_id = query.data.split("_", 2)[2] # att_class_9A
    context.user_data["current_class_id"] = class_id
    
    students = db_handler.get_students_by_class(class_id)
    if not students:
        # ИЗМЕНЕНО: get_text
        await query.edit_message_text(get_text(lang, 'teacher_no_students_in_class').format(class_id=class_id))
        return STATE_TEACHER_ATTENDANCE_CLASS

    context.user_data["attendance_checklist"] = {student: "❔" for student in students}
    
    # ИЗМЕНЕНО: get_text
    date_str = get_today_date_str()
    text = get_text(lang, 'teacher_attendance_header').format(class_id=class_id, date=date_str)
    text += "\n".join([f"{student}: ❔" for student in students])
    text += get_text(lang, 'teacher_attendance_prompt')

    await query.edit_message_text(
        text,
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_student_list_keyboard(students, "att_student_", lang)
    )
    return STATE_TEACHER_ATTENDANCE_STUDENT

async def show_attendance_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает кнопки 'Тут/Нет' при нажатии на ученика."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    student_username = query.data.split("_", 2)[2] # att_student_student_test_1
    
    await query.edit_message_reply_markup(
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_attendance_keyboard(student_username, lang)
    )
    return STATE_TEACHER_ATTENDANCE_STUDENT


async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмечает ученика (Тут/Нет) и обновляет сообщение."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_") # att_mark_present_student_test_1
    status_str = parts[2] # present или absent
    student_username = "_".join(parts[3:]) 
    
    class_id = context.user_data["current_class_id"]
    date_str = get_today_date_str()
    status_icon = "✅" if status_str == "present" else "❌"

    db_handler.mark_attendance(student_username, date_str, status_str)
    
    if "attendance_checklist" not in context.user_data:
         students = db_handler.get_students_by_class(class_id)
         context.user_data["attendance_checklist"] = {student: "❔" for student in students}

    checklist = context.user_data["attendance_checklist"]
    checklist[student_username] = status_icon
    
    # ИЗМЕНЕНО: get_text
    text = get_text(lang, 'teacher_attendance_header').format(class_id=class_id, date=date_str)
    text += "\n".join([f"{student}: {mark}" for student, mark in checklist.items()])
    text += get_text(lang, 'teacher_attendance_prompt')
    
    students = list(checklist.keys())
    await query.edit_message_text(
        text,
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_student_list_keyboard(students, "att_student_", lang)
    )
    return STATE_TEACHER_ATTENDANCE_STUDENT

# --- Обработка Оценок ---

async def select_student_for_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список учеников для выставления оценки."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    class_id = query.data.split("_", 2)[2] # grade_class_9A
    context.user_data["current_class_id"] = class_id
    students = db_handler.get_students_by_class(class_id)
    
    if not students:
        # ИЗМЕНЕНО: get_text
        await query.edit_message_text(get_text(lang, 'teacher_no_students_in_class').format(class_id=class_id))
        return STATE_TEACHER_GRADES_CLASS
        
    await query.edit_message_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'teacher_choose_student_grade'),
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_student_list_keyboard(students, "grade_student_", lang)
    )
    return STATE_TEACHER_GRADES_STUDENT


async def select_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает кнопки 2-5 для ученика."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    student_username = query.data.split("_", 2)[2] # grade_student_student_test_1
    
    teacher_subject = context.user_data.get("user_details", {}).get("subject")
    
    if not teacher_subject:
         # ИЗМЕНЕНО: get_text
         await query.edit_message_text(get_text(lang, 'teacher_subject_not_found'))
         return STATE_TEACHER_GRADES_CLASS

    context.user_data["current_subject"] = teacher_subject
    
    await query.edit_message_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'teacher_confirm_grade').format(student_username=student_username, subject=teacher_subject),
        # Клавиатура 2-5 не требует lang
        reply_markup=keyboards.get_grades_set_keyboard(student_username, teacher_subject)
    )
    return STATE_TEACHER_GRADES_SET

async def set_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет оценку в БД."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_") # grade_set_5_math_student_test_1
    grade = parts[2]
    subject = parts[3]
    student_username = "_".join(parts[4:])
    date_str = get_today_date_str()
    
    db_handler.set_grade(student_username, subject, grade, date_str)
    
    # ИЗМЕНЕНО: get_text
    await query.edit_message_text(
        get_text(lang, 'teacher_grade_set_success').format(student_username=student_username, grade=grade, subject=subject)
    )
    
    teacher_classes = context.user_data.get("user_details", {}).get("classes", [])
    await query.message.reply_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'teacher_choose_next_class'),
        # ИЗМЕНЕНО: передаем lang
        reply_markup=keyboards.get_teacher_class_list(teacher_classes, "grade_class_", lang)
    )
    return STATE_TEACHER_GRADES_CLASS

