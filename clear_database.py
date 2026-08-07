#!/usr/bin/env python3
"""
Очистка базы данных от тестовых заказов
"""

import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from loguru import logger
from database import SessionLocal
from models import Order

logger.info("=" * 60)
logger.info("🗑️  ОЧИСТКА БАЗЫ ДАННЫХ")
logger.info("=" * 60)

# Подключаемся к базе
db = SessionLocal()

try:
    # Считаем сколько заказов есть
    count = db.query(Order).count()
    
    if count == 0:
        logger.info("\n✅ База данных уже пустая")
    else:
        logger.info(f"\n📦 Найдено заказов в базе: {count}")
        
        # Показываем несколько примеров
        logger.info("\n📋 Примеры заказов:")
        orders = db.query(Order).limit(5).all()
        for i, order in enumerate(orders, 1):
            logger.info(f"\n  {i}. Order ID: {order.order_id}")
            logger.info(f"     Статус: {order.status}")
            logger.info(f"     Описание: {order.description[:50] if order.description else 'Нет'}...")
            logger.info(f"     Цена: ¥{order.total_price}")
            logger.info(f"     Создан: {order.created_at}")
        
        # Спрашиваем подтверждение
        logger.info("\n" + "=" * 60)
        response = input(f"\n⚠️  Удалить ВСЕ {count} заказов? (yes/no): ")
        
        if response.lower() == 'yes':
            # Удаляем все заказы
            deleted = db.query(Order).delete()
            db.commit()
            
            logger.info(f"\n✅ Удалено заказов: {deleted}")
            logger.info("База данных очищена")
        else:
            logger.info("\n❌ Отменено")
    
finally:
    db.close()

logger.info("\n" + "=" * 60)
logger.info("✅ ГОТОВО")
logger.info("=" * 60)
logger.info("\n📝 Следующие шаги:")
logger.info("   1. Убедись, что файл taobao_cookies.json существует")
logger.info("   2. Запусти сервер: ./start.sh")
logger.info("   3. Открой http://localhost:8000")
logger.info("   4. Нажми 'Синхронизировать заказы'")
logger.info("   5. Реальные заказы должны загрузиться!")
logger.info("\n" + "=" * 60)
