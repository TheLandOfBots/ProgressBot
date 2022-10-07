import os
from dotenv import load_dotenv
import logging
from datetime import date, datetime, timedelta
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)

AGE, MORNING_TIME, EVENING_TIME = range(3)
TOTAL_NUMBER_OF_WEEKS = 4680


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def get_number_of_weeks_between(d1: date, d2: date) -> int:
    # count weeks between mondays
    monday1 = d1 - timedelta(days=d1.weekday())
    monday2 = d2 - timedelta(days=d2.weekday())
    return (monday2 - monday1).days // 7


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("What's your age?")
    return AGE


async def process_age(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    age = int(update.message.text)
    context.user_data["age"] = age
    await update.message.reply_text("Morning time")

    return MORNING_TIME


async def process_morning_time(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    time = datetime.strptime(update.message.text, "%H:%M").time
    context.user_data["morning_time"] = time
    await update.message.reply_text("Evening time")
    return EVENING_TIME


async def process_evening_time(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    time = datetime.strptime(update.message.text, "%H:%M").time
    context.user_data["evening_time"] = time
    context.user_data["start_date"] = datetime.now().date()
    age = context.user_data["age"]
    context.user_data["start_week"] = age * 52
    await update.message.reply_text("All set!")
    return ConversationHandler.END


async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Canceled! Start again by typing /start.")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Unknown command: {update.message.text}",
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_date = context.user_data["start_date"]
    start_week = context.user_data["start_week"]
    weeks = get_number_of_weeks_between(start_date, datetime.now().date())
    await update.message.reply_text(
        f"{start_week + weeks}/{TOTAL_NUMBER_OF_WEEKS}"
    )


if __name__ == "__main__":
    load_dotenv()
    application = ApplicationBuilder().token(os.getenv("TOKEN", "")).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],
        states={
            AGE: [
                MessageHandler(
                    filters.Regex("^[0-9]$|^[1-9][0-9]$"), process_age
                )
            ],
            MORNING_TIME: [
                MessageHandler(
                    filters.Regex("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"),
                    process_morning_time,
                )
            ],
            EVENING_TIME: [
                MessageHandler(
                    filters.Regex("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"),
                    process_evening_time,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling()
