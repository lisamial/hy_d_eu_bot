import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1JImz1gXRHDnp7CtUdxUUsQRtgafJwzdwA_PE4sokNdU/edit?usp=sharing"

def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_url(GOOGLE_SHEET_URL)
    return sh.sheet1  # Первый лист

def log_daily_data(
    date_str: str,
    venlafaxine_morning: bool,
    venlafaxine_evening: bool,
    anaprilin_morning: bool,
    anaprilin_evening: bool,
    hormon: bool,
    iron: bool,
    vitamins: bool,
    headache: bool,
    painkiller: bool,
    recovered: bool
):
    ws = get_sheet()
    # Подготавливаем строку в соответствие с колонками
    row = [
        date_str,
        "1" if venlafaxine_morning else "",  # если принимала — 1, иначе пусто
        "1" if venlafaxine_evening else "",
        "1" if anaprilin_morning else "",
        "1" if anaprilin_evening else "",
        "1" if hormon else "",
        "1" if iron else "",
        "1" if vitamins else "",
        "Да" if headache else "Нет",
        "Да" if painkiller else "Нет",
        "Да" if recovered else "Нет"
    ]
    ws.append_row(row)

# ---------- Бот ------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Заполнить дневные данные", callback_data="daily_data")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Хочешь ввести данные за сегодня?", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "daily_data":
        # Сначала спросим про утро / вечер таблетки: Венлафаксин утра
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="venlaf_morn_yes"),
             InlineKeyboardButton("Нет", callback_data="venlaf_morn_no")]
        ]
        await query.edit_message_text("Приняла ли Венлафаксин утром?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["venlaf_morn_yes", "venlaf_morn_no"]:
        context.user_data["venlaf_morning"] = (query.data == "venlaf_morn_yes")
        # Продолжаем: Венлафаксин вечером
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="venlaf_even_yes"),
             InlineKeyboardButton("Нет", callback_data="venlaf_even_no")]
        ]
        await query.edit_message_text("Приняла ли Венлафаксин вечером?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["venlaf_even_yes", "venlaf_even_no"]:
        context.user_data["venlaf_evening"] = (query.data == "venlaf_even_yes")
        # Спросим про Анаприлин утром
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="anapr_morn_yes"),
             InlineKeyboardButton("Нет", callback_data="anapr_morn_no")]
        ]
        await query.edit_message_text("Приняла ли Анаприлин утром?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["anapr_morn_yes", "anapr_morn_no"]:
        context.user_data["anaprilin_morning"] = (query.data == "anapr_morn_yes")
        # Анаприлин вечером
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="anapr_even_yes"),
             InlineKeyboardButton("Нет", callback_data="anapr_even_no")]
        ]
        await query.edit_message_text("Приняла ли Анаприлин вечером?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["anapr_even_yes", "anapr_even_no"]:
        context.user_data["anaprilin_evening"] = (query.data == "anapr_even_yes")
        # Гормон
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="hormon_yes"),
             InlineKeyboardButton("Нет", callback_data="hormon_no")]
        ]
        await query.edit_message_text("Приняла гормон?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["hormon_yes", "hormon_no"]:
        context.user_data["hormon"] = (query.data == "hormon_yes")
        # Железо
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="iron_yes"),
             InlineKeyboardButton("Нет", callback_data="iron_no")]
        ]
        await query.edit_message_text("Приняла железо?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["iron_yes", "iron_no"]:
        context.user_data["iron"] = (query.data == "iron_yes")
        # Витамины
        keyboard = [
            [InlineKeyboardButton("Да", callback_data="vitamins_yes"),
             InlineKeyboardButton("Нет", callback_data="vitamins_no")]
        ]
        await query.edit_message_text("Приняла витамины?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["vitamins_yes", "vitamins_no"]:
        context.user_data["vitamins"] = (query.data == "vitamins_yes")
        # Спрашиваем про головную боль
        keyboard = [
            [InlineKeyboardButton("Голова болела", callback_data="headache_yes"),
             InlineKeyboardButton("Не болела", callback_data="headache_no")]
        ]
        await query.edit_message_text("Болела ли голова сегодня?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["headache_yes", "headache_no"]:
        context.user_data["headache"] = (query.data == "headache_yes")
        # Если болела - спрашиваем про обезбол и результат
        if context.user_data["headache"]:
            keyboard = [
                [InlineKeyboardButton("Пила обезбол", callback_data="painkiller_yes"),
                 InlineKeyboardButton("Не пила", callback_data="painkiller_no")]
            ]
            await query.edit_message_text("Приняла ли обезболивающее?", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            context.user_data["painkiller"] = False
            context.user_data["recovered"] = False
            # Записываем сразу и завершаем
            date_str = datetime.now().strftime("%d.%m.%Y")
            log_daily_data(
                date_str,
                venlafaxine_morning=context.user_data.get("venlaf_morning", False),
                venlafaxine_evening=context.user_data.get("venlaf_evening", False),
                anaprilin_morning=context.user_data.get("anaprilin_morning", False),
                anaprilin_evening=context.user_data.get("anaprilin_evening", False),
                hormon=context.user_data.get("hormon", False),
                iron=context.user_data.get("iron", False),
                vitamins=context.user_data.get("vitamins", False),
                headache=False,
                painkiller=False,
                recovered=False
            )
            await query.edit_message_text("✅ Всё записано за сегодня!")
    
    elif query.data in ["painkiller_yes", "painkiller_no"]:
        took = (query.data == "painkiller_yes")
        context.user_data["painkiller"] = took
        if took:
            # спрашиваем, помог ли обезбол
            keyboard = [
                [InlineKeyboardButton("Прошла", callback_data="recovered_yes"),
                 InlineKeyboardButton("Не прошла", callback_data="recovered_no")]
            ]
            await query.edit_message_text("Обезбол помог?", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            context.user_data["recovered"] = False
            # записываем сразу
            date_str = datetime.now().strftime("%d.%m.%Y")
            log_daily_data(
                date_str,
                venlafaxine_morning=context.user_data.get("venlaf_morning", False),
                venlafaxine_evening=context.user_data.get("venlaf_evening", False),
                anaprilin_morning=context.user_data.get("anaprilin_morning", False),
                anaprilin_evening=context.user_data.get("anaprilin_evening", False),
                hormon=context.user_data.get("hormon", False),
                iron=context.user_data.get("iron", False),
                vitamins=context.user_data.get("vitamins", False),
                headache=True,
                painkiller=False,
                recovered=False
            )
            await query.edit_message_text("✅ Всё записано за сегодня!")
    
    elif query.data in ["recovered_yes", "recovered_no"]:
        recon = (query.data == "recovered_yes")
        context.user_data["recovered"] = recon
        date_str = datetime.now().strftime("%d.%m.%Y")
        log_daily_data(
            date_str,
            venlafaxine_morning=context.user_data.get("venlaf_morning", False),
            venlafaxine_evening=context.user_data.get("venlaf_evening", False),
            anaprilin_morning=context.user_data.get("anaprilin_morning", False),
            anaprilin_evening=context.user_data.get("anaprilin_evening", False),
            hormon=context.user_data.get("hormon", False),
            iron=context.user_data.get("iron", False),
            vitamins=context.user_data.get("vitamins", False),
            headache=True,
            painkiller=True,
            recovered=recon
        )
        await query.edit_message_text("✅ Всё записано за сегодня!")

# ------------- Запуск -------------

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN_RW")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.run_polling()
