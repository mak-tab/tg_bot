import logging
import datetime
import pytz
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
from bot import ( 
    STUDENT_MAIN, 
    TEACHER_MAIN, 
    ADMIN_MAIN,
    TEACHER_SCHEDULE, 
    TEACHER_ATTENDANCE_SELECT_CLASS, 
    TEACHER_ATTENDANCE_SELECT_LETTER, 
    TEACHER_ATTENDANCE_SELECT_STUDENT, 
    TEACHER_ATTENDANCE_MARK_STUDENT,
    TEACHER_GRADES_SELECT_CLASS, 
    TEACHER_GRADES_SELECT_LETTER,
    TEACHER_GRADES_SELECT_STUDENT, 
    TEACHER_GRADES_MARK_STUDENT,
    TEACHER_SETTINGS, 
    TEACHER_SETTINGS_CHANGE_LOGIN,
    TEACHER_SETTINGS_CHANGE_PASS
)
logger = logging.getLogger(__name__)

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
        'settings_error_login_spaces': "❌ Логин не должен содержать пробелов. Попробуйте еще раз.",
        'error_student_not_found': "❌ Ошибка: Ученик не найден.",
        'error_generic': "❌ Произошла ошибка. Попробуйте снова.",
        'error_teacher_subject_not_found': "❌ Ошибка: ID ученика или предмет учителя не найден. Попробуйте снова.",
        'teacher_schedule_title': "<b>Ваше полное расписание (Предмет: {subject})</b>",
        'teacher_schedule_today_title': "<b>Ваше расписание на сегодня ({day_name})</b>",
        'teacher_schedule_tomorrow_title': "<b>Ваше расписание на завтра ({day_name})</b>",
        'teacher_schedule_not_found': "Не удалось найти уроки по вашему предмету ({subject}) в расписании.",
        'teacher_subject_not_set': "❌ Ваш предмет не указан в профиле. Обратитесь к администратору.",
        'no_lessons_today': "Сегодня у вас нет уроков.",
        'no_lessons_tomorrow': "Завтра у вас нет уроков.",
        'day_monday': "Понедельник",
        'day_tuesday': "Вторник",
        'day_wednesday': "Среда",
        'day_thursday': "Четверг",
        'day_friday': "Пятница",
        'day_saturday': "Суббота",
        'day_sunday': "Воскресенье",
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
        'settings_error_login_spaces': "❌ Username must not contain spaces. Try again.",
        'error_student_not_found': "❌ Error: Student not found.",
        'error_generic': "❌ An error occurred. Please try again.",
        'error_teacher_subject_not_found': "❌ Error: Student ID or teacher subject not found. Please try again.",
        'teacher_schedule_title': "<b>Your full schedule (Subject: {subject})</b>",
        'teacher_schedule_today_title': "<b>Your schedule for today ({day_name})</b>",
        'teacher_schedule_tomorrow_title': "<b>Your schedule for tomorrow ({day_name})</b>",
        'teacher_schedule_not_found': "Could not find any lessons for your subject ({subject}) in the schedule.",
        'teacher_subject_not_set': "❌ Your subject is not specified in your profile. Please contact the administrator.",
        'no_lessons_today': "You have no lessons today.",
        'no_lessons_tomorrow': "You have no lessons tomorrow.",
        'day_monday': "Monday",
        'day_tuesday': "Tuesday",
        'day_wednesday': "Wednesday",
        'day_thursday': "Thursday",
        'day_friday': "Friday",
        'day_saturday': "Saturday",
        'day_sunday': "Sunday",
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
        'settings_error_login_spaces': "❌ Login bo'sh joylarni o'z ichiga olmasligi kerak. Qayta urinib ko'ring.",
        'error_student_not_found': "❌ Xato: O'quvchi topilmadi.",
        'error_generic': "❌ Xatolik yuz berdi. Qayta urinib ko'ring.",
        'error_teacher_subject_not_found': "❌ Xato: O'quvchi IDsi yoki o'qituvchi fani topilmadi. Qayta urinib ko'ring.",
        'teacher_schedule_title': "<b>Sizning to‘liq dars jadvalingiz (Fan: {subject})</b>",
        'teacher_schedule_today_title': "<b>Bugungi dars jadvalingiz ({day_name})</b>",
        'teacher_schedule_tomorrow_title': "<b>Ertangi dars jadvalingiz ({day_name})</b>",
        'teacher_schedule_not_found': "Sizning faningiz ({subject}) bo‘yicha darslar topilmadi.",
        'teacher_subject_not_set': "❌ Profilingizda faningiz ko‘rsatilmagan. Administrator bilan bog‘laning.",
        'no_lessons_today': "Bugun sizda dars yo‘q.",
        'no_lessons_tomorrow': "Ertaga sizda dars yo‘q.",
        'day_monday': "Dushanba",
        'day_tuesday': "Seshanba",
        'day_wednesday': "Chorshanba",
        'day_thursday': "Payshanba",
        'day_friday': "Juma",
        'day_saturday': "Shanba",
        'day_sunday': "Yakshanba",
    }
}

def get_tchr_msg(key, lang='ru'):
    return MESSAGES.get(lang, MESSAGES['ru']).get(key, f"_{key}_")

def get_user_data(context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    user_info = context.user_data.get('user_info', {})
    db_id = context.user_data.get('db_id')
    return lang, user_info, db_id

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_tchr_msg('back_to_main', lang),
        reply_markup=kb.get_teacher_main_keyboard(lang)
    )
    return TEACHER_MAIN

async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
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
    students = db.get_all_students()
    classes = {}
    for student_data in students.values():
        class_num = student_data.get('class')
        letter = student_data.get('letter')
        if class_num and letter:
            if class_num not in classes:
                classes[class_num] = set()
            classes[class_num].add(letter)
    
    sorted_classes = {k: sorted(list(v)) for k, v in classes.items()}
    sorted_keys = sorted(sorted_classes.keys(), key=lambda x: int(x))
    return {k: sorted_classes[k] for k in sorted_keys}

def _get_students_by_class(class_num, letter):
    students = db.get_all_students()
    matches = []
    for student_id, student_data in students.items():
        if student_data.get('class') == class_num and student_data.get('letter') == letter:
            matches.append({
                'id': student_id,
                'first_name': student_data.get('first_name', ''),
                'last_name': student_data.get('last_name', '')
            })
    return sorted(matches, key=lambda x: (x.get('last_name', ''), x.get('first_name', '')))

async def handle_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_tchr_msg('schedule_menu', lang),
        reply_markup=kb.get_teacher_schedule_keyboard(lang)
    )
    return TEACHER_SCHEDULE

async def handle_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    classes_dict = _get_all_classes_and_letters()
    
    if not classes_dict:
        await update.message.reply_text(get_tchr_msg('error_generic', lang)) # ИЗМЕНИТЬ
        return TEACHER_MAIN
        
    await update.message.reply_text(
        get_tchr_msg('attendance_select_class', lang),
        reply_markup=kb.generate_class_list_keyboard(
            classes_list=classes_dict.keys(),
            callback_prefix='att_class_',
            lang=lang
        )
    )
    return TEACHER_ATTENDANCE_SELECT_CLASS

async def handle_grades(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    classes_dict = _get_all_classes_and_letters()
    
    if not classes_dict:
        await update.message.reply_text(get_tchr_msg('error_generic', lang))
        return TEACHER_MAIN
        
    await update.message.reply_text(
        get_tchr_msg('grades_select_class', lang),
        reply_markup=kb.generate_class_list_keyboard(
            classes_list=classes_dict.keys(),
            callback_prefix='grade_class_',
            lang=lang
        )
    )
    return TEACHER_GRADES_SELECT_CLASS

def _get_teacher_schedule(teacher_subject: str) -> dict:
    all_schedule = db.get_schedule()
    teacher_schedule = {
        'monday': [], 'tuesday': [], 'wednesday': [], 
        'thursday': [], 'friday': [], 'saturday': [], 'sunday': []
    }
    
    if not teacher_subject:
        return teacher_schedule

    for class_key, class_schedule in all_schedule.items():
        for day_key, day_schedule in class_schedule.items():
            if day_key not in teacher_schedule: 
                continue
            
            for lesson_num, subject_name in day_schedule.items():
                if subject_name == teacher_subject:
                    try:
                        num = int(lesson_num)
                        info_str = f"{class_key} (Урок {lesson_num})"
                        teacher_schedule[day_key].append((num, info_str))
                    except ValueError:
                        continue

    for day_key in teacher_schedule:
        teacher_schedule[day_key].sort(key=lambda x: x[0])
        teacher_schedule[day_key] = [info for num, info in teacher_schedule[day_key]]

    return teacher_schedule

def _format_teacher_day(day_lessons: list, day_name: str) -> str:
    if not day_lessons:
        return ""
    
    lines = [f"<b>{day_name}</b>:"]
    for lesson_info in day_lessons:
        lines.append(f"  • {lesson_info}")
    return "\n".join(lines)

async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, _ = get_user_data(context)
    await update.message.reply_text(
        get_tchr_msg('settings_menu', lang),
        reply_markup=kb.generate_settings_keyboard(user_info, lang)
    )
    return TEACHER_SETTINGS

async def show_teacher_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, user_info, _ = get_user_data(context)
    teacher_subject = user_info.get('subject')
    if not teacher_subject:
        await update.message.reply_text(get_tchr_msg('teacher_subject_not_set', lang))
        return TEACHER_SCHEDULE

    full_schedule = _get_teacher_schedule(teacher_subject)
    button_text = update.message.text

    day_keys = ['day_monday', 'day_tuesday', 'day_wednesday', 'day_thursday', 'day_friday', 'day_saturday', 'day_sunday']
    day_db_keys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    output_lines = []

    if button_text == kb.get_text('schedule_full', lang):
        output_lines.append(get_tchr_msg('teacher_schedule_title', lang).format(subject=teacher_subject))
        has_lessons = False

        for i, day_db in enumerate(day_db_keys):
            day_name = get_tchr_msg(day_keys[i], lang)
            day_lessons = full_schedule.get(day_db, [])

            if day_lessons:
                has_lessons = True
                output_lines.append(_format_teacher_day(day_lessons, day_name))

        if not has_lessons:
            await update.message.reply_text(get_tchr_msg('teacher_schedule_not_found', lang).format(subject=teacher_subject))
            return TEACHER_SCHEDULE
    else:
        try:
            tashkent_time = datetime.datetime.now(pytz.timezone("Asia/Tashkent"))
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning("Часовой пояс Asia/Tashkent не найден, используется UTC.")
            tashkent_time = datetime.datetime.now(pytz.timezone("UTC"))

        target_date = tashkent_time.date()
        title_key = 'teacher_schedule_today_title'
        no_lesson_key = 'no_lessons_today'

        if button_text == kb.get_text('schedule_tomorrow', lang):
            target_date = target_date + datetime.timedelta(days=1)
            title_key = 'teacher_schedule_tomorrow_title'
            no_lesson_key = 'no_lessons_tomorrow'

        day_idx = target_date.weekday()
        day_db = day_db_keys[day_idx]
        day_name = get_tchr_msg(day_keys[day_idx], lang)

        output_lines.append(get_tchr_msg(title_key, lang).format(day_name=day_name))
        day_lessons = full_schedule.get(day_db, [])

        if not day_lessons:
            output_lines.append(get_tchr_msg(no_lesson_key, lang))
        else:
            output_lines.append(_format_teacher_day(day_lessons, day_name))

    await update.message.reply_text("\n\n".join(filter(None, output_lines)), parse_mode='HTML')
    return TEACHER_SCHEDULE

async def select_attendance_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    class_num = ""
    if query.data.startswith('att_class_'):
        class_num = query.data.split('att_class_')[-1]
    elif query.data.startswith('att_student_back_to_letter_'):
        class_num = query.data.split('_')[-1]
    
    if not class_num:
        await query.edit_message_text(get_tchr_msg('error_generic', lang))
        return TEACHER_MAIN

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
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    try:
        class_num, letter = "", ""
        if query.data.startswith('att_letter_'):
            class_num, letter = query.data.split('att_letter_')[-1].split('_')
        elif query.data.startswith('att_mark_back_to_student_list_'):
             class_num, letter = query.data.split('att_mark_back_to_student_list_')[-1].split('_')
        else:
            raise ValueError("Invalid callback data")
            
    except ValueError:
        await query.edit_message_text(get_tchr_msg('error_generic', lang))
        return TEACHER_MAIN
    
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
    return TEACHER_ATTENDANCE_SELECT_STUDENT
    
async def select_attendance_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    student_id = query.data.split('att_student_')[-1]
    
    all_students = db.get_all_students()
    student_data = all_students.get(student_id)
    if not student_data:
        await query.edit_message_text(get_tchr_msg('error_student_not_found', lang)) 
        return TEACHER_MAIN
        
    name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
    
    class_num = student_data.get('class')
    letter = student_data.get('letter')
    
    context.user_data['selected_student_id'] = student_id
    context.user_data['selected_student_name'] = name
    
    await query.edit_message_text(
        get_tchr_msg('attendance_marking', lang).format(name=name),
        reply_markup=kb.get_attendance_markup(lang, class_num, letter),
        parse_mode='HTML'
    )
    return TEACHER_ATTENDANCE_MARK_STUDENT

async def mark_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    status = query.data
    student_id = context.user_data.pop('selected_student_id', None)
    student_name = context.user_data.pop('selected_student_name', 'N/A')
    
    if not student_id:
        await query.edit_message_text(get_tchr_msg('error_generic', lang)) # ИЗMENIT
        return TEACHER_MAIN
        
    status_text = 'present' if status == 'att_present' else 'absent'
    status_icon = '✅' if status == 'att_present' else '❌'
    
    today_str = datetime.datetime.now(pytz.timezone("Asia/Tashkent")).date().isoformat()
    
    app_data = db.get_app_data()
    if 'attendance' not in app_data:
        app_data['attendance'] = {}
    if today_str not in app_data['attendance']:
        app_data['attendance'][today_str] = {}
        
    app_data['attendance'][today_str][student_id] = status_text
    db.save_app_data(app_data)
    
    await query.edit_message_text(
        get_tchr_msg('attendance_marked', lang).format(name=student_name, status_icon=status_icon),
        parse_mode='HTML'
    )
    
    return await back_to_main_callback(update, context)


async def select_grades_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    class_num = ""
    if query.data.startswith('grade_class_'):
        class_num = query.data.split('grade_class_')[-1]
    elif query.data.startswith('grade_student_back_to_letter_'):
        class_num = query.data.split('_')[-1]

    if not class_num:
        await query.edit_message_text(get_tchr_msg('error_generic', lang))
        return TEACHER_MAIN

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
    query = update.callback_query
    await query.answer()
    lang, _, _ = get_user_data(context)
    
    class_num, letter = "", ""
    try:
        if query.data.startswith('grade_letter_'):
            class_num, letter = query.data.split('grade_letter_')[-1].split('_')
        elif query.data.startswith('grade_back_to_student_list_'):
            class_num, letter = query.data.split('grade_back_to_student_list_')[-1].split('_')
        else:
            raise ValueError("Invalid callback data")
            
    except Exception:
        await query.edit_message_text(get_tchr_msg('error_generic', lang))
        return TEACHER_MAIN
    
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
    query = update.callback_query
    await query.answer()
    lang, user_info, _ = get_user_data(context)
    
    student_id = query.data.split('grade_student_')[-1]
    
    all_students = db.get_all_students()
    student_data = all_students.get(student_id)
    if not student_data:
        await query.edit_message_text(get_tchr_msg('error_student_not_found', lang)) 
        return TEACHER_MAIN
        
    name = f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}"
    teacher_subject = user_info.get('subject', 'N/A')
    
    class_num = student_data.get('class')
    letter = student_data.get('letter')
    
    context.user_data['selected_student_id'] = student_id
    context.user_data['selected_student_name'] = name
    
    await query.edit_message_text(
        get_tchr_msg('grades_marking', lang).format(name=name, subject=teacher_subject),
        reply_markup=kb.get_grades_markup(lang, class_num, letter),
        parse_mode='HTML'
    )
    return TEACHER_GRADES_MARK_STUDENT

async def set_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Сохраняет оценку."""
    query = update.callback_query
    await query.answer()
    lang, user_info, _ = get_user_data(context)
    
    grade = query.data.split('grade_')[-1]
    student_id = context.user_data.pop('selected_student_id', None)
    student_name = context.user_data.pop('selected_student_name', 'N/A')
    teacher_subject = user_info.get('subject')
    
    if not student_id or not teacher_subject:
        await query.edit_message_text(get_tchr_msg('error_teacher_subject_not_found', lang))
        return TEACHER_MAIN
        
    today_str = datetime.datetime.now(pytz.timezone("Asia/Tashkent")).date().isoformat()
    
    app_data = db.get_app_data()
    if 'grades' not in app_data:
        app_data['grades'] = {}
    if student_id not in app_data['grades']:
        app_data['grades'][student_id] = {}
    if teacher_subject not in app_data['grades'][student_id]:
        app_data['grades'][student_id][teacher_subject] = {}
        
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
    
    return await back_to_main_callback(update, context)

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
        await update.message.reply_text(get_tchr_msg('settings_error_login_spaces', lang))
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
        await update.message.reply_text(get_tchr_msg('error_generic', lang))
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
