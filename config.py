import os
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Проверка наличия токена
if not BOT_TOKEN:
    raise ValueError("Не указан токен бота! Укажите его в файле .env или в переменных окружения.") 