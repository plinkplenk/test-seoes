from datetime import datetime

WEEK_DAYS = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье",
}

date_format_out = "%d.%m.%Y"


def get_day_of_week(date_string):
    date = datetime.strptime(date_string, date_format_out)
    day_of_week = date.strftime("%A")
    return WEEK_DAYS[day_of_week]
