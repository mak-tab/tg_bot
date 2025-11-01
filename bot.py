import logging
import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    PicklePersistence,
)
from telegram.constants import ParseMode
from datetime import time
# ИЗМЕНЕНО: Убраны импорты, которые теперь не нужны
from datetime import datetime, timedelta
# import pytz

from localization import get_text 
from states import *
import utils
import config
import keyboards
import db_handler
import student
import teacher  # Оставляем импорт, но не будем использовать
import admin    # Оставляем импорт, но не будем использовать

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- JobQueue (Уведомления) ---
# ... (функции send_daily_schedule_job, check_upcoming_lessons_job, clear_sent_notifications_job остаются БЕЗ ИЗМЕНЕНИЙ) ...
async def send_daily_schedule_job(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running daily schedule job...")
    all_settings = db_handler.get_all_user_settings()
    user_data_persistence = await context.application.persistence.get_user_data()

    day_str = utils.get_day_of_week_str('today')
    
    for user_id_str, settings in all_settings.items():
        if not settings.get("notify_schedule"):
            continue

        try:
            user_id = int(user_id_str)
            user_data = user_data_persistence.get(user_id)
            
            if not user_data:
                logger.warning(f"No persistence data found for user {user_id} for daily schedule.")
                continue
            
            lang = user_data.get('lang', 'uz') 
            role = user_data.get("role")
            
            # ИЗМЕНЕНО: Логика для учителя/админа больше не нужна для этого job
            if role not in ["student", "parent"]:
                 continue # Пропускаем, так как мы тестируем только учеников

            text = get_text(lang, 'notify_daily_schedule_header').format(day_key=day_str.capitalize())
            lessons = []

            class_id = user_data.get("class_id")
            if not class_id:
                continue
            schedule = db_handler.get_schedule_for_class(class_id)
            lessons = schedule.get(day_str, [get_text(lang, 'no_lessons_today')])
            
            if lessons:
                text += "\n".join(lessons)
                await context.bot.send_message(chat_id=user_id, text=text)

        except Exception as e:
            logger.error(f"Failed to send daily schedule to user {user_id_str}: {e}")

async def check_upcoming_lessons_job(context: ContextTypes.DEFAULT_TYPE):
    # ... (логика времени не меняется) ...
    now = datetime.now(utils.TZ)
    check_time_min = (now + timedelta(minutes=14)).time()
    check_time_max = (now + timedelta(minutes=15)).time()
    day_str = utils.get_day_of_week_str('today')
    
    if 'sent_lesson_notifications' not in context.bot_data:
        context.bot_data['sent_lesson_notifications'] = set()

    all_settings = db_handler.get_all_user_settings()
    user_data_persistence = await context.application.persistence.get_user_data()

    for user_id_str, settings in all_settings.items():
        if not settings.get("notify_lesson"):
            continue

        try:
            user_id = int(user_id_str)
            user_data = user_data_persistence.get(user_id)
            
            if not user_data:
                continue
            
            lang = user_data.get('lang', 'uz')
            role = user_data.get("role")
            schedule = {}
            
            # ИЗМЕНЕНО: Логика для учителя/админа больше не нужна для этого job
            if role in ["student", "parent"]:
                class_id = user_data.get("class_id")
                if class_id:
                    schedule = db_handler.get_schedule_for_class(class_id)
            else:
                continue # Пропускаем

            today_lessons = schedule.get(day_str, [])
            
            for lesson_str in today_lessons:
                lesson_time_str = db_handler.parse_lesson_time(lesson_str)
                if not lesson_time_str:
                    continue
                
                lesson_start_time = datetime.strptime(lesson_time_str, '%H:%M').time()
                
                if check_time_min <= lesson_start_time <= check_time_max:
                    notification_key = (user_id, day_str, lesson_time_str)
                    
                    if notification_key not in context.bot_data['sent_lesson_notifications']:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=get_text(lang, 'notify_lesson_upcoming').format(lesson_str=lesson_str)
                        )
                        context.bot_data['sent_lesson_notifications'].add(notification_key)

        except Exception as e:
            logger.error(f"Failed to check lessons for user {user_id_str}: {e}")

async def clear_sent_notifications_job(context: ContextTypes.DEFAULT_TYPE):
    if 'sent_lesson_notifications' in context.bot_data:
        context.bot_data['sent_lesson_notifications'].clear()
    logger.info("Cleared sent lesson notifications cache.")


# --- Хендлеры ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    logger.info(f"User {user.username} (ID: {user.id}) started the bot.")
    
    context.user_data.clear()
    
    await update.message.reply_text(
        get_text('ru', 'welcome'),
        reply_markup=keyboards.get_language_keyboard(),
    )
    return STATE_LANG

# ИЗМЕНЕНО: Эта функция теперь "логинит" пользователя как ученика
async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang
    
    # --- Логика авто-логина ---
    user = update.effective_user
    role = "student" # Жестко задаем роль
    username = user.username if user.username else f"test_user_{user.id}"

    context.user_data["role"] = role
    context.user_data["user_id"] = user.id
    context.user_data["username"] = username.lower()
    # Создаем фейковые данные
    context.user_data["user_details"] = {
        "password": "test_mode",
        "role": role,
        "full_name": user.full_name or "Test User"
    }
    
    logger.info(f"Test user {username} (ID: {user.id}) auto-logged in as {role}.")
    
    # Сразу переходим к выбору класса, минуя STATE_LOGIN
    await query.edit_message_text(
        get_text(lang, 'login_success_class'), 
        reply_markup=keyboards.get_class_number_keyboard()
    )
    return STATE_CLASS_SELECT

# ИЗМЕНЕНО: ЭТА ФУНКЦИЯ БОЛЬШЕ НЕ НУЖНА
# async def handle_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     ... (весь код удален)


async def handle_class_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (эта функция не меняется) ...
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    
    class_num = query.data.split("_")[1]
    context.user_data["class_num"] = class_num
    
    available_letters = db_handler.get_class_letters(class_num)
    if not available_letters:
        await query.edit_message_text(get_text(lang, 'class_letters_not_found'))
        return STATE_CLASS_SELECT

    await query.edit_message_text(
        get_text(lang, 'class_num_selected').format(class_num=class_num),
        reply_markup=keyboards.get_class_letter_keyboard(available_letters)
    )
    return STATE_LETTER_SELECT

async def handle_class_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (эта функция не меняется) ...
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    
    class_letter = query.data.split("_")[1]
    class_num = context.user_data["class_num"]
    class_id = f"{class_num}{class_letter}"
    
    if not db_handler.get_schedule_for_class(class_id):
         await query.edit_message_text(get_text(lang, 'class_schedule_not_found').format(class_id=class_id))
         return STATE_LETTER_SELECT

    context.user_data["class_id"] = class_id
    logger.info(f"User {context.user_data['username']} selected class {class_id}")

    await query.edit_message_text(get_text(lang, 'class_selected').format(class_id=class_id))
    
    await query.message.reply_text(
        get_text(lang, 'main_menu'),
        reply_markup=keyboards.get_student_main_menu(lang)
    )
    return STATE_MENU_STUDENT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "uz")
    role = context.user_data.get("role")
    logger.info(f"User {context.user_data.get('username')} cancelled operation.")
    
    await update.message.reply_text(get_text(lang, 'action_cancelled'), reply_markup=ReplyKeyboardRemove())
    
    # ИЗМЕНЕНО: Оставляем логику только для ученика
    if role in ["student", "parent"]:
        await update.message.reply_text(get_text(lang, 'main_menu'), reply_markup=keyboards.get_student_main_menu(lang))
        return STATE_MENU_STUDENT
    
    # Если роли нет (или она 'teacher'/'admin', которых мы отключили), кидаем на старт
    return await start(update, context)

def main() -> None:


    persistence = PicklePersistence(filepath=config.PERSISTENCE_FILE)
    
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .persistence(persistence)
        .build()
    )

    # ... (JobQueue остается без изменений) ...
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_schedule_job, time=time(hour=7, minute=0, tzinfo=utils.TZ), name="daily_schedule")
    job_queue.run_repeating(check_upcoming_lessons_job, interval=60, first=10, name="check_lessons")
    job_queue.run_daily(clear_sent_notifications_job, time=time(hour=0, minute=1, tzinfo=utils.TZ), name="clear_notification_cache")

    # ИЗМЕНHЕНО: ConversationHandler УПРОЩЕН
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # --- Этапы входа (упрощенные) ---
            STATE_LANG: [
                CallbackQueryHandler(handle_language_selection, pattern="^lang_"),
            ],
            # ИЗМЕНЕНО: STATE_LOGIN удален
            STATE_CLASS_SELECT: [
                CallbackQueryHandler(handle_class_number, pattern="^class_num_"),
            ],
            STATE_LETTER_SELECT: [
                CallbackQueryHandler(handle_class_letter, pattern="^class_letter_"),
            ],
            
            # --- Меню Ученика (оставлено) ---
            STATE_MENU_STUDENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, student.route_main_menu),
            ],
            STATE_STUDENT_SCHEDULE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, student.route_schedule_menu),
            ],
            STATE_STUDENT_GRADES: [
                CallbackQueryHandler(student.send_grades_for_subject, pattern="^subject_"),
                CallbackQueryHandler(student.back_to_main_menu_inline, pattern="^back_to_main$"),
            ],
            STATE_STUDENT_SETTINGS: [
                CallbackQueryHandler(student.toggle_notification, pattern="^toggle_"),
                CallbackQueryHandler(student.change_credentials, pattern="^change_creds$"),
                CallbackQueryHandler(student.back_to_main_menu_inline, pattern="^back_to_main$"),
            ],
            STATE_SETTINGS_CHANGE_CREDS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, student.update_credentials),
            ],

            # ИЗМЕНЕНО: Все состояния Учителя и Админа УДАЛЕНЫ
            # STATE_MENU_TEACHER: [...],
            # STATE_TEACHER_SCHEDULE: [...],
            # ...
            # STATE_MENU_ADMIN: [...],
            # STATE_ADMIN_SCHEDULE: [...],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        persistent=True,
        name="main_conversation",
    )

    application.add_handler(conv_handler)

    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    # ИЗМЕНЕНО: Добавлены импорты для JobQueue, которые были удалены по ошибке
    # from datetime import datetime, timedelta
    
    main()
