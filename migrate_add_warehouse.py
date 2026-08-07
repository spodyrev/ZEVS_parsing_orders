#!/usr/bin/env python3
"""
Миграция: добавление поля received_at_warehouse в таблицу orders
"""

import sys
import os

# Добавляем путь к backend для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from config import settings

def migrate():
    """Выполняет миграцию базы данных"""
    
    # Создаем подключение к БД
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Проверяем, существует ли уже колонка
        result = conn.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result]
        
        if 'received_at_warehouse' in columns:
            print("✅ Колонка 'received_at_warehouse' уже существует")
            return
        
        # Добавляем новую колонку
        print("📝 Добавляем колонку 'received_at_warehouse'...")
        conn.execute(text("""
            ALTER TABLE orders 
            ADD COLUMN received_at_warehouse INTEGER DEFAULT 0 NOT NULL
        """))
        conn.commit()
        
        print("✅ Миграция успешно выполнена!")
        print("   Добавлена колонка: received_at_warehouse (INTEGER, default=0)")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        sys.exit(1)
