import os
from dotenv import load_dotenv
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Start!"
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Unknown command: {update.message.text}",
    )


if __name__ == "__main__":
    load_dotenv()
    application = ApplicationBuilder().token(os.getenv("TOKEN", "")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling()
