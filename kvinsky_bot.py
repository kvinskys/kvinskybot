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

MY_TG_USERNAME = "starygnom"  # рабочий TG-юзернейм (без @)
AUTHOR_TG = f"t.me/{MY_TG_USERNAME}"

BRAND_LINE = "✂️ kvinsky · качественный монтаж"

# Обложка (кладём рядом с кодом)
COVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kvinsky-cover-3.jpg")

# ===== УСЛУГИ: категория -> список (название, цена) =====
CATEGORIES = {
    "🎬 Рилсы": [
        ("Рилс до 60 сек", "800 ₽ · 1-2 дня"),
        ("Рилс с анимацией", "1200 ₽ · 2 дня"),
        ("Пакет 3 рилса", "3000 ₽ · 3-4 дня"),
    ],
    "🌀 Эдиты": [
        ("Эдит", "600 ₽ · 1-2 дня"),
    ],
    "📦 Пакеты": [
        ("Пакет 5 рилсов", "6000 ₽ · 5-7 дней"),
        ("Карьерный (10 рилсов)", "10000 ₽ · 10-12 дней"),
    ],
    "🎥 Обложки и интро": [
        ("Обложка для стрима", "1000 ₽ · 1 день"),
        ("Интро / заставка", "800 ₽ · 1-2 дня"),
    ],
}

WELCOME_TEXT = (
    "⚡️ *KVINSKY* ⚡️ — качественный монтаж по ТЗ\n\n"
    "Выбери раздел, посмотри услуги и нажми «Купить» — "
    "сразу откроется мой ЛС с готовой заявкой. 👇"
)

CATEGORY_HINT = "Выбери услугу:"

# ========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def buy_link(service, price):
    """Ссылка на ЛС кинера с заранее заполненной заявкой."""
    text = "Привет, хочу заказать твой монтаж! " + service + " (" + price + ")"
    from urllib.parse import quote
    return f"https://{AUTHOR_TG}?text=" + quote(text)


def main_keyboard():
    """Главное меню: разделы-категории."""
    buttons = [
        [InlineKeyboardButton(name, callback_data="cat:" + name)]
        for name in CATEGORIES
    ]
    return InlineKeyboardMarkup(buttons)


def category_keyboard(cat):
    """Клавиатура услуг внутри категории: [Название] + [Купить]."""
    rows = []
    for service, price in CATEGORIES[cat]:
        rows.append([InlineKeyboardButton(
            f"{service} — {price}", callback_data="svc:" + service
        )])
        rows.append([InlineKeyboardButton(
            "🛒 Купить", url=buy_link(service, price)
        )])
    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_menu")])
    return InlineKeyboardMarkup(rows)


def service_text(cat, service, price):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🛒 Купить", url=buy_link(service, price))
    ], [
        InlineKeyboardButton("⬅️ Назад", callback_data="back_cat:" + cat)
    ]])
    msg = (
        f"🏷 *{service}*\n"
        f"💰 *{price}*\n\n"
        f"Нажми «Купить» — откроется мой ЛС с готовой заявкой "
        f"«Привет, хочу заказать твой монтаж!», останется только отправить."
    )
    return msg, kb


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # Обложка
    try:
        with open(COVER_PATH, "rb") as f:
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)
    except Exception as e:
        logger.warning(f"обложка: {e}")

    await update.message.reply_text(
        WELCOME_TEXT, parse_mode="Markdown", reply_markup=main_keyboard()
    )

    try:
        await context.bot.send_message(
            chat_id=YOUR_TELEGRAM_ID,
            text=f"👋 Кто-то открыл бота: @{user.username or 'без ника'} (id {user.id})",
        )
    except Exception as e:
        logger.warning(f"hint: {e}")


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Главное меню:", reply_markup=main_keyboard()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("cat:"):
        cat = data[4:]
        await q.edit_message_text(
            f"*{cat}*\n\n{CATEGORY_HINT}",
            parse_mode="Markdown",
            reply_markup=category_keyboard(cat),
        )

    elif data.startswith("svc:"):
        service = data[4:]
        for cat, items in CATEGORIES.items():
            for s, p in items:
                if s == service:
                    msg, kb = service_text(cat, s, p)
                    await q.edit_message_text(
                        msg, parse_mode="Markdown", reply_markup=kb
                    )
                    return

    elif data.startswith("back_cat:"):
        cat = data[9:]
        await q.edit_message_text(
            f"*{cat}*\n\n{CATEGORY_HINT}",
            parse_mode="Markdown",
            reply_markup=category_keyboard(cat),
        )

    elif data == "back_menu":
        await q.edit_message_text(
            "Главное меню:", reply_markup=main_keyboard()
        )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Я принимаю заказы на монтаж!\n\n"
        f"Выбери раздел кнопкой ниже 👇\n\n{BRAND_LINE}",
        reply_markup=main_keyboard(),
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, unknown)
    )

    _start_web_server()

    print("Бот v4 запущен. Нажми Ctrl+C, чтобы остановить.")
    app.run_polling()


def _start_web_server():
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
        logger.warning(f"HTTP keeper: {e}")


if __name__ == "__main__":
    main()
