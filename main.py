import os
import psycopg2

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN_RW")
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Этапы диалога
(HEIGHT, WEIGHT, VOLUMES, START_DATE, SELECT_TRACKERS) = range(5)

# Временное хранилище пользователей
user_data = {}

# Кнопки для выбора функционала
TRACKER_OPTIONS = [
    ["💧 Вода", "⚡ Зарядка"],
    ["💊 Таблетки", "🍽️ Меню"],
    ["🤕 Головная боль"],
]

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я твой ЗОЖ-бот-компаньон 💪\n\n"
        "Сейчас нужно заполнить эту скушную херню, ты знаешь типо вес, рост, размер your ASS. \n\n"
        "Начнем с роста (в см)"
    )
    return HEIGHT

# HEIGHT
async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = update.message.text
    await update.message.reply_text("Отлишно! А теперь твой вес (в кг)")
    return WEIGHT

# WEIGHT
async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["weight"] = update.message.text
    await update.message.reply_text("Супер! Напиши свои объёмы (грудь/талия/бедра)")
    return VOLUMES

# VOLUMES
async def get_volumes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["volumes"] = update.message.text
    await update.message.reply_text("Укажи дату старта (например: 05.08.2025)")
    return START_DATE

# START DATE
async def get_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["start_date"] = update.message.text
    await update.message.reply_text(
        "Теперь выбери, что ты хочешь отслеживать 📝",
        reply_markup=ReplyKeyboardMarkup(TRACKER_OPTIONS, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECT_TRACKERS

# SELECT TRACKERS
async def select_trackers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tracker = update.message.text

    if "trackers" not in context.user_data:
        context.user_data["trackers"] = []

    if tracker not in context.user_data["trackers"]:
        context.user_data["trackers"].append(tracker)

    await update.message.reply_text(
        f"Добавлено: {tracker}\n\n"
        f"Можешь выбрать ещё или напиши «Готово», когда всё выберешь"
    )
    return SELECT_TRACKERS

# DONE
async def finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = context.user_data.copy()

    await update.message.reply_text(
        "🎉 Готово! Я запомнил твои параметры и выбранные функции.\n"
        "Скоро начнём отслеживание 💚"
    )
    return ConversationHandler.END

# CANCEL
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Настройка отменена. Напиши /start, чтобы начать заново.")
    return ConversationHandler.END


if __name__ == "__main__":
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print(f"✅ Подключено к базе: {db_version}")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            VOLUMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_volumes)],
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_date)],
            SELECT_TRACKERS: [
                MessageHandler(filters.Regex("^(💧 Вода|⚡ Зарядка|💊 Таблетки|🍽️ Меню|🤕 Головная боль)$"), select_trackers),
                MessageHandler(filters.TEXT & ~filters.COMMAND, finish_setup),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
