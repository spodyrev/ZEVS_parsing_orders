#!/usr/bin/env python3
"""
Скрипт для полной переустановки системы
Выполняет все шаги: очистка, авторизация, синхронизация, обновление трек-номеров
"""

import sys
import os
import time
import subprocess
from loguru import logger

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def step_1_clear_data():
    """Шаг 1: Очистка данных"""
    logger.info("=" * 60)
    logger.info("ШАГ 1: ОЧИСТКА ДАННЫХ")
    logger.info("=" * 60)
    
    files_to_delete = [
        "orders.db",  # ИСПРАВЛЕНО: база в корне проекта
        "taobao_cookies.json",
        "test_detail_response.json",
        "debug_logistics_page.png",
        "tracking_structure.json"
    ]
    
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"✅ Удален: {file_path}")
    
    logger.info("✅ Очистка завершена")
    logger.info("")

def step_2_init_db():
    """Шаг 2: Инициализация БД"""
    logger.info("=" * 60)
    logger.info("ШАГ 2: ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    logger.info("=" * 60)
    
    from database import init_db
    init_db()
    
    logger.info("✅ База данных инициализирована")
    logger.info("")

def step_3_auth():
    """Шаг 3: Авторизация"""
    logger.info("=" * 60)
    logger.info("ШАГ 3: АВТОРИЗАЦИЯ НА TAOBAO")
    logger.info("=" * 60)
    logger.info("")
    logger.info("⚠️  ВНИМАНИЕ!")
    logger.info("   Сейчас запустится скрипт авторизации.")
    logger.info("   Следуй инструкциям на экране.")
    logger.info("")
    
    import subprocess
    
    # Запускаем auth_taobao.py
    result = subprocess.run(
        [sys.executable, "auth_taobao.py"],
        cwd=os.path.dirname(__file__)
    )
    
    if result.returncode != 0:
        logger.error("❌ Авторизация не удалась")
        return False
    
    logger.info("✅ Авторизация успешна")
    logger.info("")
    return True

def step_4_sync_orders():
    """Шаг 4: Синхронизация заказов"""
    logger.info("=" * 60)
    logger.info("ШАГ 4: СИНХРОНИЗАЦИЯ ЗАКАЗОВ")
    logger.info("=" * 60)
    
    from scraper.taobao_client import TaobaoClient
    from database import SessionLocal
    from models import Order
    
    client = TaobaoClient()
    db = SessionLocal()
    
    try:
        # Получаем заказы
        logger.info("Получаем заказы с Taobao...")
        orders_data = client.get_orders()
        
        if not orders_data:
            logger.warning("⚠️  Заказы не найдены")
            return False
        
        logger.info(f"Найдено заказов: {len(orders_data)}")
        
        # Сохраняем в БД
        saved_count = 0
        for order_dict in orders_data:
            # Создаем объект Order из словаря
            order = Order(
                order_id=order_dict.get('order_id'),
                tracking_number=order_dict.get('tracking_number'),
                status=order_dict.get('status'),
                description=order_dict.get('description'),
                product_url=order_dict.get('product_url'),
                product_image_url=order_dict.get('product_image_url'),
                items_count=order_dict.get('items_count'),
                total_price=order_dict.get('total_price'),
                currency=order_dict.get('currency'),
                order_date=order_dict.get('order_date'),
                raw_data=order_dict.get('raw_data')
            )
            
            # Проверяем, есть ли уже такой заказ
            existing = db.query(Order).filter_by(order_id=order.order_id).first()
            
            if not existing:
                db.add(order)
                saved_count += 1
        
        db.commit()
        
        logger.info(f"✅ Синхронизация завершена! Сохранено новых заказов: {saved_count}")
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        client.close()
        db.close()

def step_5_update_tracking():
    """Шаг 5: Обновление трек-номеров"""
    logger.info("=" * 60)
    logger.info("ШАГ 5: ОБНОВЛЕНИЕ ТРЕК-НОМЕРОВ")
    logger.info("=" * 60)
    logger.info("")
    logger.info("⚠️  Это может занять несколько минут...")
    logger.info("")
    
    from scraper.taobao_client import TaobaoClient
    from database import SessionLocal
    from models import Order
    
    db = SessionLocal()
    client = TaobaoClient()
    
    try:
        # Находим заказы без трек-номера
        orders = db.query(Order).filter(Order.tracking_number.is_(None)).all()
        
        logger.info(f"Найдено {len(orders)} заказов без трек-номера")
        
        if not orders:
            logger.info("✅ Все заказы уже имеют трек-номера")
            return True
        
        updated = 0
        
        for idx, order in enumerate(orders, 1):
            logger.info(f"[{idx}/{len(orders)}] Обрабатываем {order.order_id}...")
            
            tracking = client.get_tracking_number_browser(order.order_id)
            
            if tracking:
                order.tracking_number = tracking
                db.commit()
                logger.info(f"  ✅ Трек-номер: {tracking}")
                updated += 1
            else:
                logger.info(f"  ⚠️  Трек-номер не найден")
            
            # Пауза между запросами
            if idx < len(orders):
                time.sleep(2)
        
        logger.info("")
        logger.info(f"✅ Обновлено трек-номеров: {updated}/{len(orders)}")
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления трек-номеров: {e}")
        return False
    finally:
        client.close()
        db.close()

def main():
    """Главная функция"""
    logger.info("")
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info("║       ПОЛНАЯ ПЕРЕУСТАНОВКА PARSING TAOBAO                  ║")
    logger.info("╚════════════════════════════════════════════════════════════╝")
    logger.info("")
    
    # Шаг 1: Очистка
    step_1_clear_data()
    
    # Шаг 2: Инициализация БД
    step_2_init_db()
    
    # Шаг 3: Авторизация
    if not step_3_auth():
        logger.error("Переустановка прервана")
        return
    
    # Шаг 4: Синхронизация
    if not step_4_sync_orders():
        logger.error("Переустановка прервана")
        return
    
    # Шаг 5: Обновление трек-номеров
    if not step_5_update_tracking():
        logger.warning("Трек-номера не обновлены, но можно продолжить")
    
    # Готово!
    logger.info("=" * 60)
    logger.info("✅ ПЕРЕУСТАНОВКА ЗАВЕРШЕНА!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📝 Теперь можешь запустить сервер:")
    logger.info("   ./start.sh")
    logger.info("")
    logger.info("   Или:")
    logger.info("   cd backend && python3 app.py")
    logger.info("")

if __name__ == "__main__":
    main()
