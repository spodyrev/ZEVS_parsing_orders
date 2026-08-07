#!/usr/bin/env python3
"""
Миграция: поддержка множественных фото для одного заказа
Конвертирует warehouse_photo_path из строки в JSON массив
"""
import sys
import json
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from database import engine, SessionLocal
from models import Order

def migrate():
    """Конвертировать warehouse_photo_path в JSON массив"""
    
    print("🔄 Миграция: поддержка множественных фото...")
    
    db = SessionLocal()
    try:
        # Получаем все заказы с фото
        orders = db.query(Order).filter(Order.warehouse_photo_path.isnot(None)).all()
        
        print(f"📊 Найдено заказов с фото: {len(orders)}")
        
        updated = 0
        for order in orders:
            # Если уже JSON массив - пропускаем
            if order.warehouse_photo_path.startswith('['):
                continue
            
            # Конвертируем строку в массив
            photo_path = order.warehouse_photo_path
            photo_array = [photo_path]
            order.warehouse_photo_path = json.dumps(photo_array)
            updated += 1
        
        db.commit()
        
        print(f"✅ Обновлено заказов: {updated}")
        print(f"📋 Пропущено (уже JSON): {len(orders) - updated}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        migrate()
        print("\n✅ Миграция завершена успешно!")
    except Exception as e:
        print(f"\n❌ Ошибка миграции: {e}")
        sys.exit(1)
