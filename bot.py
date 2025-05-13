import asyncio
import logging
import datetime
from datetime import date, timedelta
import random

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN
from database import (
    init_user, add_run, get_user_stats, has_runs_this_week,
    get_week_range, users_db
)
from ranks import determine_rank, calculate_progress, CHALLENGES
from messages import (
    get_random_motivation, WELCOME_MESSAGE, HELP_MESSAGE,
    UNKNOWN_COMMAND_MESSAGE, RUN_SUCCESS_MESSAGE,
    RUN_SUCCESS_NEXT_RANK_MESSAGE, NO_STATS_MESSAGE,
    CHALLENGE_MESSAGE, WEEKLY_REPORT_MESSAGE
)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создаем основной роутер
router = Router()
dp.include_router(router)

# Определение состояний для FSM
class RunStates(StatesGroup):
    waiting_for_distance = State()

# Функция для создания основной клавиатуры
def get_main_keyboard():
    kb = [
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="🎯 Задания")
        ],
        [
            KeyboardButton(text="🏃‍♂️ Записать пробежку"),
            KeyboardButton(text="❓ Помощь")
        ]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    return keyboard

# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    logging.info(f"Получена команда /start от пользователя {message.from_user.id}")
    user_id = message.from_user.id
    init_user(user_id)
    
    welcome_text = WELCOME_MESSAGE.format(name=message.from_user.first_name)
    await message.answer(welcome_text, reply_markup=get_main_keyboard())
    logging.info(f"Отправлено приветственное сообщение пользователю {user_id}")

# Обработчик команды /run
@router.message(Command("run"))
async def cmd_run(message: Message) -> None:
    user_id = message.from_user.id
    
    # Разбор аргументов команды
    args = message.text.split()
    if len(args) != 2:
        await message.answer("⚠️ Пожалуйста, укажи дистанцию. Например: /run 5.2")
        return
    
    try:
        distance = float(args[1].replace(',', '.'))
        if distance <= 0:
            await message.answer("⚠️ Дистанция должна быть положительным числом!")
            return
    except ValueError:
        await message.answer("⚠️ Некорректный формат дистанции. Используй число, например: /run 5.2")
        return
    
    await process_run(message, user_id, distance)

# Функция обработки добавления пробежки
async def process_run(message: Message, user_id: int, distance: float) -> None:
    # Добавление пробежки и получение общей дистанции за неделю
    weekly_distance = add_run(user_id, distance)
    
    # Определение ранга
    rank = determine_rank(weekly_distance)
    
    # Создание ответного сообщения
    response = RUN_SUCCESS_MESSAGE.format(
        distance=distance,
        weekly_distance=weekly_distance,
        rank=rank
    )
    
    # Добавляем информацию о прогрессе к следующему рангу
    current_rank, next_rank, km_needed = calculate_progress(weekly_distance)
    if next_rank:
        response += RUN_SUCCESS_NEXT_RANK_MESSAGE.format(
            next_rank=next_rank,
            km_needed=km_needed
        )
    
    # Добавляем случайное мотивационное сообщение
    motivational_msg = get_random_motivation()
    response += f"\n💪 {motivational_msg}"
    
    await message.answer(response, reply_markup=get_main_keyboard())

# Отправка еженедельного отчета
async def send_weekly_report(user_id: int) -> None:
    stats = get_user_stats(user_id)
    
    if not stats["weekly_runs"]:
        return
    
    weekly_distance = stats["weekly_distance"]
    rank = determine_rank(weekly_distance)
    
    start_date, end_date = get_week_range()
    start_date_str = start_date.strftime('%d.%m')
    end_date_str = end_date.strftime('%d.%m')
    
    # Формирование детализации по дням
    details = ""
    for run_date, distance in sorted(stats["weekly_runs"].items()):
        date_obj = datetime.date.fromisoformat(run_date)
        details += f"• {date_obj.strftime('%d.%m')}: {distance:.1f} км\n"
    
    report = WEEKLY_REPORT_MESSAGE.format(
        start_date=start_date_str,
        end_date=end_date_str,
        weekly_distance=weekly_distance,
        rank=rank,
        details=details
    )
    
    try:
        await bot.send_message(user_id, report, reply_markup=get_main_keyboard())
    except Exception as e:
        logging.error(f"Failed to send weekly report to user {user_id}: {e}")

# Обработчик команды /stats
@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    user_id = message.from_user.id
    
    if not has_runs_this_week(user_id):
        await message.answer(NO_STATS_MESSAGE, reply_markup=get_main_keyboard())
        return
    
    stats = get_user_stats(user_id)
    weekly_distance = stats["weekly_distance"]
    total_distance = stats["total_distance"]
    rank = determine_rank(weekly_distance)
    
    start_date, end_date = get_week_range()
    
    response = (
        f"📊 Твоя статистика бега:\n\n"
        f"Текущая неделя ({start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')}):\n"
        f"🏃‍♂️ Пробежано за неделю: {weekly_distance:.1f} км\n"
        f"🏅 Текущий ранг: {rank}\n\n"
    )
    
    # Добавляем информацию о прогрессе к следующему рангу
    current_rank, next_rank, km_needed = calculate_progress(weekly_distance)
    if next_rank:
        response += f"До ранга \"{next_rank}\" осталось: {km_needed:.1f} км\n\n"
    
    # Детализация по дням
    response += "Пробежки по дням:\n"
    for run_date, distance in sorted(stats["weekly_runs"].items()):
        date_obj = datetime.date.fromisoformat(run_date)
        response += f"• {date_obj.strftime('%d.%m')}: {distance:.1f} км\n"
    
    response += f"\n🌟 Всего пробежано с момента регистрации: {total_distance:.1f} км"
    
    await message.answer(response, reply_markup=get_main_keyboard())

# Обработчик команды /challenge - дополнительные задания
@router.message(Command("challenge"))
async def cmd_challenge(message: Message) -> None:
    user_id = message.from_user.id
    init_user(user_id)
    
    stats = get_user_stats(user_id)
    weekly_distance = stats["weekly_distance"]
    rank = determine_rank(weekly_distance)
    
    user_challenges = CHALLENGES.get(rank, CHALLENGES["Падуан"])
    selected_challenge = random.choice(user_challenges)
    
    response = CHALLENGE_MESSAGE.format(
        rank=rank,
        challenge=selected_challenge
    )
    
    await message.answer(response, reply_markup=get_main_keyboard())

# Обработчик команды /help
@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_MESSAGE, reply_markup=get_main_keyboard())

# Обработчики для кнопок

# Обработчик кнопки "Статистика"
@router.message(lambda message: message.text == "📊 Статистика")
async def button_stats(message: Message) -> None:
    logging.info(f"Нажата кнопка 'Статистика' пользователем {message.from_user.id}")
    await cmd_stats(message)

# Обработчик кнопки "Задания"
@router.message(lambda message: message.text == "🎯 Задания")
async def button_challenge(message: Message) -> None:
    logging.info(f"Нажата кнопка 'Задания' пользователем {message.from_user.id}")
    await cmd_challenge(message)

# Обработчик кнопки "Помощь"
@router.message(lambda message: message.text == "❓ Помощь")
async def button_help(message: Message) -> None:
    logging.info(f"Нажата кнопка 'Помощь' пользователем {message.from_user.id}")
    await cmd_help(message)

# Обработчик кнопки "Записать пробежку"
@router.message(lambda message: message.text == "🏃‍♂️ Записать пробежку")
async def button_run(message: Message, state: FSMContext) -> None:
    logging.info(f"Нажата кнопка 'Записать пробежку' пользователем {message.from_user.id}")
    await state.set_state(RunStates.waiting_for_distance)
    await message.answer("💡 Введите дистанцию пробежки в километрах (например: 5.2):")

# Обработчик ввода дистанции после кнопки "Записать пробежку"
@router.message(StateFilter(RunStates.waiting_for_distance))
async def process_distance(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    
    try:
        distance = float(message.text.replace(',', '.'))
        if distance <= 0:
            await message.answer("⚠️ Дистанция должна быть положительным числом! Попробуйте еще раз:")
            return
        
        # Сбрасываем состояние
        await state.clear()
        
        # Обрабатываем пробежку
        await process_run(message, user_id, distance)
        
    except ValueError:
        await message.answer("⚠️ Некорректный формат дистанции. Используйте число, например: 5.2")

# Обработчик для неизвестных сообщений
@router.message()
async def unknown_message(message: Message) -> None:
    await message.answer(UNKNOWN_COMMAND_MESSAGE, reply_markup=get_main_keyboard())

# Запуск бота
async def main() -> None:
    logging.info("Запуск бота 'Беговая Империя'")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 