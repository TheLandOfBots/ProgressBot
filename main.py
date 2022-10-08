import os
from dotenv import load_dotenv
import logging
from datetime import date, datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
)
import inspect

AGE, MORNING_TIME, EVENING_TIME = range(3)
TOTAL_NUMBER_OF_WEEKS = 4680
TOTAL_NUMBER_OF_DAYS = TOTAL_NUMBER_OF_WEEKS * 7


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


def get_status_message(user_data: dict) -> str:
    try:
        start_date = user_data["start_date"]
        start_week = user_data["start_week"]
        start_day = user_data["start_day"]
    except KeyError:
        return "Missing information. Did you call /start?"

    day_goal = user_data.get("day_goal", "Not set!")
    streak = user_data.get("current_streak", 0)

    now = datetime.now().date()
    weeks = get_number_of_weeks_between(start_date, now)
    days = (now - start_date).days

    current_week = start_week + weeks
    current_week_pct = round((current_week / TOTAL_NUMBER_OF_WEEKS) * 100, 2)
    current_day = start_day + days
    current_day_pct = round((current_day / TOTAL_NUMBER_OF_DAYS) * 100, 2)

    return inspect.cleandoc(
        f"""Weeks: {current_week}/{TOTAL_NUMBER_OF_WEEKS} ({current_week_pct}%)
        Days: {current_day}/{TOTAL_NUMBER_OF_DAYS} ({current_day_pct}%)
        Day goal: {day_goal}
        Streak: {streak}"""
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("What's your age?")
    return AGE


async def process_age(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    age = int(update.message.text)
    context.user_data["age"] = age
    await update.message.reply_text(
        "What's your preferred time for a morning notification?"
    )

    return MORNING_TIME


async def process_morning_time(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    time = datetime.strptime(update.message.text, "%H:%M").time
    context.user_data["morning_time"] = time
    await update.message.reply_text(
        "What's your preferred time for an evening notification?"
    )
    return EVENING_TIME


async def process_evening_time(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    assert context.user_data, "User data should not be None"

    time = datetime.strptime(update.message.text, "%H:%M").time
    context.user_data["evening_time"] = time
    context.user_data["start_date"] = datetime.now().date()
    age = context.user_data["age"]
    context.user_data["start_week"] = age * 52
    context.user_data["start_day"] = age * 52 * 7

    await update.message.reply_text("All set!")
    await update.message.reply_text(get_status_message(context.user_data))
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
    assert context.user_data, "User data should not be None"
    await update.message.reply_text(get_status_message(context.user_data))


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
