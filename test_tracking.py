#!/usr/bin/env python3
"""
Тестовый скрипт для проверки получения трек-номера
Использует order_id из JSON, который ты прислал
"""

import sys
import os
import json

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from scraper.taobao_client import TaobaoClient
from scraper.parser import TaobaoParser
from loguru import logger


def test_tracking():
    """
    Тестируем получение трек-номера для заказа 3316188865004009384
    """
    logger.info("🧪 Тестирование получения трек-номера...")
    
    # Создаем клиент
    client = TaobaoClient()
    
    # ID заказа из твоего JSON
    test_order_id = "3316188865004009384"
    
    logger.info(f"Получаем детали заказа {test_order_id}...")
    
    # Получаем детали
    detail_data = client.get_order_details(test_order_id)
    
    if not detail_data:
        logger.error("❌ Не удалось получить детали заказа")
        logger.error("Убедись, что файл taobao_cookies.json существует и содержит валидные cookies")
        return False
    
    # Сохраняем ответ для отладки
    with open('test_detail_response.json', 'w', encoding='utf-8') as f:
        json.dump(detail_data, f, ensure_ascii=False, indent=2)
    logger.info("Ответ API сохранен в test_detail_response.json")
    
    # Парсим трек-номер
    tracking_number = TaobaoParser.parse_tracking_from_detail(detail_data)
    
    if tracking_number:
        logger.info(f"✅ УСПЕХ! Трек-номер: {tracking_number}")
        
        # Проверяем, что это наш ожидаемый трек-номер
        expected = "79023797293946"
        if tracking_number == expected:
            logger.info(f"✅ Трек-номер совпадает с ожидаемым: {expected}")
        else:
            logger.warning(f"⚠️  Трек-номер не совпадает. Ожидали: {expected}, получили: {tracking_number}")
        
        return True
    else:
        logger.error("❌ Трек-номер не найден в ответе API")
        logger.error("Проверь файл test_detail_response.json")
        return False


if __name__ == "__main__":
    logger.add(
        "logs/test_tracking_{time}.log",
        rotation="10 MB",
        level="DEBUG"
    )
    
    success = test_tracking()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ТЕСТ ПРОЙДЕН!")
        print("=" * 60)
        print("\nТеперь можешь запустить:")
        print("  python3 update_tracking_numbers.py")
        print("\nДля обновления трек-номеров всех заказов в базе данных.")
    else:
        print("\n" + "=" * 60)
        print("❌ ТЕСТ НЕ ПРОЙДЕН")
        print("=" * 60)
        print("\nПроверь:")
        print("  1. Файл taobao_cookies.json существует")
        print("  2. Cookies актуальные (не истекли)")
        print("  3. Запусти python3 auth_taobao.py для повторной авторизации")
