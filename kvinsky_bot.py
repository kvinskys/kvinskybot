# kvinsky_bot.py — Telegram-бот для приёма заказов на монтаж
# Запуск: python kvinsky_bot.py
# Требует: pip install python-telegram-bot

import logging
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# ===== НАСТРОЙКИ (поменяй на свои) =====

# 1. Токен от @BotFather. Вставь между кавычками:
BOT_TOKEN = "9159913958:AAEshD6brh51WXuvAcWAX4lfufeTlWh0njs"

# 2. Твой настоящий Telegram ID — куда приходят уведомления о заказах.
#    Узнать свой ID: напиши @userinfobot, он покажет "Id: 123456789".
YOUR_TELEGRAM_ID = 8895149828 # замени 0 на свой ID, например 123456789

# 3. Прайс-лист (название кнопки -> то, что отправится тебе в заявке).
PRICE_ITEMS = {
    "Рилс (1 шт.)": "800 руб., срок 1-2 дня",
    "Эдит полный (1 шт.)": "1500 руб., срок 2-3 дня",
    "Пакет 5 рилсов": "6000 руб., срок 4-6 дней",
    "Обложка / интро для стрима": "1000 руб., срок 1 день",
}

WELCOME_TEXT = (
    "Приветик! Это бот kvinsky — закажи монтаж за пару кликов.\n\n"
    "Выбери услугу и я приму заявку. После этого напиши своё ТЗ "
    "(кратко опиши задачу), и я свяжусь с тобой в личку."
)

# ========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(name, callback_data=name)]
        for name in PRICE_ITEMS
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_TEXT, reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chosen = query.data
    price = PRICE_ITEMS.get(chosen, chosen)

    user = query.from_user
    username = user.username or "нет ника"
    user_id = user.id

    # Отправляем заявку тебе (в твою личку)
    text = (
        f"📥 НОВЫЙ ЗАКАЗ\n"
        f"Услуга: {chosen}\n"
        f"({price})\n"
        f"От: @{username} (id {user_id})\n"
        f"Telegram: t.me/{username}" if username != "нет ника" else
        f"От: @{username} (id {user_id}) — без юзернейма",
    )
    if YOUR_TELEGRAM_ID:
        try:
            await context.bot.send_message(
                chat_id=YOUR_TELEGRAM_ID, text=text[0]
            )
        except Exception as e:
            logger.warning(f"Не смог отправить тебе уведомление: {e}")

    # Подтверждаем клиенту
    await query.edit_message_text(
        f"✅ Заявка принята!\n\n"
        f"Ты выбрал: {chosen}\n({price})\n\n"
        f"Теперь напиши сюда краткое описание задачи — "
        f"я прочитаю и свяжусь с тобой."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Когда клиент прислал описание задачи — пересылаем тебе."""
    user = update.message.from_user
    username = user.username or "нет ника"
    order_text = update.message.text[:1500]

    if YOUR_TELEGRAM_ID:
        try:
            await context.bot.send_message(
                chat_id=YOUR_TELEGRAM_ID,
                text=(
                    f"✍️ ТЗ от клиента @{username} (id {user.id}):\n\n"
                    f"{order_text}"
                ),
            )
        except Exception as e:
            logger.warning(f"Не смог переслать ТЗ: {e}")

    await update.message.reply_text(
        "Принял твоё описание! 🙌\n"
        "Я написал себе в личку, скоро свяжусь с тобой тут или в Telegram."
    )


def main():
    if "ВСТАВЬ_СЮДА_ТОКЕН" in BOT_TOKEN:
        print("❌ Ты не вставил токен. Открой файл и замени BOT_TOKEN.")
        return
    if not YOUR_TELEGRAM_ID:
        print("❌ Ты не указал YOUR_TELEGRAM_ID. Замени 0 на свой Telegram ID.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    print("Бот запущен. Нажми Ctrl+C, чтобы остановить.")
    app.run_polling()


if __name__ == "__main__":
    main()