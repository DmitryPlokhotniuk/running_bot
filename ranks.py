from typing import Dict, Tuple, Optional, List
import random
from db_utils import determine_rank_db, calculate_progress_db, get_challenges_for_rank

# Функция для определения ранга пользователя по километражу
def determine_rank(km: float) -> str:
    """
    Определяет ранг пользователя на основе километража за неделю.
    Использует данные из базы данных.
    """
    return determine_rank_db(km)

def calculate_progress(km: float) -> Tuple[str, Optional[str], Optional[float]]:
    """
    Рассчитывает прогресс до следующего ранга.
    Использует данные из базы данных.
    Возвращает: (текущий ранг, следующий ранг, км до следующего ранга)
    """
    return calculate_progress_db(km)

def get_challenges(rank: str) -> List[str]:
    """
    Получает список заданий для конкретного ранга из базы данных.
    """
    return get_challenges_for_rank(rank)

def get_random_challenge(rank: str) -> str:
    """
    Возвращает случайное задание для указанного ранга
    """
    challenges = get_challenges(rank)
    return random.choice(challenges)