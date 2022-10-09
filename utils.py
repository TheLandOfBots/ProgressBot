from datetime import date, datetime, timedelta
import inspect


TOTAL_NUMBER_OF_WEEKS = 4680
TOTAL_NUMBER_OF_DAYS = TOTAL_NUMBER_OF_WEEKS * 7


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
    streak = user_data.get("streak", 0)

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
