import os
from dotenv import load_dotenv
import logging
from datetime import date, datetime, timedelta
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
import inspect

AGE, MORNING_TIME, EVENING_TIME = range(3)
TOTAL_NUMBER_OF_WEEKS = 4680
TOTAL_NUMBER_OF_DAYS = TOTAL_NUMBER_OF_WEEKS * 7

# Callback data
(
    SELECT_SET_GOAL,
    SELECT_SKIP,
    SELECT_GOAL_COMPLETED,
    SELECT_GOAL_NOT_COMPLETED,
) = range(4)

SET_GOAL = 0

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

    day_goal = user_data.get("day_goal")
    day_goal_text = day_goal if day_goal else "Not set!"
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
        Day goal: {day_goal_text}
        Streak: {streak}"""
    )


async def send_morning_notification(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    assert context.user_data, "User data should not be None"
    job = context.job
    chat_id = job.chat_id
    keyboard = [
        [
            InlineKeyboardButton(
                "Set goal", callback_data=str(SELECT_SET_GOAL)
            ),
            InlineKeyboardButton("Skip", callback_data=str(SELECT_SKIP)),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id,
        text=get_status_message(context.user_data),
        reply_markup=reply_markup,
    )


async def send_evening_notification(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    job = context.job
    chat_id = job.chat_id
    day_goal = context.user_data.get("day_goal")
    if day_goal:
        pass
    else:
        pass


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

    chat_id = update.effective_message.chat_id
    time = datetime.strptime(update.message.text, "%H:%M").time()
    context.user_data["evening_time"] = time
    context.user_data["start_date"] = datetime.now().date()
    age = context.user_data["age"]
    context.user_data["start_week"] = age * 52
    context.user_data["start_day"] = age * 52 * 7

    # setup notifications
    # context.job_queue.run_daily(
    #     send_morning_notification,
    #     context.user_data["morning_time"],
    #     chat_id=chat_id,
    #     user_id=chat_id,
    #     name=str(chat_id),
    # )

    context.job_queue.run_daily(
        send_morning_notification,
        (datetime.utcnow() + timedelta(seconds=3)).time(),
        chat_id=chat_id,
        user_id=chat_id,
        name=str(chat_id),
    )

    context.job_queue.run_daily(
        send_evening_notification,
        time,
        chat_id=chat_id,
        user_id=chat_id,
        name=str(chat_id),
    )

    await update.message.reply_text("All set!")
    await update.message.reply_text(get_status_message(context.user_data))
    return ConversationHandler.END


async def cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Canceled!")
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Unknown command: {update.message.text}",
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assert context.user_data, "User data should not be None"
    await update.message.reply_text(get_status_message(context.user_data))


async def set_goal_selected(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="What is your day goal?",
    )
    return SET_GOAL


async def process_goal(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    goal = update.message.text
    context.user_data["day_goal"] = goal
    await update.message.reply_text(f"Day goal is set to: {goal}")
    return ConversationHandler.END


async def skip_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    context.user_data["day_goal"] = None
    context.user_data["streak"] = 0
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Skipping day goal!",
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

    morning_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                set_goal_selected, pattern="^" + str(SELECT_SET_GOAL) + "$"
            )
        ],
        states={
            SET_GOAL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    process_goal,
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(
        CallbackQueryHandler(
            skip_selected, pattern="^" + str(SELECT_SKIP) + "$"
        )
    )
    application.add_handler(conv_handler)
    application.add_handler(morning_conv_handler)
    application.add_handler(CommandHandler("status", status))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    application.run_polling()
