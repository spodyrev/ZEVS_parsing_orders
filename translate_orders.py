#!/usr/bin/env python3
"""
Скрипт для перевода описаний заказов с китайского на русский
Использует Google Gemini API или googletrans
"""

import sys
import os
from loguru import logger

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, init_db
from models import Order
from translator import Translator


def translate_orders(gemini_api_key: str = None):
    """
    Переводит описания всех заказов на русский язык
    
    Args:
        gemini_api_key: API ключ Google Gemini (опционально)
    """
    logger.info("=" * 60)
    logger.info("🌐 ПЕРЕВОД ОПИСАНИЙ ЗАКАЗОВ")
    logger.info("=" * 60)
    logger.info("")
    
    # Инициализируем БД
    init_db()
    db = SessionLocal()
    
    try:
        # Создаем переводчик
        translator = Translator(gemini_api_key)
        
        # Находим заказы без перевода
        orders = db.query(Order).filter(
            Order.translated_description.is_(None),
            Order.description.isnot(None)
        ).all()
        
        if not orders:
            logger.info("✅ Все заказы уже переведены!")
            return
        
        logger.info(f"Найдено {len(orders)} заказов для перевода")
        logger.info("")
        
        translated_count = 0
        failed_count = 0
        
        for idx, order in enumerate(orders, 1):
            logger.info(f"[{idx}/{len(orders)}] Заказ {order.order_id}")
            logger.info(f"  Оригинал: {order.description[:80]}...")
            
            try:
                # Переводим
                translated = translator.translate(order.description)
                
                if translated:
                    order.translated_description = translated
                    db.commit()
                    
                    logger.info(f"  ✅ Перевод: {translated[:80]}...")
                    translated_count += 1
                else:
                    logger.warning(f"  ⚠️  Не удалось перевести")
                    failed_count += 1
                
                logger.info("")
                
            except Exception as e:
                logger.error(f"  ❌ Ошибка: {e}")
                failed_count += 1
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ Переведено: {translated_count}")
        logger.info(f"❌ Ошибок: {failed_count}")
        logger.info(f"📊 Всего обработано: {len(orders)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close()


if __name__ == "__main__":
    # Проверяем API ключ
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_key:
        logger.warning("⚠️  GEMINI_API_KEY не найден в переменных окружения")
        logger.info("Будет использован googletrans (может быть менее точным)")
        logger.info("")
        logger.info("Чтобы использовать Gemini:")
        logger.info("  1. Получи бесплатный API ключ: https://makersuite.google.com/app/apikey")
        logger.info("  2. Добавь в .env: GEMINI_API_KEY=твой_ключ")
        logger.info("")
        
        response = input("Продолжить с googletrans? (y/n): ")
        if response.lower() != 'y':
            logger.info("Отменено")
            sys.exit(0)
    
    translate_orders(gemini_key)
