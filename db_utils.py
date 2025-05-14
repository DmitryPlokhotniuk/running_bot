import sqlite3
from typing import Dict, List, Any, Tuple, Optional

# Путь к базе данных SQLite
DB_PATH = 'running_bot.db'

def determine_rank_db(km: float) -> str:
    """
    Определяет ранг пользователя на основе километража за неделю из базы данных
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM ranks 
        WHERE min_km <= ? AND max_km >= ?
        ORDER BY min_km DESC
        LIMIT 1
    """, (km, km))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    
    # Если не найдено подходящего ранга, возвращаем самый высокий
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM ranks ORDER BY max_km DESC LIMIT 1")
    highest_rank = cursor.fetchone()[0]
    conn.close()
    
    return highest_rank

def calculate_progress_db(km: float) -> Tuple[str, Optional[str], Optional[float]]:
    """
    Рассчитывает прогресс до следующего ранга из базы данных
    Возвращает: (текущий ранг, следующий ранг, км до следующего ранга)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Находим текущий ранг
    current_rank = determine_rank_db(km)
    
    # Находим следующий ранг (если он есть)
    cursor.execute("""
        SELECT r1.name, r1.min_km
        FROM ranks r1
        JOIN ranks r2 ON r1.min_km > r2.min_km
        WHERE r2.name = ?
        ORDER BY r1.min_km
        LIMIT 1
    """, (current_rank,))
    
    next_rank_data = cursor.fetchone()
    conn.close()
    
    if next_rank_data:
        next_rank, next_rank_min = next_rank_data
        km_needed = next_rank_min - km
        return current_rank, next_rank, km_needed
    
    return current_rank, None, None

def get_challenges_for_rank(rank: str) -> List[str]:
    """
    Получает список заданий для конкретного ранга из базы данных
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.challenge_text
        FROM challenges c
        JOIN ranks r ON c.rank_id = r.id
        WHERE r.name = ?
    """, (rank,))
    
    challenges = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    if not challenges:
        # Если для этого ранга нет заданий, возвращаем задания для самого низкого ранга
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.challenge_text
            FROM challenges c
            JOIN ranks r ON c.rank_id = r.id
            WHERE r.min_km = (SELECT MIN(min_km) FROM ranks)
        """)
        
        challenges = [row[0] for row in cursor.fetchall()]
        conn.close()
    
    return challenges

def get_random_motivation_db() -> str:
    """
    Возвращает случайное мотивационное сообщение из базы данных
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT message FROM motivational_messages
        ORDER BY RANDOM()
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    
    # Если таблица пуста, возвращаем дефолтное сообщение
    return "Продолжай двигаться вперед! Каждый шаг приближает тебя к цели." 