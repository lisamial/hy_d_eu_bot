import os
import psycopg2

from psycopg2.extras import RealDictCursor
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

BOT_TOKEN = "8253855152:AAFm4wNtc5p12t3Y3TXGEaTcib2QUVs9KS0" #os.environ.get("BOT_TOKEN_RW")
DATABASE_URL = "postgresql://postgres:TjbTSYOaJuBQcfvJrmomppQUMXcIFfUV@metro.proxy.rlwy.net:31874/railway"  # or use
#os.getenv("DATABASE_URL")

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

def get_bd_connection():
    """Функция для получения соединения с базой данных."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Функция для логирования таблеток
def log_tablets(user_id, tablet_name):
    conn = get_bd_connection()
    cur = conn.cursor()
    date = datetime.now()

    cur.execute(
        "INSERT INTO tablets (user_id, tablet_name, date) VALUES (%s, %s, %s)",
        (user_id, tablet_name, date)
    )
    conn.commit()
    cur.close()
    conn.close()

def log_pain(user_id, pain, painkillers, result_pain):
    conn = get_bd_connection()
    cur = conn.cursor()
    date = datetime.now()
    cur.execute(
        "INSERT INTO pain (user_id, pain, painkillers, result_pain, date) VALUES (%s, %s, %s, %s, %s)",
        (user_id, pain, painkillers, result_pain, date)
    )
    conn.commit()
    cur.close()
    conn.close()

def insert_user_data(user_id, height, weight, waist, hips, breast, arm, leg):
    date = datetime.now()
    conn = get_bd_connection()
    cur = conn.cursor()
    date = datetime.now()
    cur.execute(
        "INSERT INTO users (telegram_id, height, start_weight, start_waist, start_hips, start_breast, start_arm, start_leg, start_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, height, weight, waist, hips, breast, arm, leg, date)
    )
    conn.commit()
    cur.close()
    conn.close()
    

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step", 0)
    height = context.user_data.get("height", 0)
    weight = context.user_data.get("weight", 0)
    waist = context.user_data.get("waist", 0)
    hips = context.user_data.get("hips", 0)
    breast = context.user_data.get("breast", 0)
    arm = context.user_data.get("arm", 0)
    leg = context.user_data.get("leg", 0)
    
    # height, weight, waist, hips, breast, arm, leg
    if step == 0:
        await update.message.reply_text(
                "Привет! Я твой ЗОЖ-бот-компаньон 💪\n\n"
                "Сейчас нужно заполнить эту скушную херню, ты знаешь типо вес, рост, размер your ASS. \n\n"
                "Начнем с роста (в см)"
        )
        context.user_data["step"] = 1
    elif step == 1:    
        height = update.message.text 
        await update.message.reply_text("Вес (в кг):")
        context.user_data["step"] = 2
    elif step == 2:
        weight = update.message.text
        await update.message.reply_text(
            "Сейчас самое сложное:\n\n" 
            "Нужны твои замеры (в см) \n\n" 
            "Отправь через /: обхват талии/ обхват бедер/ обхват груди/ обхват плеча/ обхват ляжки"
        )
        context.user_data["step"] = 3
    else: 
        paramStr = update.message.text
        param = paramStr.split("/")
        if param:
            insert_user_data()
        waist = param[0]
        hips = param[1]
        breast = param[2]
        arm = param[3]
        leg = param[4]




async def printMess(update: Update, context: ContextTypes.DEFAULT_TYPE, text):
    await update.message.reply_text(text)
    return update.message.text


# HEIGHT
async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["height"] = update.message.text
    await update.message.edit_text("Отлишно! А теперь твой вес (в кг)")
    return WEIGHT

# WEIGHT
async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["weight"] = update.message.text
    await update.message.edit_text("Супер! Напиши свои объёмы (грудь/талия/бедра)")
    return VOLUMES

# VOLUMES
async def get_volumes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["volumes"] = update.message.text
    await update.message.edit_text("Укажи дату старта (например: 05.08.2025)")
    return START_DATE

# START DATE
async def get_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["start_date"] = update.message.text
    await update.message.edit_text(
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

    await update.message.edit_text(
        f"Добавлено: {tracker}\n\n"
        f"Можешь выбрать ещё или напиши «Готово», когда всё выберешь"
    )
    return SELECT_TRACKERS

# DONE
async def finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data[user_id] = context.user_data.copy()

    await update.message.edit_text(
        "🎉 Готово! Я запомнил твои параметры и выбранные функции.\n"
        "Скоро начнём отслеживание 💚"
    )
    return ConversationHandler.END

# CANCEL
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.edit_text("Настройка отменена. Напиши /start, чтобы начать заново.")
    return ConversationHandler.END


if __name__ == "__main__":
   
    get_bd_connection()
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
