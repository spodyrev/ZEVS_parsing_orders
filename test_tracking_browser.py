#!/usr/bin/env python3
"""
Тест получения трек-номера через браузер
"""

import sys
sys.path.append('backend')

from loguru import logger
from scraper.taobao_client import TaobaoClient

def test_tracking_browser():
    """Тестирует получение трек-номера через браузер"""
    
    logger.info("🧪 Тестирование получения трек-номера через браузер...")
    
    # Создаем клиента
    client = TaobaoClient()
    
    # ID заказа для теста
    test_order_id = "3316188865004009384"
    
    logger.info(f"Получаем трек-номер для заказа {test_order_id}...")
    
    try:
        # Получаем трек-номер через браузер
        tracking_number = client.get_tracking_number_browser(test_order_id)
        
        if tracking_number:
            logger.info("=" * 60)
            logger.info("✅ ТЕСТ ПРОЙДЕН")
            logger.info("=" * 60)
            logger.info(f"📦 Заказ: {test_order_id}")
            logger.info(f"📍 Трек-номер: {tracking_number}")
            logger.info("=" * 60)
            return True
        else:
            logger.error("=" * 60)
            logger.error("❌ ТЕСТ НЕ ПРОЙДЕН")
            logger.error("=" * 60)
            logger.error("Трек-номер не найден")
            logger.error("=" * 60)
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        # Закрываем браузер
        client.close()

if __name__ == "__main__":
    success = test_tracking_browser()
    sys.exit(0 if success else 1)
