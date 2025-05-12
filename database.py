import datetime
import sqlite3
import os
from datetime import date, timedelta
from typing import Dict, List, Any, Tuple, Optional

# Путь к базе данных SQLite
DB_PATH = 'running_bot.db'

# Инициализация базы данных
def init_db() -> None:
    """
    Создает базу данных и таблицы, если они не существуют
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создаем таблицу пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        current_week INTEGER,
        total_distance REAL,
        joined_date TEXT
    )
    ''')
    
    # Создаем таблицу пробежек
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        run_date TEXT,
        distance REAL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Инициализируем базу данных при импорте модуля
init_db()

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем, существует ли пользователь
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        current_week = get_current_week()
        joined_date = datetime.date.today().isoformat()
        
        # Добавляем пользователя
        cursor.execute(
            "INSERT INTO users (user_id, current_week, total_distance, joined_date) VALUES (?, ?, ?, ?)",
            (user_id, current_week, 0, joined_date)
        )
        conn.commit()
    
    conn.close()

# Добавление новой пробежки
def add_run(user_id: int, distance: float) -> float:
    """
    Добавляет новую пробежку пользователя и возвращает общую дистанцию за неделю
    """
    init_user(user_id)
    current_week = get_current_week()
    current_date = datetime.date.today().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем текущую неделю пользователя
    cursor.execute("SELECT current_week FROM users WHERE user_id = ?", (user_id,))
    user_week = cursor.fetchone()[0]
    
    # Если неделя изменилась, обновляем неделю пользователя
    if user_week != current_week:
        cursor.execute("UPDATE users SET current_week = ? WHERE user_id = ?", (current_week, user_id))
    
    # Добавляем пробежку
    cursor.execute(
        "INSERT INTO runs (user_id, run_date, distance) VALUES (?, ?, ?)",
        (user_id, current_date, distance)
    )
    
    # Обновляем общую дистанцию пользователя
    cursor.execute(
        "UPDATE users SET total_distance = total_distance + ? WHERE user_id = ?",
        (distance, user_id)
    )
    
    conn.commit()
    
    # Получаем общую дистанцию за текущую неделю
    start_of_week, end_of_week = get_week_range()
    cursor.execute(
        "SELECT SUM(distance) FROM runs WHERE user_id = ? AND run_date BETWEEN ? AND ?",
        (user_id, start_of_week.isoformat(), end_of_week.isoformat())
    )
    weekly_distance = cursor.fetchone()[0] or 0
    
    conn.close()
    return weekly_distance

# Получение статистики пользователя
def get_user_stats(user_id: int) -> Dict[str, Any]:
    """
    Возвращает статистику пользователя
    """
    init_user(user_id)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем общую дистанцию и дату регистрации
    cursor.execute("SELECT total_distance, joined_date FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    total_distance = user_data[0]
    joined_date = user_data[1]
    
    # Получаем пробежки за текущую неделю
    start_of_week, end_of_week = get_week_range()
    cursor.execute(
        "SELECT run_date, distance FROM runs WHERE user_id = ? AND run_date BETWEEN ? AND ?",
        (user_id, start_of_week.isoformat(), end_of_week.isoformat())
    )
    runs_data = cursor.fetchall()
    
    weekly_runs = {}
    for run_date, distance in runs_data:
        if run_date in weekly_runs:
            weekly_runs[run_date] += distance
        else:
            weekly_runs[run_date] = distance
    
    weekly_distance = sum(weekly_runs.values())
    
    conn.close()
    
    return {
        "weekly_distance": weekly_distance,
        "total_distance": total_distance,
        "weekly_runs": weekly_runs,
        "joined_date": joined_date
    }

# Проверка, есть ли у пользователя пробежки на текущей неделе
def has_runs_this_week(user_id: int) -> bool:
    init_user(user_id)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    start_of_week, end_of_week = get_week_range()
    cursor.execute(
        "SELECT COUNT(*) FROM runs WHERE user_id = ? AND run_date BETWEEN ? AND ?",
        (user_id, start_of_week.isoformat(), end_of_week.isoformat())
    )
    count = cursor.fetchone()[0]
    
    conn.close()
    return count > 0

# Для совместимости с существующим кодом, поддерживаем переменную users_db
# Эта переменная будет использоваться только для чтения данных, 
# но все изменения будут выполняться через функции работы с БД
def get_users_db() -> Dict[int, Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем всех пользователей
    cursor.execute("SELECT user_id, current_week, total_distance, joined_date FROM users")
    users = cursor.fetchall()
    
    users_db = {}
    
    for user_id, current_week, total_distance, joined_date in users:
        # Получаем пробежки за текущую неделю
        start_of_week, end_of_week = get_week_range()
        cursor.execute(
            "SELECT run_date, distance FROM runs WHERE user_id = ? AND run_date BETWEEN ? AND ?",
            (user_id, start_of_week.isoformat(), end_of_week.isoformat())
        )
        runs_data = cursor.fetchall()
        
        weekly_runs = {}
        for run_date, distance in runs_data:
            if run_date in weekly_runs:
                weekly_runs[run_date] += distance
            else:
                weekly_runs[run_date] = distance
        
        users_db[user_id] = {
            "weekly_runs": weekly_runs,
            "current_week": current_week,
            "total_distance": total_distance,
            "joined_date": joined_date
        }
    
    conn.close()
    return users_db

# Создаем свойство users_db для получения текущего состояния базы данных
users_db = property(get_users_db) 