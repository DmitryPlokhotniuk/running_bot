import sqlite3
import sys

DB_PATH = 'running_bot.db'

def migrate_database():
    """Добавляет столбец username в таблицу users, если его нет"""
    print("Начинаю миграцию базы данных...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли столбец username
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'username' not in column_names:
            print("Добавляю столбец 'username' в таблицу 'users'...")
            cursor.execute("ALTER TABLE users ADD COLUMN username TEXT")
            conn.commit()
            print("Миграция успешно завершена!")
        else:
            print("Столбец 'username' уже существует в таблице 'users'.")
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при миграции базы данных: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    if migrate_database():
        print("База данных успешно обновлена.")
    else:
        print("Не удалось обновить базу данных.")
        sys.exit(1) 