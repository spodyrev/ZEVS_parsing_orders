#!/usr/bin/env python3
"""
Скрипт для проверки, что происходит при синхронизации
"""

import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from loguru import logger
import requests
import json

logger.info("=" * 60)
logger.info("🔍 ДИАГНОСТИКА СИСТЕМЫ")
logger.info("=" * 60)

# 1. Проверка сервера
logger.info("\n1️⃣ Проверка веб-сервера...")
try:
    response = requests.get("http://localhost:8000", timeout=5)
    if response.status_code == 200:
        logger.info("✅ Сервер работает на http://localhost:8000")
    else:
        logger.warning(f"⚠️ Сервер вернул код: {response.status_code}")
except requests.exceptions.ConnectionError:
    logger.error("❌ Сервер не запущен!")
    logger.error("Запусти сервер командой: ./start.sh")
    sys.exit(1)
except Exception as e:
    logger.error(f"❌ Ошибка подключения: {e}")
    sys.exit(1)

# 2. Проверка API эндпоинтов
logger.info("\n2️⃣ Проверка API эндпоинтов...")
try:
    # Проверяем /api/orders
    response = requests.get("http://localhost:8000/api/orders", timeout=5)
    logger.info(f"  /api/orders: {response.status_code}")
    
    # Проверяем /api/stats
    response = requests.get("http://localhost:8000/api/stats", timeout=5)
    logger.info(f"  /api/stats: {response.status_code}")
    
    # Проверяем /api/scheduler/status
    response = requests.get("http://localhost:8000/api/scheduler/status", timeout=5)
    logger.info(f"  /api/scheduler/status: {response.status_code}")
    
    logger.info("✅ Все API эндпоинты доступны")
except Exception as e:
    logger.error(f"❌ Ошибка проверки API: {e}")

# 3. Проверка базы данных
logger.info("\n3️⃣ Проверка базы данных...")
try:
    from database import SessionLocal
    from models import Order
    
    db = SessionLocal()
    count = db.query(Order).count()
    logger.info(f"✅ База данных доступна")
    logger.info(f"  Заказов в базе: {count}")
    
    if count > 0:
        # Показываем последний заказ
        last_order = db.query(Order).order_by(Order.created_at.desc()).first()
        logger.info(f"  Последний заказ:")
        logger.info(f"    - ID: {last_order.order_id}")
        logger.info(f"    - Статус: {last_order.status}")
        logger.info(f"    - Цена: {last_order.total_price}")
        logger.info(f"    - Дата: {last_order.order_date}")
    
    db.close()
except Exception as e:
    logger.error(f"❌ Ошибка базы данных: {e}")

# 4. Проверка cookies
logger.info("\n4️⃣ Проверка cookies...")
try:
    from config import settings
    
    cookies_file = settings.taobao_cookies_file
    if os.path.exists(cookies_file):
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
        logger.info(f"✅ Файл cookies найден: {cookies_file}")
        logger.info(f"  Количество cookies: {len(cookies)}")
        
        # Проверяем важные cookies
        important_cookies = ['_tb_token_', 'cookie2', 't', '_m_h5_tk']
        found_cookies = [c['name'] for c in cookies if c['name'] in important_cookies]
        
        logger.info(f"  Важные cookies найдены: {', '.join(found_cookies)}")
        
        if len(found_cookies) < 3:
            logger.warning("⚠️ Некоторые важные cookies отсутствуют!")
            logger.warning("Возможно, нужно авторизоваться заново")
    else:
        logger.warning(f"⚠️ Файл cookies не найден: {cookies_file}")
        logger.warning("Нужно авторизоваться на Taobao")
except Exception as e:
    logger.error(f"❌ Ошибка проверки cookies: {e}")

# 5. Тест синхронизации
logger.info("\n5️⃣ Тестирование ручной синхронизации...")
try:
    logger.info("Отправка запроса на /api/sync...")
    response = requests.post("http://localhost:8000/api/sync", timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        logger.info("✅ Синхронизация завершена")
        logger.info(f"  Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        logger.error(f"❌ Ошибка синхронизации: {response.status_code}")
        logger.error(f"  Ответ: {response.text}")
except Exception as e:
    logger.error(f"❌ Ошибка тестирования синхронизации: {e}")
    import traceback
    logger.error(traceback.format_exc())

# 6. Проверка заказов после синхронизации
logger.info("\n6️⃣ Проверка заказов после синхронизации...")
try:
    response = requests.get("http://localhost:8000/api/orders", timeout=5)
    if response.status_code == 200:
        orders = response.json()
        logger.info(f"✅ Получено заказов: {len(orders)}")
        
        if len(orders) > 0:
            logger.info("\n📦 Примеры заказов:")
            for i, order in enumerate(orders[:3]):  # Показываем первые 3
                logger.info(f"\n  Заказ {i+1}:")
                logger.info(f"    - ID: {order['order_id']}")
                logger.info(f"    - Статус: {order['status']}")
                logger.info(f"    - Описание: {order['description'][:50]}...")
                logger.info(f"    - Цена: ¥{order['total_price']}")
        else:
            logger.warning("⚠️ Заказы не найдены после синхронизации")
            logger.warning("\nВозможные причины:")
            logger.warning("  1. Не авторизован на Taobao")
            logger.warning("  2. Нет заказов в аккаунте")
            logger.warning("  3. API вернул ошибку")
            logger.warning("  4. Неправильная структура API ответа")
except Exception as e:
    logger.error(f"❌ Ошибка получения заказов: {e}")

# Итоговый статус
logger.info("\n" + "=" * 60)
logger.info("📊 ИТОГОВЫЙ СТАТУС")
logger.info("=" * 60)

try:
    db = SessionLocal()
    order_count = db.query(Order).count()
    db.close()
    
    if order_count > 0:
        logger.info(f"✅ Система работает! В базе {order_count} заказов")
        logger.info("Открой http://localhost:8000 чтобы увидеть заказы")
    else:
        logger.warning("⚠️ Система запущена, но заказов нет")
        logger.warning("\nЧто делать:")
        logger.warning("  1. Открой HOW_TO_FIND_CORRECT_API.md")
        logger.warning("  2. Найди правильный API запрос в DevTools")
        logger.warning("  3. Убедись, что это queryboughtlistv2")
        logger.warning("  4. Проверь, что cookies актуальны")
except Exception as e:
    logger.error(f"❌ Ошибка проверки статуса: {e}")

logger.info("=" * 60)
