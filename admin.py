import logging
import json
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import google.generativeai as genai

# ИЗМЕНЕНО: Добавлены импорты
from localization import get_text
import db_handler
import config
from states import STATE_MENU_ADMIN, STATE_ADMIN_SCHEDULE

logger = logging.getLogger(__name__)

# ... (Настройка Gemini и СИСТЕМНЫЙ ПРОМПТ остаются без изменений) ...
if config.GEMINI_API_KEY:
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        logger.info("Gemini API configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini: {e}")
        
else:
    logger.warning("GEMINI_API_KEY not set. Admin features will be limited.")


# Системный промпт для Gemini
GEMINI_SYSTEM_PROMPT = """
Ты - ИИ-ассистент для управления школьным расписанием.
Твоя задача - принимать запросы на естественном языке от администратора и преобразовывать их в JSON-объект для обновления базы данных.

База данных (schedule.json) имеет формат:
{
  "9А": {
    "monday": ["1. Математика", "2. Физика"],
    "tuesday": ["1. Литература"]
  },
  "10Б": { ... }
}

Твой ответ ДОЛЖЕН БЫТЬ в одном из двух форматов:

1.  **Если запрос понятен и содержит всю информацию (класс, день, уроки):**
    Ты должен вернуть ТОЛЬКО JSON-объект (без ```json и прочего) следующего вида:
    {
      "status": "success",
      "class_id": "9А",
      "day": "monday",
      "lessons": ["1. Новый Урок 1", "2. Новый Урок 2"]
    }
    (Ключи дней: "monday", "tuesday", "wednesday", "thursday", "friday", "saturday")
    (Убедись, что название класса (class_id) точно соответствует запросу, включая букву).

2.  **Если в запросе не хватает информации (не указан класс, день недели или сами уроки):**
    Ты должен вернуть ТОЛЬКО JSON-объект:
    {
      "status": "clarify",
      "question": "Пожалуйста, уточните, для какого класса и на какой день недели нужно внести эти изменения?"
    }

ЗАПРЕЩЕНО отвечать обычным текстом. Только JSON.
"""



# ИЗМЕНЕНО: Добавлен роутер главного меню
async def route_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Маршрутизатор для главного меню админа."""
    lang = context.user_data.get('lang', 'uz')
    text = update.message.text

    if text == get_text(lang, 'btn_admin_schedule'):
        return await handle_schedule_update(update, context)
    else:
        await update.message.reply_text(get_text(lang, 'unknown_command'))
        return STATE_MENU_ADMIN


async def handle_schedule_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает диалог обновления расписания."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    
    await update.message.reply_text(
        # ИЗМЕНЕНО: get_text
        get_text(lang, 'admin_schedule_prompt'),
        reply_markup=ReplyKeyboardRemove()
    )
    
    if config.GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
                system_instruction=GEMINI_SYSTEM_PROMPT
            )
        except Exception as e:
            # ИЗМЕНЕНО: get_text
            await update.message.reply_text(get_text(lang, 'admin_gemini_init_error').format(e=e))
            return STATE_MENU_ADMIN
    
    return STATE_ADMIN_SCHEDULE

async def process_schedule_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает текст админа через Gemini."""
    # ИЗМЕНЕНО: lang
    lang = context.user_data.get('lang', 'uz')
    user_text = update.message.text
    
    if not config.GEMINI_API_KEY:
        # ИЗМЕНЕНО: get_text
        await update.message.reply_text(get_text(lang, 'admin_gemini_config_error'))
        return STATE_ADMIN_SCHEDULE

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=GEMINI_SYSTEM_PROMPT
        )
        
        response = await model.generate_content_async(user_text)
        gemini_response_text = response.text.strip()
        logger.info(f"Gemini raw response: {gemini_response_text}")

        # 1. Проверяем, что ответ - это JSON
        if not gemini_response_text.startswith('{') or not gemini_response_text.endswith('}'):
            logger.error(f"Gemini returned non-JSON response: {gemini_response_text}")
            if "```json" in gemini_response_text:
                gemini_response_text = gemini_response_text.split("```json")[1].split("```")[0].strip()
            else:
                # ИЗМЕНЕНО: get_text
                await update.message.reply_text(get_text(lang, 'admin_gemini_non_json_error'))
                return STATE_ADMIN_SCHEDULE
        
        # 2. Парсим JSON
        try:
            data = json.loads(gemini_response_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from Gemini: {gemini_response_text}")
            # ИЗМЕНЕНО: get_text
            await update.message.reply_text(get_text(lang, 'admin_gemini_json_decode_error'))
            return STATE_ADMIN_SCHEDULE

        # 3. Обрабатываем ответ
        if data.get("status") == "success":
            if not all(k in data for k in ["class_id", "day", "lessons"]):
                 # ИЗМЕНЕНО: get_text
                 await update.message.reply_text(get_text(lang, 'admin_gemini_missing_keys_error'))
                 return STATE_ADMIN_SCHEDULE

            db_handler.update_schedule(
                data["class_id"], 
                data["day"], 
                data["lessons"]
            )
            # ИЗМЕНЕНО: get_text
            await update.message.reply_text(
                get_text(lang, 'admin_schedule_updated').format(class_id=data['class_id'], day=data['day'])
            )
            
        elif data.get("status") == "clarify":
            # ИЗМЕНЕНО: Улучшенная логика с get_text
            question = data.get('question')
            if question:
                await update.message.reply_text(get_text(lang, 'admin_gemini_clarify').format(question=question))
            else:
                await update.message.reply_text(get_text(lang, 'admin_gemini_clarify_default'))
            
        else:
            # ИЗМЕНЕНО: get_text
            await update.message.reply_text(get_text(lang, 'admin_gemini_internal_error'))
            
    except Exception as e:
        logger.error(f"Error processing Gemini request: {e}")
        # ИЗМЕНЕНО: get_text
        await update.message.reply_text(get_text(lang, 'admin_gemini_api_error').format(e=e))

    return STATE_ADMIN_SCHEDULE
