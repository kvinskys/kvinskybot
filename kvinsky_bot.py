# kvinsky_bot.py — Telegram-бот для приёма заказов на монтаж
# Запуск: python kvinsky_bot.py
# Требует: pip install python-telegram-bot

# kvinsky_bot.py — Telegram-бот для приёма заказов на монтаж (v2)
# Запуск локально: python kvinsky_bot.py
# На Render: Start Command = python kvinsky_bot.py
import logging
import os
import threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "9159913958:AAEshD6brh51WXuvAcWAX4lfufeTlWh0njs"
YOUR_TELEGRAM_ID = 8895149828

PORTFOLIO_URL = "https://kvinskys.github.io/kvinsky/"
MY_TG_USERNAME = "starygnom"  # рабочий TG-юзернейм (без @)

BRAND_LINE = "✂️ kvinsky · качественный монтаж"
AUTHOR_TG = f"t.me/{MY_TG_USERNAME}"

# Путь к обложке (файл кладём рядом с ботом). Если нет — просто пропустим картинку.
COVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kvinsky-cover-2.jpg")

# Услуги: [название, цена+срок]
SERVICES = [
    ("🎬 Рилс до 60 сек", "800 ₽ · 1-2 дня"),
    ("🎬 Рилс с анимацией", "1200 ₽ · 2 дня"),
    ("🎬 Пакет 3 рилса", "3000 ₽ · 3-4 дня"),
    ("🌀 Эдит", "600 ₽ · 1-2 дня"),
    ("📦 Пакет 5 рилсов", "6000 ₽ · 5-7 дней"),
    ("📦 Карьерный (10 рилсов)", "10000 ₽ · 10-12 дней"),
    ("🎥 Обложка для стрима", "1000 ₽ · 1 день"),
    ("🎥 Интро / заставка", "800 ₽ · 1-2 дня"),
]

WELCOME_TEXT = (
    "⚡️ *KVINSKY* ⚡️\n"
    "Качественный монтаж, который выглядит дорого и бьёт в топ.\n\n"
    "Нажми на нужную услугу — и сразу откроется мой ЛС с уже готовым текстом заказа. "
    "Останется только отправить! 👇"
)

# ========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def order_link(service, price):
    """Ссылка на ЛС кинера с заранее заполненным текстом заказа."""
    text = f"Хочу заказать: {service} ({price}). Расскажи подробнее!"
    return f"https://{AUTHOR_TG}?text=" + text.replace(" ", "%20").replace("\n", "%0A")


def main_keyboard():
    """Каждая услуга — кнопка-ссылка на ЛС. Просто и надёжно."""
    buttons = [[InlineKeyboardButton(name, url=order_link(name, price))]
               for name, price in SERVICES]
    buttons.append([InlineKeyboardButton("📖 Портфолио", url=PORTFOLIO_URL)])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # Сначала обложка, затем приветственное меню
    try:
        with open(COVER_PATH, "rb") as f:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)
    except Exception as e:
        logger.warning(f"Обложка не отправлена: {e}")

    await update.message.reply_text(
        WELCOME_TEXT, parse_mode="Markdown", reply_markup=main_keyboard()
    )
    # уведомление владельцу
    try:
        await context.bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=f"👋 Кто-то открыл бота: @{user.username or 'без ника'} (id {user.id})",
        )
    except Exception as e:
        logger.warning(f"hint fail: {e}")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Выбери услугу 👇", reply_markup=main_keyboard()
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Я принимаю заказы на монтаж!\n\n"
        f"Выбери услугу кнопкой ниже или напиши мне напрямую — я быстро всё сделаю 👇\n\n"
        f"{BRAND_LINE}",
        reply_markup=main_keyboard(),
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, unknown)
    )

    _start_web_server()

    print("Бот v3 запущен. Нажми Ctrl+C, чтобы остановить.")
    app.run_polling()


def _start_web_server():
    """Мини-HTTP-сервер, держит Render живым на порту PORT (default 10000)."""
    try:
        from http.server import BaseHTTPRequestHandler, HTTPServer

        port = int(os.environ.get("PORT", "10000"))

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"kvinsky bot is running")

            def log_message(self, *a):
                pass

        httpd = HTTPServer(("0.0.0.0", port), Handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print(f"HTTP keeper listening on port {port}")
    except Exception as e:
        logger.warning(f"Не удалось запустить HTTP keeper: {e}")


if __name__ == "__main__":
    main()
