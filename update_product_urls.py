#!/usr/bin/env python3
"""
Скрипт для обновления product_url и product_image_url
для существующих заказов в базе данных
"""

import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from loguru import logger
from database import SessionLocal
from models import Order

logger.info("=" * 60)
logger.info("🔄 ОБНОВЛЕНИЕ URL И ИЗОБРАЖЕНИЙ ТОВАРОВ")
logger.info("=" * 60)

db = SessionLocal()

try:
    # Получаем все заказы
    orders = db.query(Order).all()
    logger.info(f"\nНайдено {len(orders)} заказов в базе")
    
    updated_count = 0
    
    for order in orders:
        if not order.raw_data:
            logger.warning(f"Заказ {order.order_id}: нет raw_data")
            continue
        
        # Извлекаем данные из raw_data
        items = order.raw_data.get("items", [])
        if not items:
            logger.warning(f"Заказ {order.order_id}: нет items в raw_data")
            continue
        
        first_item = items[0]
        
        # Извлекаем URL товара
        item_url = first_item.get("itemUrl", "")
        if item_url:
            if item_url.startswith("//"):
                order.product_url = f"https:{item_url}"
            elif not item_url.startswith("http"):
                order.product_url = f"https://{item_url}"
            else:
                order.product_url = item_url
        
        # Извлекаем URL изображения
        pic_url = first_item.get("pic", "")
        if pic_url:
            if pic_url.startswith("//"):
                order.product_image_url = f"https:{pic_url}"
            elif not pic_url.startswith("http"):
                order.product_image_url = f"https://{pic_url}"
            else:
                order.product_image_url = pic_url
        
        if order.product_url or order.product_image_url:
            updated_count += 1
            logger.debug(f"Обновлен заказ {order.order_id}")
            if order.product_url:
                logger.debug(f"  URL: {order.product_url[:50]}...")
            if order.product_image_url:
                logger.debug(f"  Фото: {order.product_image_url[:50]}...")
    
    # Сохраняем изменения
    db.commit()
    
    logger.info(f"\n✅ Обновлено заказов: {updated_count}")
    logger.info("=" * 60)
    logger.info("\n📝 Теперь:")
    logger.info("   1. Обнови страницу в браузере (F5)")
    logger.info("   2. Ссылки и фотографии должны появиться!")
    logger.info("=" * 60)
    
except Exception as e:
    logger.error(f"\n❌ Ошибка: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
finally:
    db.close()
