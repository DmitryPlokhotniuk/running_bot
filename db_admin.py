import sqlite3
import argparse
import os
from datetime import datetime, timedelta, date

DB_PATH = 'running_bot.db'

def backup_database():
    """Создает резервную копию базы данных"""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: Файл базы данных {DB_PATH} не найден.")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backup_{timestamp}.db"
    
    try:
        # Копирование базы данных
        with open(DB_PATH, 'rb') as source:
            with open(backup_path, 'wb') as dest:
                dest.write(source.read())
        print(f"Резервная копия успешно создана: {backup_path}")
    except Exception as e:
        print(f"Ошибка при создании резервной копии: {e}")

def list_users():
    """Выводит список всех пользователей"""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: Файл базы данных {DB_PATH} не найден.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        SELECT user_id, username, current_week, total_distance, joined_date 
        FROM users 
        ORDER BY total_distance DESC
        """)
        users = cursor.fetchall()
        
        if not users:
            print("В базе данных нет пользователей.")
            return
        
        print("\nСписок пользователей:")
        print("-" * 90)
        print(f"{'ID':^10} | {'Имя':^15} | {'Текущая неделя':^15} | {'Всего км':^10} | {'Дата регистрации':^20}")
        print("-" * 90)
        
        for user in users:
            user_id, username, current_week, total_distance, joined_date = user
            # Используем дружественный формат имени
            username = username if username else f"Бегун #{user_id}"
            joined_date_formatted = datetime.fromisoformat(joined_date).strftime("%d.%m.%Y")
            print(f"{user_id:^10} | {username:^15} | {current_week:^15} | {total_distance:^10.1f} | {joined_date_formatted:^20}")
    
    except Exception as e:
        print(f"Ошибка при получении списка пользователей: {e}")
    finally:
        conn.close()

def user_stats(user_id):
    """Выводит детальную статистику по пользователю"""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: Файл базы данных {DB_PATH} не найден.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Получаем информацию о пользователе
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"Пользователь с ID {user_id} не найден.")
            return
        
        user_id, username, current_week, total_distance, joined_date = user
        # Используем дружественный формат имени
        username = username if username else f"Бегун #{user_id}"
        joined_date_formatted = datetime.fromisoformat(joined_date).strftime("%d.%m.%Y")
        
        print(f"\nСтатистика пользователя ID: {user_id}")
        print("-" * 50)
        print(f"Имя пользователя: {username}")
        print(f"Всего преодолено: {total_distance:.1f} км")
        print(f"Дата регистрации: {joined_date_formatted}")
        print(f"Текущая неделя: {current_week}")
        
        # Получаем пробежки пользователя
        cursor.execute("""
        SELECT run_date, SUM(distance) as total
        FROM runs 
        WHERE user_id = ? 
        GROUP BY run_date
        ORDER BY run_date DESC
        LIMIT 10
        """, (user_id,))
        
        runs = cursor.fetchall()
        
        if runs:
            print("\nПоследние 10 пробежек:")
            print("-" * 30)
            print(f"{'Дата':^15} | {'Дистанция (км)':^15}")
            print("-" * 30)
            
            for run in runs:
                run_date, distance = run
                date_formatted = datetime.fromisoformat(run_date).strftime("%d.%m.%Y")
                print(f"{date_formatted:^15} | {distance:^15.1f}")
        else:
            print("\nПользователь еще не записал ни одной пробежки.")
    
    except Exception as e:
        print(f"Ошибка при получении статистики пользователя: {e}")
    finally:
        conn.close()

def clear_user_runs(user_id):
    """Удаляет все пробежки пользователя"""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: Файл базы данных {DB_PATH} не найден.")
        return
    
    # Сначала создаем резервную копию
    backup_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            print(f"Пользователь с ID {user_id} не найден.")
            return
        
        # Получаем текущее общее расстояние
        cursor.execute("SELECT SUM(distance) FROM runs WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()[0] or 0
        
        # Удаляем все пробежки
        cursor.execute("DELETE FROM runs WHERE user_id = ?", (user_id,))
        
        # Обновляем общую дистанцию пользователя
        cursor.execute("UPDATE users SET total_distance = 0 WHERE user_id = ?", (user_id,))
        
        conn.commit()
        print(f"Все пробежки пользователя {user_id} удалены. Общее расстояние {total:.1f} км сброшено до 0.")
    
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении пробежек: {e}")
    finally:
        conn.close()

def delete_user(user_id):
    """Полностью удаляет пользователя из базы данных"""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: Файл базы данных {DB_PATH} не найден.")
        return
    
    # Сначала создаем резервную копию
    backup_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            print(f"Пользователь с ID {user_id} не найден.")
            return
        
        # Удаляем пробежки пользователя
        cursor.execute("DELETE FROM runs WHERE user_id = ?", (user_id,))
        
        # Удаляем пользователя
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        conn.commit()
        print(f"Пользователь {user_id} полностью удален из базы данных.")
    
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении пользователя: {e}")
    finally:
        conn.close()

def show_leaderboard():
    """Показывает таблицу лидеров"""
    if not os.path.exists(DB_PATH):
        print(f"Ошибка: Файл базы данных {DB_PATH} не найден.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Определяем начало и конец текущей недели
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Определяем начало и конец текущего месяца
        start_of_month = date(today.year, today.month, 1)
        if today.month == 12:
            next_month = date(today.year + 1, 1, 1)
        else:
            next_month = date(today.year, today.month + 1, 1)
        end_of_month = next_month - timedelta(days=1)
        
        # Получаем лидеров по неделе
        cursor.execute("""
            SELECT u.user_id, u.username, SUM(r.distance) as weekly_distance
            FROM users u
            JOIN runs r ON u.user_id = r.user_id
            WHERE r.run_date BETWEEN ? AND ?
            GROUP BY u.user_id, u.username
            ORDER BY weekly_distance DESC
            LIMIT 10
        """, (start_of_week.isoformat(), end_of_week.isoformat()))
        
        weekly_leaders = cursor.fetchall()
        
        print("\nТоп-10 бегунов за неделю:")
        print("-" * 50)
        print(f"{'№':^5} | {'Имя':^15} | {'Дистанция (км)':^15}")
        print("-" * 50)
        
        if weekly_leaders:
            for i, (user_id, username, distance) in enumerate(weekly_leaders, 1):
                # Используем дружественный формат имени
                username = username if username else f"Бегун #{user_id}"
                print(f"{i:^5} | {username:^15} | {distance:^15.1f}")
        else:
            print("Нет данных о пробежках за текущую неделю")
        
        # Получаем лидеров по месяцу
        cursor.execute("""
            SELECT u.user_id, u.username, SUM(r.distance) as monthly_distance
            FROM users u
            JOIN runs r ON u.user_id = r.user_id
            WHERE r.run_date BETWEEN ? AND ?
            GROUP BY u.user_id, u.username
            ORDER BY monthly_distance DESC
            LIMIT 10
        """, (start_of_month.isoformat(), end_of_month.isoformat()))
        
        monthly_leaders = cursor.fetchall()
        
        print("\nТоп-10 бегунов за месяц:")
        print("-" * 50)
        print(f"{'№':^5} | {'Имя':^15} | {'Дистанция (км)':^15}")
        print("-" * 50)
        
        if monthly_leaders:
            for i, (user_id, username, distance) in enumerate(monthly_leaders, 1):
                # Используем дружественный формат имени
                username = username if username else f"Бегун #{user_id}"
                print(f"{i:^5} | {username:^15} | {distance:^15.1f}")
        else:
            print("Нет данных о пробежках за текущий месяц")
    
    except Exception as e:
        print(f"Ошибка при получении таблицы лидеров: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Утилита администрирования базы данных бота для бега')
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда backup
    backup_parser = subparsers.add_parser('backup', help='Создать резервную копию базы данных')
    
    # Команда list
    list_parser = subparsers.add_parser('list', help='Показать список всех пользователей')
    
    # Команда stats
    stats_parser = subparsers.add_parser('stats', help='Показать статистику пользователя')
    stats_parser.add_argument('user_id', type=int, help='ID пользователя')
    
    # Команда clear
    clear_parser = subparsers.add_parser('clear', help='Удалить все пробежки пользователя')
    clear_parser.add_argument('user_id', type=int, help='ID пользователя')
    
    # Команда delete
    delete_parser = subparsers.add_parser('delete', help='Полностью удалить пользователя')
    delete_parser.add_argument('user_id', type=int, help='ID пользователя')
    
    # Команда leaderboard
    leaderboard_parser = subparsers.add_parser('leaderboard', help='Показать таблицу лидеров')
    
    args = parser.parse_args()
    
    if args.command == 'backup':
        backup_database()
    elif args.command == 'list':
        list_users()
    elif args.command == 'stats':
        user_stats(args.user_id)
    elif args.command == 'clear':
        clear_user_runs(args.user_id)
    elif args.command == 'delete':
        delete_user(args.user_id)
    elif args.command == 'leaderboard':
        show_leaderboard()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 