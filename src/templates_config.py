"""
Общая конфигурация шаблонов Jinja2 с кастомными фильтрами
"""
from fastapi.templating import Jinja2Templates
from datetime import datetime

# Русские названия дней недели
WEEKDAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def format_date_ru(date_obj):
    """Форматирует дату в формат: дд.мм.гггг день недели"""
    if not date_obj:
        return "-"
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except Exception:
            return str(date_obj)
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    weekday_name = WEEKDAYS_RU[date_obj.weekday()]
    return f"{date_obj.day:02d}.{date_obj.month:02d}.{date_obj.year} {weekday_name}"


# Создаём общий экземпляр шаблонов
templates = Jinja2Templates(directory="templates")
templates.env.filters["format_date_ru"] = format_date_ru
