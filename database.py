import datetime
from datetime import date, timedelta
from typing import Dict, List, Any, Tuple, Optional

# База данных пользователей (в памяти)
users_db: Dict[int, Dict[str, Any]] = {}

# Получение номера текущей недели
def get_current_week() -> int:
    return datetime.date.today().isocalendar()[1]

# Получение начала и конца текущей недели
def get_week_range() -> Tuple[date, date]:
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

# Инициализация пользователя в БД
def init_user(user_id: int) -> None:
    if user_id not in users_db:
        current_week = get_current_week()
        users_db[user_id] = {
            "weekly_runs": {},
            "current_week": current_week,
            "total_distance": 0,
            "joined_date": datetime.date.today().isoformat()
        }

# Добавление новой пробежки
def add_run(user_id: int, distance: float) -> float:
    """
    Добавляет новую пробежку пользователя и возвращает общую дистанцию за неделю
    """
    current_week = get_current_week()
    current_date = datetime.date.today().isoformat()
    
    # Проверка и инициализация пользователя
    init_user(user_id)
    
    # Проверка, не начинается ли новая неделя
    if users_db[user_id]["current_week"] != current_week:
        # Сброс данных на новую неделю
        users_db[user_id]["weekly_runs"] = {}
        users_db[user_id]["current_week"] = current_week
    
    # Добавляем сегодняшнюю пробежку
    if current_date in users_db[user_id]["weekly_runs"]:
        users_db[user_id]["weekly_runs"][current_date] += distance
    else:
        users_db[user_id]["weekly_runs"][current_date] = distance
    
    users_db[user_id]["total_distance"] += distance
    
    # Возвращаем общую дистанцию за неделю
    return sum(users_db[user_id]["weekly_runs"].values())

# Получение статистики пользователя
def get_user_stats(user_id: int) -> Dict[str, Any]:
    """
    Возвращает статистику пользователя
    """
    # Проверка и инициализация пользователя
    init_user(user_id)
    
    weekly_distance = sum(users_db[user_id]["weekly_runs"].values())
    total_distance = users_db[user_id]["total_distance"]
    
    return {
        "weekly_distance": weekly_distance,
        "total_distance": total_distance,
        "weekly_runs": users_db[user_id]["weekly_runs"],
        "joined_date": users_db[user_id]["joined_date"]
    }

# Проверка, есть ли у пользователя пробежки на текущей неделе
def has_runs_this_week(user_id: int) -> bool:
    # Проверка и инициализация пользователя
    init_user(user_id)
    
    return bool(users_db[user_id]["weekly_runs"]) 