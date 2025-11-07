import logging, uuid, json, asyncio
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ( ContextTypes, ConversationHandler, MessageHandler,
                          CallbackQueryHandler, CommandHandler, filters, )
import google.generativeai as genai
import database as db
import keyboards as kb
from bot import ( STUDENT_MAIN, TEACHER_MAIN, ADMIN_MAIN, 
    ADMIN_REGISTER_STEP_1_NAME, ADMIN_REGISTER_STEP_2_LASTNAME,
    ADMIN_REGISTER_STEP_3_CLASS, ADMIN_REGISTER_STEP_4_LETTER,
    ADMIN_REGISTER_STEP_5_LOGIN, ADMIN_REGISTER_STEP_6_PASS,
    ADMIN_EDIT_SCHEDULE 
    )

logger = logging.getLogger(__name__)
GEMINI_API_KEY = "AIzaSyDYKPNqqBirAqSP7B_PWT8J2hJruC8tjq8"

MESSAGES = {
    'ru': {
        'back_to_main': "Главное меню",
        'cancel_register': "❌ Регистрация ученика отменена.",
        'register_start': "<b>Регистрация нового ученика</b>\n\n(Чтобы отменить, введите /cancel в любой момент)\n\n<b>Шаг 1/6:</b> Введите <b>Имя</b> ученика:",
        'register_step_2': "Отлично, Имя: <b>{first_name}</b>\n\n<b>Шаг 2/6:</b> Введите <b>Фамилию</b> ученика:",
        'register_step_3': "Фамилия: <b>{last_name}</b>\n\n<b>Шаг 3/6:</b> Введите <b>Класс</b> (только цифру, например, <code>10</code>):",
        'register_step_4': "Класс: <b>{class_num}</b>\n\n<b>Шаг 4/6:</b> Введите <b>Букву</b> класса (например, <code>А</code>):",
        'register_step_5': "Буква: <b>{letter}</b>\n\n<b>Шаг 5/6:</b> Введите <b>Логин</b> для ученика (username):",
        'register_step_6': "Логин: <code>{username}</code>\n\n<b>Шаг 6/6:</b> Введите <b>Пароль</b> для ученика:",
        'register_success': "✅ <b>Ученик успешно зарегистрирован!</b>\n\n"
                            "<b>Имя:</b> {first_name}\n"
                            "<b>Фамилия:</b> {last_name}\n"
                            "<b>Класс:</b> {class_letter}\n"
                            "<b>Логин:</b> <code>{username}</code>\n"
                            "<b>Пароль:</b> <code>{password}</code>\n"
                            "<b>ID в базе:</b> <code>{db_id}</code>",
        'register_username_exists': "❌ Этот логин (<code>{username}</code>) уже занят. Попробуйте другой.\n\n<b>Шаг 5/6:</b> Введите <b>Логин</b>:",
        'schedule_edit_prompt': "<b>Редактор Расписания (AI)</b>\n\n"
                                "Отправьте мне расписание в любом формате. Я постараюсь его распознать и обновить базу данных.\n\n"
                                "<b>Пример:</b>\n"
                                "<code>Понедельник 10А:\n1. Математика\n2. Физика\n...</code>\n"
                                "<code>10Б в среду:\n1. Химия</code>\n\n"
                                "(Чтобы отменить, введите /cancel)",
        'schedule_edit_processing': "⏳ Получил. Обрабатываю расписание... (Это может занять до 30 секунд)",
        'schedule_edit_success': "✅ Расписание успешно обновлено!",
        'schedule_edit_error_api': "❌ Ошибка API Gemini. Попробуйте позже.",
        'schedule_edit_error_json': "❌ AI вернул некорректные данные. Не удалось обновить расписание.",
        'schedule_edit_error_missing_info': "❓ Недостаточно информации. {ai_question}\n\nПожалуйста, уточните ваш запрос.",
        'schedule_edit_cancel': "Редактирование расписания отменено."
    },
    'en': {
        'back_to_main': "Main Menu",
        'cancel_register': "❌ Student registration cancelled.",
        'register_start': "<b>New Student Registration</b>\n\n(To cancel, type /cancel at any time)\n\n<b>Step 1/6:</b> Enter the student's <b>First Name</b>:",
        'register_step_2': "Great, First Name: <b>{first_name}</b>\n\n<b>Step 2/6:</b> Enter the student's <b>Last Name</b>:",
        'register_step_3': "Last Name: <b>{last_name}</b>\n\n<b>Step 3/6:</b> Enter the <b>Grade</b> (numbers only, e.g. <code>10</code>):",
        'register_step_4': "Grade: <b>{class_num}</b>\n\n<b>Step 4/6:</b> Enter the <b>Letter</b> of the class (e.g. <code>A</code>):",
        'register_step_5': "Letter: <b>{letter}</b>\n\n<b>Step 5/6:</b> Enter a <b>Username</b> for the student:",
        'register_step_6': "Username: <code>{username}</code>\n\n<b>Step 6/6:</b> Enter a <b>Password</b> for the student:",
        'register_success': "✅ <b>Student successfully registered!</b>\n\n"
                            "<b>First Name:</b> {first_name}\n"
                            "<b>Last Name:</b> {last_name}\n"
                            "<b>Class:</b> {class_letter}\n"
                            "<b>Username:</b> <code>{username}</code>\n"
                            "<b>Password:</b> <code>{password}</code>\n"
                            "<b>Database ID:</b> <code>{db_id}</code>",
        'register_username_exists': "❌ This username (<code>{username}</code>) is already taken. Try another one.\n\n<b>Step 5/6:</b> Enter a <b>Username</b>:",
        'schedule_edit_prompt': "<b>Schedule Editor (AI)</b>\n\n"
                                "Send me the schedule in any format. I’ll try to recognize it and update the database.\n\n"
                                "<b>Example:</b>\n"
                                "<code>Monday 10A:\n1. Math\n2. Physics\n...</code>\n"
                                "<code>10B on Wednesday:\n1. Chemistry</code>\n\n"
                                "(To cancel, type /cancel)",
        'schedule_edit_processing': "⏳ Got it. Processing the schedule... (This may take up to 30 seconds)",
        'schedule_edit_success': "✅ Schedule successfully updated!",
        'schedule_edit_error_api': "❌ Gemini API error. Please try again later.",
        'schedule_edit_error_json': "❌ AI returned invalid data. Could not update the schedule.",
        'schedule_edit_error_missing_info': "❓ Not enough information. {ai_question}\n\nPlease clarify your request.",
        'schedule_edit_cancel': "Schedule editing cancelled."
    },
    'uz': {
        'back_to_main': "Asosiy menyu",
        'cancel_register': "❌ O‘quvchi ro‘yxatdan o‘tishi bekor qilindi.",
        'register_start': "<b>Yangi o‘quvchini ro‘yxatdan o‘tkazish</b>\n\n(Bekor qilish uchun istalgan payt /cancel deb yozing)\n\n<b>1-qadam/6:</b> O‘quvchining <b>Ismini</b> kiriting:",
        'register_step_2': "Ajoyib, Ismi: <b>{first_name}</b>\n\n<b>2-qadam/6:</b> O‘quvchining <b>Familiyasini</b> kiriting:",
        'register_step_3': "Familiyasi: <b>{last_name}</b>\n\n<b>3-qadam/6:</b> <b>Sinf raqamini</b> kiriting (faqat raqam, masalan, <code>10</code>):",
        'register_step_4': "Sinf raqami: <b>{class_num}</b>\n\n<b>4-qadam/6:</b> <b>Sinf harfini</b> kiriting (masalan, <code>A</code>):",
        'register_step_5': "Sinf harfi: <b>{letter}</b>\n\n<b>5-qadam/6:</b> O‘quvchi uchun <b>foydalanuvchi nomi</b> (username) kiriting:",
        'register_step_6': "Foydalanuvchi nomi: <code>{username}</code>\n\n<b>6-qadam/6:</b> O‘quvchi uchun <b>parol</b> kiriting:",
        'register_success': "✅ <b>O‘quvchi muvaffaqiyatli ro‘yxatdan o‘tkazildi!</b>\n\n"
                            "<b>Ismi:</b> {first_name}\n"
                            "<b>Familiyasi:</b> {last_name}\n"
                            "<b>Sinf:</b> {class_letter}\n"
                            "<b>Foydalanuvchi nomi:</b> <code>{username}</code>\n"
                            "<b>Parol:</b> <code>{password}</code>\n"
                            "<b>Bazadagi ID:</b> <code>{db_id}</code>",
        'register_username_exists': "❌ Ushbu foydalanuvchi nomi (<code>{username}</code>) band. Boshqasini tanlang.\n\n<b>5-qadam/6:</b> Yangi <b>foydalanuvchi nomini</b> kiriting:",
        'schedule_edit_prompt': "<b>Dars jadvali muharriri (AI)</b>\n\n"
                                "Jadvalni istalgan formatda yuboring. Men uni aniqlab, bazani yangilayman.\n\n"
                                "<b>Misol:</b>\n"
                                "<code>Dushanba 10A:\n1. Matematika\n2. Fizika\n...</code>\n"
                                "<code>10B chorshanba kuni:\n1. Kimyo</code>\n\n"
                                "(Bekor qilish uchun /cancel deb yozing)",
        'schedule_edit_processing': "⏳ Qabul qilindi. Jadval qayta ishlanmoqda... (Bu 30 soniyagacha davom etishi mumkin)",
        'schedule_edit_success': "✅ Jadval muvaffaqiyatli yangilandi!",
        'schedule_edit_error_api': "❌ Gemini API xatosi. Keyinroq urinib ko‘ring.",
        'schedule_edit_error_json': "❌ AI noto‘g‘ri ma’lumot qaytardi. Jadval yangilanmadi.",
        'schedule_edit_error_missing_info': "❓ Yetarli ma’lumot yo‘q. {ai_question}\n\nIltimos, so‘rovingizni aniqlashtiring.",
        'schedule_edit_cancel': "Jadvalni tahrirlash bekor qilindi."
    }
}

def get_adm_msg(key, lang='ru'):
    lang_dict = MESSAGES.get(lang, MESSAGES['ru'])
    msg = lang_dict.get(key)
    if msg is None: 
        msg = MESSAGES['ru'].get(key, f"_{key}_")
    return msg

def get_user_data(context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('lang', 'ru')
    user_info = context.user_data.get('user_info', {})
    db_id = context.user_data.get('db_id')
    return lang, user_info, db_id

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_adm_msg('back_to_main', lang),
        reply_markup=kb.get_admin_main_keyboard(lang)
    )
    return ADMIN_MAIN

async def handle_register_student(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    context.user_data['new_student_data'] = {}
    await update.message.reply_text(
        get_adm_msg('register_start', lang),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='HTML'
    )
    return ADMIN_REGISTER_STEP_1_NAME

async def handle_edit_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_adm_msg('schedule_edit_prompt', lang),
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='HTML'
    )
    return ADMIN_EDIT_SCHEDULE

async def cancel_register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    context.user_data.pop('new_student_data', None)
    await update.message.reply_text(
        get_adm_msg('cancel_register', lang),
        reply_markup=kb.get_admin_main_keyboard(lang)
    )
    return ADMIN_MAIN

async def register_step_1_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    first_name = update.message.text
    context.user_data['new_student_data'] = {'first_name': first_name}
    await update.message.reply_text(
        get_adm_msg('register_step_2', lang).format(first_name=first_name),
        parse_mode='HTML'
    )
    return ADMIN_REGISTER_STEP_2_LASTNAME

async def register_step_2_lastname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    last_name = update.message.text
    context.user_data['new_student_data']['last_name'] = last_name
    await update.message.reply_text(
        get_adm_msg('register_step_3', lang).format(last_name=last_name),
        parse_mode='HTML'
    )
    return ADMIN_REGISTER_STEP_3_CLASS

async def register_step_3_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    class_num = update.message.text
    if not class_num.isdigit():
        await update.message.reply_text("ОШИБКА: Введите только цифру класса (например, 10). Попробуйте еще раз.")
        return ADMIN_REGISTER_STEP_3_CLASS
    context.user_data['new_student_data']['class'] = class_num
    await update.message.reply_text(
        get_adm_msg('register_step_4', lang).format(class_num=class_num),
        parse_mode='HTML'
    )
    return ADMIN_REGISTER_STEP_4_LETTER

async def register_step_4_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    letter = update.message.text.upper()
    if len(letter) > 2 or not letter.isalpha():
        await update.message.reply_text("Ошибка: Введите только букву класса (например, А). Попробуйте еще раз.")
        return ADMIN_REGISTER_STEP_4_LETTER
    context.user_data['new_student_data']['letter'] = letter
    await update.message.reply_text(
        get_adm_msg('register_step_5', lang).format(letter=letter),
        parse_mode='HTML'
    )
    return ADMIN_REGISTER_STEP_5_LOGIN

async def register_step_5_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    username = update.message.text.lower()
    if len(username.split()) > 1:
        await update.message.reply_text("Логин не должен содержать пробелов. Попробуйте еще раз.")
        return ADMIN_REGISTER_STEP_5_LOGIN
    db_id, user = db.find_user_by_username(username, 'student')
    if user:
        await update.message.reply_text(
            get_adm_msg('register_username_exists', lang).format(username=username),
            parse_mode='HTML'
        )
        return ADMIN_REGISTER_STEP_5_LOGIN
    context.user_data['new_student_data']['username'] = username
    await update.message.reply_text(
        get_adm_msg('register_step_6', lang).format(username=username),
        parse_mode='HTML'
    )
    return ADMIN_REGISTER_STEP_6_PASS

async def register_step_6_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    password = update.message.text
    student_data = context.user_data.pop('new_student_data', {})
    student_data['password'] = password
    student_data['lang'] = 'ru'
    student_data['warning_about_next_lesson'] = True
    student_data['warning_everyday_about_lessons'] = False
    new_db_id = f"new_{student_data['class']}{student_data['letter']}_{uuid.uuid4()}"
    all_students = db.get_all_students()
    all_students[new_db_id] = student_data
    db.save_all_students(all_students)
    await update.message.reply_text(
        get_adm_msg('register_success', lang).format(
            first_name=student_data['first_name'],
            last_name=student_data['last_name'],
            class_letter=f"{student_data['class']}{student_data['letter']}",
            username=student_data['username'],
            password=student_data['password'],
            db_id=new_db_id
        ),
        parse_mode='HTML',
        reply_markup=kb.get_admin_main_keyboard(lang)
    )
    return ADMIN_MAIN

async def call_gemini_for_schedule(raw_text: str, current_schedule: dict) -> tuple[dict | None, str | None]:
    system_prompt = f"""
Ты - ассистент директора школы, отвечающий за расписание.
Твоя задача - принять текст от администратора и ПРЕОБРАЗОВАТЬ его в СТРОГИЙ JSON формат.
Текущее расписание (если нужно обновить):
{json.dumps(current_schedule, indent=2, ensure_ascii=False)}

ПРАВИЛА:
1.  Ты ДОЛЖЕН вернуть ТОЛЬКО JSON. Никакого текста до или после.
2.  Формат JSON:
    {{
        "10А": {{
            "monday": {{
                "1": "Математика",
                "2": "Физика"
            }},
            "tuesday": {{...}}
        }},
        "10Б": {{...}}
    }}
3.  Дни недели: 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'.
4.  Классы: Ключ - это класс + буква (например, "10А", "9В").
5.  Уроки: Ключ - номер урока (строка "1", "2", ...).
6.  Если в тексте пользователя не хватает информации (например, не указан класс или день недели), НЕ ДОДУМЫВАЙ.
    Вместо JSON, верни JSON-объект с запросом на уточнение:
    {{
        "error": "missing_info",
        "question": "Для какого класса это расписание на Понедельник?"
    }}
7.  Если пользователь хочет ОЧИСТИТЬ расписание (например, "у 10А нет уроков во вторник"), верни пустой объект для этого дня:
    "10А": {{ "tuesday": {{}} }}
8.  ОБНОВЛЯЙ текущее расписание, а не заменяй его полностью, если запрос частичный.
"""
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    response = await model.generate_content_async(raw_text)
    response_json = json.loads(response.text)
    if "error" in response_json and response_json["error"] == "missing_info":
        return None, response_json.get("question", "Нужны уточнения.")
    return response_json, None

async def receive_schedule_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    raw_text = update.message.text
    await update.message.reply_text(get_adm_msg('schedule_edit_processing', lang))
    current_schedule = db.get_schedule()
    new_data, error_or_question = await call_gemini_for_schedule(raw_text, current_schedule)
    if error_or_question:
        if "API" in error_or_question:
            await update.message.reply_text(get_adm_msg('schedule_edit_error_api', lang))
        else:
            await update.message.reply_text(
                get_adm_msg('schedule_edit_error_missing_info', lang).format(ai_question=error_or_question)
            )
        return ADMIN_EDIT_SCHEDULE 
    if new_data:
        for class_key, days_schedule in new_data.items():
            if class_key not in current_schedule:
                current_schedule[class_key] = {}
            for day_key, lessons in days_schedule.items():
                current_schedule[class_key][day_key] = lessons
        db.save_schedule(current_schedule)
        await update.message.reply_text(get_adm_msg('schedule_edit_success', lang))
        await update.message.reply_text(get_adm_msg('schedule_edit_error_json', lang))
    else:
        await update.message.reply_text(get_adm_msg('schedule_edit_error_api', lang))
    return await back_to_main(update, context)

async def cancel_edit_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    lang, _, _ = get_user_data(context)
    await update.message.reply_text(
        get_adm_msg('schedule_edit_cancel', lang),
        reply_markup=kb.get_admin_main_keyboard(lang)
    )
    return ADMIN_MAIN
