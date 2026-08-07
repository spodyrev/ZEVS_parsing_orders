#!/usr/bin/env python3
"""
Миграция: добавление поля deleted_at для корзины
"""

import sqlite3
from pathlib import Path

def migrate():
    # Путь к БД
    db_path = Path(__file__).parent / "orders.db"
    
    print(f"🔧 Миграция базы данных: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли уже колонка
        cursor.execute("PRAGMA table_info(orders)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'deleted_at' in columns:
            print("✅ Колонка 'deleted_at' уже существует")
        else:
            # Добавляем колонку deleted_at
            cursor.execute("""
                ALTER TABLE orders 
                ADD COLUMN deleted_at TIMESTAMP NULL
            """)
            print("✅ Добавлена колонка 'deleted_at'")
        
        conn.commit()
        print("✅ Миграция успешно завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
