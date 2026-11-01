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
MY_TG_USERNAME = "starygnom"  # замени на свой рабочий TG-юзернейм (без @)

# Брендинг
BRAND = "kvinsky"
BRAND_LINE = "✂️ kvinsky · качественный монтаж"

# Категории услуг: кнопка -> (mini-меню с ценами)
SERVICES = {
    "🎬 Рилсы": {
        "Рилс до 60 сек": "800 ₽ · срок 1-2 дня",
        "Рилс с анимацией": "1200 ₽ · срок 2 дня",
        "Пакет 3 рилса": "3000 ₽ · срок 3-4 дня",
    },
    "🌀 Эдиты": {
        "Эдит (базовый)": "500 ₽ · срок 1-2 дня",
        "Эдит под трек": "1500 ₽ · срок 2-3 дня",
        "Эдит с Flow-анимациями": "2000 ₽ · срок 3 дня",
        "Полный эдит под ключ": "3000 ₽ · срок 4-5 дней",
    },
    "📦 Пакеты и коллаб": {
        "Стартовый (5 рилсов)": "6000 ₽ · срок 5-7 дней",
        "Карьерный (10 рилсов)": "10000 ₽ · 10-12 дней",
        "Месячный монтаж (8 рилсов)": "10000 ₽ · месяц",
        "Коллаб / работа со стримером": "по договорённости",
    },
    "🎥 Другое": {
        "Обложка для стрима": "1000 ₽ · 1 день",
        "Интро / заставка": "800 ₽ · 1-2 дня",
        "Клип для TikTok из поста": "700 ₽ · 1-2 дня",
        "Другое (обсудим)": "по договорённости",
    },
}

WELCOME_TEXT = (
    "⚡️ *KVINSKY* ⚡️\n"
    "Качественный монтаж, который выглядит дорого и бьёт в топ.\n\n"
    "🎬 Рилсы и shorts\n"
    "🌀 Эдиты под трек\n"
    "📦 Пакеты и коллабы\n"
    "🎥 Обложки, интро и другое\n\n"
    "👇 Нажми на категорию — посмотри цены и оставь заявку. "
    "Отвечаю быстро и беру в работу!"
)

CATEGORY_TEXT = "📋 Выбери услугу:\n\n_Жми на неё — и я приму заявку._"

NOTICE_NEW_ORDER = "📥 НОВЫЙ ЗАКАЗ"
NOTICE_NEW_TASK = "✍️ ТЗ ОТ КЛИЕНТА"

# ========================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def brand_keyboard():
    """Главное меню."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📖 Портфолио", url=PORTFOLIO_URL)],
            [InlineKeyboardButton("🎬 Рилсы", callback_data="cat:🎬 Рилсы"),
             InlineKeyboardButton("🌀 Эдиты", callback_data="cat:🌀 Эдиты")],
            [InlineKeyboardButton("📦 Пакеты", callback_data="cat:📦 Пакеты и коллаб"),
             InlineKeyboardButton("🎥 Другое", callback_data="cat:🎥 Другое")],
            [InlineKeyboardButton("✉️ Связаться", url=f"https://t.me/{MY_TG_USERNAME}")],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT, reply_markup=brand_keyboard()
    )
    _hint(update, context)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Главное меню:", reply_markup=brand_keyboard()
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # === Выбрана категория ===
    if data.startswith("cat:"):
        cat = data[4:]
        items = SERVICES.get(cat, {})
        kb = [
            [InlineKeyboardButton(name, callback_data=f"serv:{cat}|{name}")]
            for name in items
        ]
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_menu")])
        await query.edit_message_text(
            f"*{cat}*\n\n{CATEGORY_TEXT}",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="Markdown",
        )
        return

    # === Выбрана услуга — спрашиваем ТЗ ===
    if data.startswith("serv:"):
        parts = data.split("|")
        cat = parts[1]
        name = parts[2]
        price = SERVICES.get(cat, {}).get(name, "")
        context.user_data["pending_order"] = {"cat": cat, "name": name, "price": price}
        cancel_kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_menu")]]
        )
        await query.edit_message_text(
            f"✅ Ты выбрал: *{name}*\n💰 {price}\n\n"
            f"Теперь напиши сюда описание задачи — что нужно сделать, "
            f"о проекте и референсы. Я прочитаю и вернусь!",
            parse_mode="Markdown",
            reply_markup=cancel_kb,
        )
        return

    # === Назад в главное меню ===
    if data == "back_menu":
        await query.edit_message_text(
            "Главное меню:", reply_markup=brand_keyboard()
        )
        return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = user.username or "нет ника"
    text = update.message.text[:1500]

    pending = context.user_data.get("pending_order")

    if pending:
        # Есть выбранная услуга — финальная заявка
        notice = (
            f"{NOTICE_NEW_ORDER}\n"
            f"──────────────\n"
            f"Услуга: {pending['name']}\n"
            f"{pending['price']}\n"
            f"──────────────\n"
            f"От: @{username} (id {user.id})\n\n"
            f"ТЗ:\n{text}"
        )
        _send_to_owner(context, notice)

        context.user_data.pop("pending_order", None)
        await update.message.reply_text(
            "🎉 *Заявка у меня!*\n\n"
            "Я уже вижу её и скоро свяжусь с тобой. "
            "Обычно отвечаю в течение пары часов.\n\n"
            f"{BRAND_LINE}",
            parse_mode="Markdown",
            reply_markup=brand_keyboard(),
        )
    else:
        # Просто сообщение без услуги
        await update.message.reply_text(
            "Я принимаю заявки на монтаж! 🎬\n\n"
            "Чтобы заказать — жми кнопку ниже и выбери услугу.\n\n"
            f"{BRAND_LINE}",
            reply_markup=brand_keyboard(),
        )


def _send_to_owner(context: ContextTypes.DEFAULT_TYPE, text: str):
    if not YOUR_TELEGRAM_ID:
        return
    try:
        context.application.create_task(
            context.bot.send_message(chat_id=YOUR_TELEGRAM_ID, text=text)
        )
    except Exception as e:
        logger.warning(f"Не удалось отправить владельцу: {e}")


def _hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Небольшая подсказка владельцу, что кто-то запустил."""
    if not YOUR_TELEGRAM_ID:
        return
    user = update.message.from_user
    try:
        context.application.create_task(
            context.bot.send_message(
                chat_id=YOUR_TELEGRAM_ID,
                text=f"👋 Кто-то открыл бота: @{user.username or 'без ника'} (id {user.id})",
            )
        )
    except Exception:
        pass


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    # Слушаем HTTP-порт, который задаёт Render (env PORT),
    # чтобы бесплатный сервис не засыпал в спящий режим.
    _start_web_server()

    print("Бот v2 запущен. Нажми Ctrl+C, чтобы остановить.")
    app.run_polling()


def _start_web_server():
    """Мини-HTTP-сервер, держит Render-сервис живым на порту PORT (default 10000)."""
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
