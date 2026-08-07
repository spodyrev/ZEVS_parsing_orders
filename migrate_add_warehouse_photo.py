#!/usr/bin/env python3
"""
Миграция: добавление поля warehouse_photo_path для хранения пути к фото со склада
"""
import sys
from pathlib import Path

# Добавляем путь к backend
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from database import engine, SessionLocal
from models import Order

def migrate():
    """Добавить поле warehouse_photo_path"""
    
    print("🔄 Проверка необходимости миграции...")
    
    # Проверяем, существует ли уже поле
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result]
        
        if 'warehouse_photo_path' in columns:
            print("✅ Поле warehouse_photo_path уже существует, миграция не требуется")
            return
    
    print("📝 Добавление поля warehouse_photo_path...")
    
    # Добавляем новое поле
    with engine.connect() as conn:
        conn.execute(text(
            "ALTER TABLE orders ADD COLUMN warehouse_photo_path TEXT"
        ))
        conn.commit()
    
    print("✅ Миграция выполнена успешно!")
    
    # Проверяем результат
    db = SessionLocal()
    try:
        count = db.query(Order).count()
        print(f"📊 Заказов в базе: {count}")
        
        # Проверяем структуру
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(orders)"))
            print("\n📋 Структура таблицы orders:")
            for row in result:
                print(f"   {row[1]:30s} {row[2]:15s}")
    finally:
        db.close()

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        sys.exit(1)
