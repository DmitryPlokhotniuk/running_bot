import sqlite3

def view_database():
    conn = sqlite3.connect('running_bot.db')
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Таблицы в базе данных:")
    for table in tables:
        table_name = table[0]
        print(f"\nТаблица: {table_name}")
        
        # Получаем структуру таблицы
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("\nСтруктура:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Получаем данные таблицы
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        print("\nДанные:")
        if rows:
            for row in rows:
                print(f"  {row}")
        else:
            print("  Нет данных")
    
    conn.close()

if __name__ == "__main__":
    view_database() 