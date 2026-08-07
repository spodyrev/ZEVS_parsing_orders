#!/usr/bin/env python3
"""
Скрипт для обновления трек-номеров существующих заказов
Использует браузер (Playwright) для получения трек-номеров со страницы логистики
"""

import sys
import os
import time
from loguru import logger

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, init_db
from models import Order
from scraper.taobao_client import TaobaoClient
from scraper.parser import TaobaoParser


def update_tracking_numbers():
    """
    Обновляет трек-номера для всех заказов без трек-номера
    """
    logger.info("🚀 Запуск обновления трек-номеров...")
    
    # Инициализируем БД
    init_db()
    db = SessionLocal()
    
    try:
        # Находим все заказы без трек-номера
        orders_without_tracking = db.query(Order).filter(
            Order.tracking_number.is_(None)
        ).all()
        
        logger.info(f"Найдено {len(orders_without_tracking)} заказов без трек-номера")
        
        if not orders_without_tracking:
            logger.info("✅ Все заказы уже имеют трек-номера")
            return
        
        # Создаем клиент Taobao
        client = TaobaoClient()
        
        updated_count = 0
        failed_count = 0
        
        for idx, order in enumerate(orders_without_tracking, 1):
            logger.info(f"[{idx}/{len(orders_without_tracking)}] Обрабатываем заказ {order.order_id}...")
            
            try:
                # Получаем трек-номер через браузер
                tracking_number = client.get_tracking_number_browser(order.order_id)
                
                if tracking_number:
                    # Обновляем заказ
                    order.tracking_number = tracking_number
                    db.commit()
                    
                    logger.info(f"✅ Заказ {order.order_id}: трек-номер {tracking_number}")
                    updated_count += 1
                else:
                    logger.warning(f"⚠️  Заказ {order.order_id}: трек-номер не найден (товар еще не отправлен?)")
                    failed_count += 1
                
                # Пауза между запросами (чтобы не нагружать браузер)
                if idx < len(orders_without_tracking):
                    logger.debug("Пауза 2 секунды...")
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки заказа {order.order_id}: {e}")
                failed_count += 1
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ Обновлено: {updated_count}")
        logger.info(f"❌ Ошибок/не найдено: {failed_count}")
        logger.info(f"📊 Всего обработано: {len(orders_without_tracking)}")
        logger.info("=" * 60)
        
        # Закрываем браузер
        client.close()
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


if __name__ == "__main__":
    logger.add(
        "logs/update_tracking_{time}.log",
        rotation="10 MB",
        level="DEBUG"
    )
    
    update_tracking_numbers()
