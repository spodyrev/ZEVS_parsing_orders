#!/usr/bin/env python3
"""
Тестирование синхронизации заказов напрямую
Показывает детальные логи того, что происходит
"""

import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from loguru import logger
from scraper.taobao_client import TaobaoClient
from database import SessionLocal
from models import Order
import json

logger.info("=" * 70)
logger.info("🧪 ТЕСТИРОВАНИЕ СИНХРОНИЗАЦИИ ЗАКАЗОВ")
logger.info("=" * 70)

# 1. Проверка cookies
logger.info("\n1️⃣ Проверка cookies...")
cookies_file = 'taobao_cookies.json'

if not os.path.exists(cookies_file):
    logger.error(f"❌ Файл cookies не найден: {cookies_file}")
    logger.error("\nЗапусти сначала:")
    logger.error("  python3 auth_taobao.py")
    sys.exit(1)

try:
    with open(cookies_file, 'r') as f:
        cookies = json.load(f)
    
    logger.info(f"✅ Cookies файл найден")
    logger.info(f"   Количество cookies: {len(cookies)}")
    
    # Проверяем важные cookies
    cookie_names = [c['name'] for c in cookies]
    important = ['_m_h5_tk', '_tb_token_', 'cookie2', 't', 'unb']
    
    logger.info(f"\n🔑 Проверка важных cookies:")
    for name in important:
        if name in cookie_names:
            logger.info(f"   ✅ {name}")
        else:
            logger.warning(f"   ❌ {name} - ОТСУТСТВУЕТ!")
    
except Exception as e:
    logger.error(f"❌ Ошибка чтения cookies: {e}")
    sys.exit(1)

# 2. Проверка базы данных
logger.info("\n2️⃣ Проверка базы данных...")

# Инициализируем базу если нужно
from models import Base
from database import engine

try:
    # Пытаемся создать таблицы (если уже есть - ничего не произойдет)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ База данных инициализирована")
except Exception as e:
    logger.warning(f"⚠️ Предупреждение при инициализации: {e}")

db = SessionLocal()
try:
    count = db.query(Order).count()
    logger.info(f"✅ База данных доступна")
    logger.info(f"   Текущее количество заказов: {count}")
    
    if count > 0:
        logger.info(f"\n📦 Последние заказы в базе:")
        orders = db.query(Order).order_by(Order.created_at.desc()).limit(3).all()
        for i, order in enumerate(orders, 1):
            logger.info(f"\n   {i}. Order ID: {order.order_id}")
            logger.info(f"      Статус: {order.status}")
            logger.info(f"      Описание: {order.description[:50] if order.description else 'Нет'}...")
            logger.info(f"      Создан: {order.created_at}")
finally:
    db.close()

# 3. Тестирование API запроса
logger.info("\n3️⃣ Тестирование получения заказов через API...")
logger.info("   Создаем клиент...")

client = TaobaoClient()

logger.info("   Запрашиваем заказы...")
logger.info("")  # Пустая строка для разделения

try:
    orders = client.get_orders(page=1, page_size=20)
    
    logger.info("")  # Пустая строка после логов клиента
    logger.info("=" * 70)
    
    # Сохраняем response для анализа
    if hasattr(client, 'last_response'):
        with open('last_api_response.json', 'w', encoding='utf-8') as f:
            json.dump(client.last_response, f, indent=2, ensure_ascii=False)
        logger.info("💾 Ответ API сохранен в: last_api_response.json")
    
    if not orders:
        logger.error("\n❌ Заказы НЕ получены!")
        logger.error("\nВозможные причины:")
        logger.error("  1. API вернул ошибку - смотри логи выше")
        logger.error("  2. Cookies устарели - запусти: python3 auth_taobao.py")
        logger.error("  3. Неправильная подпись запроса")
        logger.error("  4. Нет заказов в аккаунте")
        
        logger.info("\n💡 Что делать:")
        logger.info("  1. Проверь логи выше - там должна быть причина")
        logger.info("  2. Если ошибка 'API вернул ошибку' - повтори авторизацию")
        logger.info("  3. Если 'подпись неверна' - также повтори авторизацию")
        
    else:
        logger.info(f"\n✅ Получено заказов: {len(orders)}")
        
        logger.info("\n📦 Примеры полученных заказов:")
        for i, order in enumerate(orders[:5], 1):
            logger.info(f"\n   {i}. Order ID: {order['order_id']}")
            logger.info(f"      Статус: {order['status']}")
            logger.info(f"      Описание: {order['description'][:80] if order['description'] else 'Нет'}...")
            logger.info(f"      Цена: ¥{order['total_price']}")
            logger.info(f"      Дата: {order['order_date']}")
        
        # 4. Сохранение в базу данных
        logger.info("\n4️⃣ Сохранение в базу данных...")
        
        db = SessionLocal()
        try:
            new_count = 0
            updated_count = 0
            
            for order_data in orders:
                # Проверяем существующий заказ
                existing = db.query(Order).filter(
                    Order.order_id == order_data['order_id']
                ).first()
                
                if existing:
                    # Обновляем
                    existing.tracking_number = order_data.get('tracking_number')
                    existing.status = order_data.get('status')
                    existing.description = order_data.get('description')
                    existing.total_price = order_data.get('total_price')
                    existing.raw_data = order_data.get('raw_data')
                    updated_count += 1
                else:
                    # Создаем новый
                    new_order = Order(
                        order_id=order_data['order_id'],
                        tracking_number=order_data.get('tracking_number'),
                        status=order_data.get('status', 'created'),
                        description=order_data.get('description', ''),
                        total_price=order_data.get('total_price', 0.0),
                        order_date=order_data.get('order_date'),
                        raw_data=order_data.get('raw_data', {})
                    )
                    db.add(new_order)
                    new_count += 1
            
            db.commit()
            
            logger.info(f"\n✅ Синхронизация завершена!")
            logger.info(f"   Новых заказов: {new_count}")
            logger.info(f"   Обновлено заказов: {updated_count}")
            
            # Проверяем итоговое количество
            total_count = db.query(Order).count()
            logger.info(f"   Всего заказов в базе: {total_count}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в базу: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            db.close()

except Exception as e:
    logger.error(f"\n❌ Ошибка получения заказов: {e}")
    import traceback
    logger.error(traceback.format_exc())

# Итог
logger.info("\n" + "=" * 70)
logger.info("📊 ИТОГОВЫЙ РЕЗУЛЬТАТ")
logger.info("=" * 70)

db = SessionLocal()
try:
    final_count = db.query(Order).count()
    
    if final_count > 0:
        logger.info(f"\n✅ В базе данных {final_count} заказов")
        logger.info("\n📝 Что делать дальше:")
        logger.info("   1. Открой http://localhost:8000")
        logger.info("   2. Обнови страницу (F5)")
        logger.info("   3. Заказы должны отображаться!")
        
        if final_count == count:
            logger.warning("\n⚠️ Количество заказов не изменилось")
            logger.warning("   Возможно, это те же тестовые заказы")
            logger.warning("   Запусти: python3 clear_database.py")
            logger.warning("   Затем повтори этот скрипт")
    else:
        logger.warning("\n⚠️ База данных пустая")
        logger.warning("   Синхронизация не прошла успешно")
        logger.warning("   Смотри логи выше для деталей")
        
finally:
    db.close()

logger.info("\n" + "=" * 70)
