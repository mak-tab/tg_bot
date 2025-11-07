import logging
import os
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ( 
    Application, 
    ApplicationBuilder, 
    CommandHandler, 
    ContextTypes,
    ConversationHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters,
)
import database as db
import keyboards as kb
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
( 
SELECT_LANG, 
SELECT_ROLE, 
LOGIN, MAIN_MENU, 
STUDENT_MAIN, 
TEACHER_MAIN, 
ADMIN_MAIN,

STUDENT_SCHEDULE, 
STUDENT_GRADES, 
STUDENT_SETTINGS, 
STUDENT_SETTINGS_CHANGE_LOGIN, 
STUDENT_SETTINGS_CHANGE_PASS,

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
TEACHER_SETTINGS_CHANGE_PASS,

ADMIN_REGISTER_STEP_1_NAME, 
ADMIN_REGISTER_STEP_2_LASTNAME, 
ADMIN_REGISTER_STEP_3_CLASS,
ADMIN_REGISTER_STEP_4_LETTER, 
ADMIN_REGISTER_STEP_5_LOGIN, 
ADMIN_REGISTER_STEP_6_PASS,
ADMIN_EDIT_SCHEDULE
) = map(str, range(30))

import student
import teacher
import admin

MESSAGES = {
    'ru': {
        'welcome': "Здравствуйте! 👋\n\nПожалуйста, выберите ваш язык:",
        'select_role': "Отлично! Теперь выберите вашу роль:",
        'prompt_login': "Пожалуйста, введите ваш <b>логин</b> и <b>пароль</b>.\n\n"
                        "Вы можете отправить их:\n"
                        "• Двумя сообщениями (сначала логин, потом пароль)\n"
                        "• Одним сообщением (<code>логин пароль</code>)",
        'login_failed': "❌ Неверный логин или пароль.\n\nПопробуйте еще раз. Введите логин и пароль.",
        'login_success': "✅ Вход выполнен успешно!",
        'hello_user': "Здравствуйте, {first_name}!",
        'login_part1_received': "Хорошо, теперь введите вторую часть (логин или пароль).",
        'student_main_menu': "<b>Главное меню ученика</b>\n\nВыберите действие:",
        'teacher_main_menu': "<b>Главное меню учителя</b>\n\nВыберите действие:",
        'admin_main_menu': "<b>Панель администрации</b>\n\nВыберите действие:",
    },
    'en': {
        'welcome': "Hello! 👋\n\nPlease select your language:",
        'select_role': "Great! Now select your role:",
        'prompt_login': "Please enter your <b>username</b> and <b>password</b>.\n\n"
                        "You can send them as:\n"
                        "• Two messages (username first, then password)\n"
                        "• One message (<code>username password</code>)",
        'login_failed': "❌ Invalid username or password.\n\nPlease try again. Enter your username and password.",
        'login_success': "✅ Login successful!",
        'hello_user': "Hello, {first_name}!",
        'login_part1_received': "OK, now enter the second part (username or password).",
        'student_main_menu': "<b>Student's Main Menu</b>\n\nSelect an action:",
        'teacher_main_menu': "<b>Teacher's Main Menu</b>\n\nSelect an action:",
        'admin_main_menu': "<b>Admin Panel</b>\n\nSelect an action:",
    },
    'uz': {
        'welcome': "Assalomu alaykum! 👋\n\nIltimos, tilingizni tanlang:",
        'select_role': "Ajoyib! Endi rolingizni tanlang:",
        'prompt_login': "Iltimos, <b>login</b> va <b>parolingizni</b> kiriting.\n\n"
                        "Siz ularni yuborishingiz mumkin:\n"
                        "• Ikkita xabarda (avval login, keyin parol)\n"
                        "• Bitta xabarda (<code>login parol</code>)",
        'login_failed': "❌ Noto'g'ri login yoki parol.\n\nQayta urinib ko'ring. Login va parolni kiriting.",
        'login_success': "✅ Tizimga kirish muvaffaqiyatli!",
        'hello_user': "Assalomu alaykum, {first_name}!",
        'login_part1_received': "Yaxshi, endi ikkinchi qismni (login yoki parolni) kiriting.",
        'student_main_menu': "<b>O'quvchi asosiy menyusi</b>\n\nAmalni tanlang:",
        'teacher_main_menu': "<b>O'qituvchi asosiy menyusi</b>\n\nAmalni tanlang:",
        'admin_main_menu': "<b>Ma'muriyat paneli</b>\n\nAmalni tanlang:",
    }
}

def get_msg(key, lang='ru'): 
    return MESSAGES.get(lang, MESSAGES['ru']).get(key, f"_{key}_")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    telegram_id = str(user.id)
    context.user_data.clear()
    user_data, role = db.get_user_by_telegram_id(telegram_id)
    if user_data and role:
        lang = user_data.get('lang', 'ru')
        context.user_data['user_info'] = user_data
        context.user_data['role'] = role
        context.user_data['lang'] = lang
        context.user_data['db_id'] = telegram_id
        
        await update.message.reply_text(
            get_msg('hello_user', lang).format(first_name=user_data.get('first_name', '')),
            parse_mode='HTML'
        )
        return await route_to_main_menu(update, context, user_data, role, lang)

    await update.message.reply_text(
        get_msg('welcome', 'ru'),
        reply_markup=kb.get_language_keyboard()
    )
    return SELECT_LANG

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    await query.answer()

    lang = query.data.split('_')[-1]
    context.user_data['lang'] = lang

    lang_text = "O'zbekcha"
    if lang == 'ru': 
        lang_text = "Русский"
    elif lang == 'en': 
        lang_text = "English"

    await query.edit_message_text(
        text=f"Выбран язык: {lang_text} ✅",
        reply_markup=None
    )

    await query.message.reply_text(
        text=get_msg('select_role', lang),
        reply_markup=kb.get_role_keyboard(lang)
    )
    return SELECT_ROLE

async def select_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang = context.user_data.get('lang', 'ru')
    role_text = update.message.text
    role = None
    if role_text == kb.get_text('role_student', lang): 
        role = 'student'
    elif role_text == kb.get_text('role_teacher', lang): 
        role = 'teacher'
    elif role_text == kb.get_text('role_admin', lang): 
        role = 'admin'
    
    if not role: 
        await update.message.reply_text(
            get_msg('select_role', lang),
            reply_markup=kb.get_role_keyboard(lang)
        )
        return SELECT_ROLE

    context.user_data['role'] = role
    
    await update.message.reply_text(
        get_msg('prompt_login', lang),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='HTML'
    )
    
    return LOGIN

async def try_login(username, password, role, telegram_id, lang):
    username = username.lower()
    
    db_id, user_data = db.find_user_by_username(username, role)
    
    if user_data and user_data.get('password') == password:
        user_data['lang'] = lang
        
        if db_id.startswith("new_"):
            logger.info(f"Первый вход для {username}. Привязка telegram_id {telegram_id}...")
            if role == 'student':
                all_users = db.get_all_students()
                all_users.pop(db_id)
                all_users[telegram_id] = user_data
                db.save_all_students(all_users)
            elif role == 'teacher':
                all_teachers = db.get_all_teachers()
                all_teachers.pop(db_id)
                all_teachers[telegram_id] = user_data
                db.save_all_teachers(all_teachers)
            elif role == 'admin':
                all_admins = db.get_all_admins()
                all_admins.pop(db_id)
                all_admins[telegram_id] = user_data
                db.save_all_admins(all_admins)
            
            return user_data, telegram_id
        
        else:
            if role == 'student':
                all_users = db.get_all_students()
                all_users[db_id]['lang'] = lang
                db.save_all_students(all_users)
            elif role == 'teacher':
                all_teachers = db.get_all_teachers()
                all_teachers[db_id]['lang'] = lang
                db.save_all_teachers(all_teachers)
            elif role == 'admin':
                all_admins = db.get_all_admins()
                all_admins[db_id]['lang'] = lang
                db.save_all_admins(all_admins)
                
            return user_data, db_id
            
    return None, None

async def handle_login_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    telegram_id = str(user.id)
    lang = context.user_data.get('lang', 'ru')
    role = context.user_data.get('role')
    
    text = update.message.text
    parts = text.split()
    
    pending_part = context.user_data.pop('login_part1', None)
    
    user_data = None
    db_telegram_id = None
    
    await update.message.delete()
    
    if pending_part:
        part2 = text
        user_data, db_telegram_id = await try_login(pending_part, part2, role, telegram_id, lang)
        if not user_data:
            user_data, db_telegram_id = await try_login(part2, pending_part, role, telegram_id, lang)
            
    elif len(parts) == 2:
        user_data, db_telegram_id = await try_login(parts[0], parts[1], role, telegram_id, lang)
        if not user_data:
            user_data, db_telegram_id = await try_login(parts[1], parts[0], role, telegram_id, lang)

    elif len(parts) == 1:
        context.user_data['login_part1'] = parts[0]
        await update.message.reply_text(get_msg('login_part1_received', lang))
        return LOGIN
    else:
        pass

    if user_data and db_telegram_id:
        context.user_data.clear()
        context.user_data['user_info'] = user_data
        context.user_data['role'] = role
        context.user_data['lang'] = lang
        context.user_data['db_id'] = db_telegram_id
        
        await update.message.reply_text(get_msg('login_success', lang))
        
        await update.message.reply_text(
            get_msg('hello_user', lang).format(first_name=user_data.get('first_name', ''))
        )
        return await route_to_main_menu(update, context, user_data, role, lang)
        
    else:
        context.user_data.pop('login_part1', None)
        await update.message.reply_text(get_msg('login_failed', lang))
        await update.message.reply_text(
            get_msg('prompt_login', lang),
            parse_mode='HTML'
        )
        return LOGIN

async def route_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data, role, lang) -> str:
    if role == 'student':
        await update.message.reply_text(
            get_msg('student_main_menu', lang),
            reply_markup=kb.get_student_main_keyboard(lang),
            parse_mode='HTML'
        )
        return STUDENT_MAIN
        
    elif role == 'teacher':
        await update.message.reply_text(
            get_msg('teacher_main_menu', lang),
            reply_markup=kb.get_teacher_main_keyboard(lang),
            parse_mode='HTML'
        )
        return TEACHER_MAIN
        
    elif role == 'admin':
        await update.message.reply_text(
            get_msg('admin_main_menu', lang),
            reply_markup=kb.get_admin_main_keyboard(lang),
            parse_mode='HTML'
        )
        return ADMIN_MAIN
        
    else:
        return await start(update, context)

def main() -> None:
    db.init_database()
    
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    application = ApplicationBuilder().token(TOKEN).build()

    student_schedule_filter = filters.Text([
        kb.get_text('main_schedule', 'ru'),
        kb.get_text('main_schedule', 'en'),
        kb.get_text('main_schedule', 'uz')
    ])
    student_grades_filter = filters.Text([
        kb.get_text('main_grades', 'ru'),
        kb.get_text('main_grades', 'en'),
        kb.get_text('main_grades', 'uz')
    ])
    student_settings_filter = filters.Text([
        kb.get_text('main_settings', 'ru'),
        kb.get_text('main_settings', 'en'),
        kb.get_text('main_settings', 'uz')
    ])
    student_schedule_tomorrow_filter = filters.Text([
        kb.get_text('schedule_tomorrow', 'ru'),
        kb.get_text('schedule_tomorrow', 'en'),
        kb.get_text('schedule_tomorrow', 'uz')
    ])
    student_schedule_full_filter = filters.Text([
        kb.get_text('schedule_full', 'ru'),
        kb.get_text('schedule_full', 'en'),
        kb.get_text('schedule_full', 'uz')
    ])
    
    back_filter = filters.Text([
        kb.get_text('back', 'ru'),
        kb.get_text('back', 'en'),
        kb.get_text('back', 'uz')
    ])
    
    teacher_schedule_filter = filters.Text([
        kb.get_text('main_schedule', 'ru'),
        kb.get_text('main_schedule', 'en'),
        kb.get_text('main_schedule', 'uz')
    ])
    teacher_attendance_filter = filters.Text([
        kb.get_text('main_attendance', 'ru'),
        kb.get_text('main_attendance', 'en'),
        kb.get_text('main_attendance', 'uz')
    ])
    teacher_grades_filter = filters.Text([
        kb.get_text('main_grades', 'ru'),
        kb.get_text('main_grades', 'en'),
        kb.get_text('main_grades', 'uz')
    ])
    teacher_settings_filter = filters.Text([
        kb.get_text('main_settings', 'ru'),
        kb.get_text('main_settings', 'en'),
        kb.get_text('main_settings', 'uz')
    ])
    
    teacher_schedule_today_filter = filters.Text(kb.get_text('schedule_today', 'ru')) | \
                                    filters.Text(kb.get_text('schedule_today', 'en')) | \
                                    filters.Text(kb.get_text('schedule_today', 'uz'))
    teacher_schedule_tomorrow_filter = filters.Text(kb.get_text('schedule_tomorrow', 'ru')) | \
                                       filters.Text(kb.get_text('schedule_tomorrow', 'en')) | \
                                       filters.Text(kb.get_text('schedule_tomorrow', 'uz'))
    teacher_schedule_full_filter = filters.Text(kb.get_text('schedule_full', 'ru')) | \
                                   filters.Text(kb.get_text('schedule_full', 'en')) | \
                                   filters.Text(kb.get_text('schedule_full', 'uz'))
    
    admin_register_filter = filters.Text([
        kb.get_text('admin_reg_student', 'ru'),
        kb.get_text('admin_reg_student', 'en'),
        kb.get_text('admin_reg_student', 'uz')
    ])
    admin_schedule_filter = filters.Text([
        kb.get_text('admin_edit_schedule', 'ru'),
        kb.get_text('admin_edit_schedule', 'en'),
        kb.get_text('admin_edit_schedule', 'uz')
    ])
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_LANG: [
                CallbackQueryHandler(select_language, pattern='^set_lang_')
            ],
            SELECT_ROLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_role)
            ],
            LOGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_input)
            ],

            STUDENT_MAIN: [
                MessageHandler(student_schedule_filter, student.handle_schedule),
                MessageHandler(student_grades_filter, student.handle_grades),
                MessageHandler(student_settings_filter, student.handle_settings),
                CallbackQueryHandler(student.back_to_main_callback, pattern='^back_to_main_menu$'),
            ],
            TEACHER_MAIN: [
                MessageHandler(teacher_schedule_filter, teacher.handle_schedule),
                MessageHandler(teacher_attendance_filter, teacher.handle_attendance),
                MessageHandler(teacher_grades_filter, teacher.handle_grades),
                MessageHandler(teacher_settings_filter, teacher.handle_settings),
                CallbackQueryHandler(teacher.back_to_main_callback, pattern='^back_to_main_menu$'),
            ],
            ADMIN_MAIN: [
                MessageHandler(admin_register_filter, admin.handle_register_student),
                MessageHandler(admin_schedule_filter, admin.handle_edit_schedule),
            ],

            STUDENT_SCHEDULE: [
                MessageHandler(student_schedule_tomorrow_filter, student.show_schedule_tomorrow),
                MessageHandler(student_schedule_full_filter, student.show_schedule_full),
                MessageHandler(back_filter, student.back_to_main),
            ],
            STUDENT_GRADES: [
                CallbackQueryHandler(student.show_grades_for_subject, pattern='^grade_subj_'),
                CallbackQueryHandler(student.back_to_main_callback, pattern='^back_to_main_menu$'),
            ],
            STUDENT_SETTINGS: [
                CallbackQueryHandler(student.toggle_next_lesson, pattern='^settings_toggle_next_lesson$'),
                CallbackQueryHandler(student.toggle_daily_schedule, pattern='^settings_toggle_daily_schedule$'),
                CallbackQueryHandler(student.start_change_login, pattern='^settings_change_login$'),
                CallbackQueryHandler(student.back_to_main_callback, pattern='^back_to_main_menu$'),
            ],
            STUDENT_SETTINGS_CHANGE_LOGIN: [
                CommandHandler('cancel', student.cancel_change_login),
                MessageHandler(filters.TEXT & ~filters.COMMAND, student.receive_new_login),
            ],
            STUDENT_SETTINGS_CHANGE_PASS: [
                CommandHandler('cancel', student.cancel_change_login),
                MessageHandler(filters.TEXT & ~filters.COMMAND, student.receive_new_password),
            ],

            TEACHER_SCHEDULE: [
                MessageHandler(teacher_schedule_today_filter | teacher_schedule_tomorrow_filter | teacher_schedule_full_filter, 
                               teacher.show_schedule_placeholder),
                MessageHandler(back_filter, teacher.back_to_main),
            ],
            TEACHER_ATTENDANCE_MARK_STUDENT: [
                CallbackQueryHandler(teacher.select_attendance_letter, pattern='^att_letter_'),
                CallbackQueryHandler(teacher.select_attendance_student, pattern='^att_student_'),
                CallbackQueryHandler(teacher.mark_attendance, pattern='^att_(present|absent)$'),
                CallbackQueryHandler(teacher.select_attendance_class, pattern='^att_letter_back_to_class'), 
            ],
            TEACHER_GRADES_SELECT_LETTER: [
                CallbackQueryHandler(teacher.select_grades_class, pattern='^grade_class_'),
                CallbackQueryHandler(teacher.back_to_main_callback, pattern='^back_to_main_menu$'),
            ],
            TEACHER_GRADES_SELECT_STUDENT: [
                CallbackQueryHandler(teacher.select_grades_letter, pattern='^grade_letter_'),
                CallbackQueryHandler(teacher.select_grades_class, pattern='^grade_letter_back_to_class'), 
            ],
            TEACHER_GRADES_MARK_STUDENT: [
                CallbackQueryHandler(teacher.select_grades_student, pattern='^grade_student_'),
                CallbackQueryHandler(teacher.set_grade, pattern='^grade_(2|3|4|5)$'),
                CallbackQueryHandler(teacher.select_grades_letter, pattern='^grade_student_back_to_letter_'), 
            ],
            TEACHER_SETTINGS: [
                CallbackQueryHandler(teacher.toggle_next_lesson, pattern='^settings_toggle_next_lesson$'),
                CallbackQueryHandler(teacher.toggle_daily_schedule, pattern='^settings_toggle_daily_schedule$'),
                CallbackQueryHandler(teacher.start_change_login, pattern='^settings_change_login$'),
                CallbackQueryHandler(teacher.back_to_main_callback, pattern='^back_to_main_menu$'),
            ],
            TEACHER_SETTINGS_CHANGE_LOGIN: [
                CommandHandler('cancel', teacher.cancel_change_login),
                MessageHandler(filters.TEXT & ~filters.COMMAND, teacher.receive_new_login),
            ],
            TEACHER_SETTINGS_CHANGE_PASS: [
                CommandHandler('cancel', teacher.cancel_change_login),
                MessageHandler(filters.TEXT & ~filters.COMMAND, teacher.receive_new_password),
            ],

            ADMIN_REGISTER_STEP_1_NAME: [
                CommandHandler('cancel', admin.cancel_register),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.register_step_1_name)
            ],
            ADMIN_REGISTER_STEP_2_LASTNAME: [
                CommandHandler('cancel', admin.cancel_register),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.register_step_2_lastname)
            ],
            ADMIN_REGISTER_STEP_3_CLASS: [
                CommandHandler('cancel', admin.cancel_register),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.register_step_3_class)
            ],
            ADMIN_REGISTER_STEP_4_LETTER: [
                CommandHandler('cancel', admin.cancel_register),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.register_step_4_letter)
            ],
            ADMIN_REGISTER_STEP_5_LOGIN: [
                CommandHandler('cancel', admin.cancel_register),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.register_step_5_login)
            ],
            ADMIN_REGISTER_STEP_6_PASS: [
                CommandHandler('cancel', admin.cancel_register),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.register_step_6_pass)
            ],

            ADMIN_EDIT_SCHEDULE: [
                CommandHandler('cancel', admin.cancel_edit_schedule),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin.receive_schedule_text),
            ],
        },
        fallbacks=[
            CommandHandler('start', start)
        ],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
