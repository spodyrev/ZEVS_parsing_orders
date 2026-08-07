"""
Планировщик для автоматической синхронизации заказов
Использует APScheduler
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from datetime import datetime
from typing import Optional

from config import settings
from database import SessionLocal
from models import Order
from scraper.taobao_client import TaobaoClient
from scraper.parser import TaobaoParser


class OrderSyncScheduler:
    """
    Планировщик автоматической синхронизации заказов
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.client: Optional[TaobaoClient] = None
        self.last_sync: Optional[datetime] = None
        self.is_running = False
        
        logger.info("OrderSyncScheduler инициализирован")
    
    def start(self):
        """
        Запускает планировщик
        """
        if self.is_running:
            logger.warning("Планировщик уже запущен")
            return
        
        # Настраиваем задачу синхронизации
        self.scheduler.add_job(
            func=self.sync_orders,
            trigger=IntervalTrigger(hours=settings.sync_interval_hours),
            id='sync_orders_job',
            name='Синхронизация заказов с Taobao',
            replace_existing=True
        )
        
        # Настраиваем задачу автоочистки корзины (раз в день)
        self.scheduler.add_job(
            func=self.auto_clean_trash,
            trigger=IntervalTrigger(days=1),
            id='auto_clean_trash_job',
            name='Автоочистка корзины (30 дней)',
            replace_existing=True
        )
        
        # Запускаем планировщик
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            f"✅ Планировщик запущен. "
            f"Интервал синхронизации: {settings.sync_interval_hours} час(ов)"
        )
        logger.info("✅ Автоочистка корзины настроена (раз в день)")
        
        # Запускаем первую синхронизацию сразу
        logger.info("Запуск первой синхронизации...")
        self.sync_orders()
    
    def stop(self):
        """
        Останавливает планировщик
        """
        if not self.is_running:
            logger.warning("Планировщик не запущен")
            return
        
        self.scheduler.shutdown()
        self.is_running = False
        
        if self.client:
            self.client.close()
        
        logger.info("Планировщик остановлен")
    
    def sync_orders(self):
        """
        Синхронизирует заказы с Taobao
        Основная функция, которая вызывается по расписанию
        """
        logger.info("=" * 50)
        logger.info("🔄 Начало синхронизации заказов...")
        
        try:
            # Инициализируем клиента если нужно
            if not self.client:
                self.client = TaobaoClient()
            
            # Получаем заказы из Taobao (используя сохраненные cookies)
            # НЕ вызываем login() - он использует Playwright который нельзя в asyncio
            orders = self.client.get_orders()
            
            if not orders:
                logger.warning("⚠️ Заказы не получены")
                logger.warning("Возможные причины:")
                logger.warning("  1. Cookies не найдены - запусти: python3 auth_taobao.py")
                logger.warning("  2. Cookies устарели - повтори авторизацию")
                logger.warning("  3. Ошибка API - проверь логи выше")
                return
            
            logger.info(f"Получено {len(orders)} заказов от Taobao")
            
            # Сохраняем в базу данных
            db = SessionLocal()
            try:
                new_count = 0
                updated_count = 0
                
                for order_data in orders:
                    # Проверяем, есть ли уже такой заказ
                    existing_order = db.query(Order).filter(
                        Order.order_id == order_data["order_id"]
                    ).first()
                    
                    if existing_order:
                        # Обновляем существующий заказ
                        existing_order.tracking_number = order_data.get("tracking_number")
                        existing_order.status = order_data.get("status")
                        existing_order.description = order_data.get("description")
                        existing_order.total_price = order_data.get("total_price")
                        existing_order.raw_data = order_data.get("raw_data")
                        updated_count += 1
                        logger.debug(f"Обновлен заказ: {order_data['order_id']}")
                    else:
                        # Создаем новый заказ
                        new_order = Order(
                            order_id=order_data["order_id"],
                            tracking_number=order_data.get("tracking_number"),
                            status=order_data.get("status", "created"),
                            description=order_data.get("description", ""),
                            total_price=order_data.get("total_price", 0.0),
                            order_date=order_data.get("order_date"),
                            raw_data=order_data.get("raw_data", {})
                        )
                        db.add(new_order)
                        new_count += 1
                        logger.debug(f"Добавлен новый заказ: {order_data['order_id']}")
                
                db.commit()
                
                logger.info(
                    f"✅ Синхронизация завершена: "
                    f"новых заказов: {new_count}, "
                    f"обновлено: {updated_count}"
                )
                
            finally:
                db.close()
            
            self.last_sync = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации: {e}", exc_info=True)
        
        logger.info("=" * 50)
    
    def get_status(self) -> dict:
        """
        Возвращает статус планировщика
        
        Returns:
            dict: Информация о состоянии планировщика
        """
        return {
            "is_running": self.is_running,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "interval_hours": settings.sync_interval_hours,
            "next_run": self.scheduler.get_jobs()[0].next_run_time.isoformat() 
                       if self.scheduler.get_jobs() else None
        }
    
    def auto_clean_trash(self):
        """
        Автоматически удаляет заказы старше 30 дней из корзины
        """
        from datetime import timedelta
        from pathlib import Path
        import json as json_lib
        
        logger.info("==================================================")
        logger.info("🗑️ Начало автоочистки корзины...")
        
        db = SessionLocal()
        
        try:
            # Дата 30 дней назад
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Находим старые удалённые заказы
            orders = db.query(Order).filter(
                Order.deleted_at.isnot(None),
                Order.deleted_at < thirty_days_ago
            ).all()
            
            if not orders:
                logger.info("✅ Нет заказов для удаления (старше 30 дней)")
                return
            
            deleted_count = 0
            for order in orders:
                # Удаляем фотографии
                if order.warehouse_photo_path:
                    try:
                        if order.warehouse_photo_path.startswith('['):
                            photos = json_lib.loads(order.warehouse_photo_path)
                        else:
                            photos = [order.warehouse_photo_path]
                        
                        for photo_filename in photos:
                            photo_path = Path(__file__).parent.parent / "warehouse_photos" / photo_filename
                            if photo_path.exists():
                                photo_path.unlink()
                                logger.debug(f"   🗑️ Удалено фото: {photo_filename}")
                    except Exception as e:
                        logger.warning(f"   ⚠️ Ошибка при удалении фото: {e}")
                
                db.delete(order)
                deleted_count += 1
                logger.info(f"   🗑️ Удалён заказ: {order.order_id} (удалён {order.deleted_at.strftime('%d.%m.%Y')})")
            
            db.commit()
            
            logger.info(f"✅ Автоочистка завершена. Удалено заказов: {deleted_count}")
            logger.info("==================================================")
            
        except Exception as e:
            logger.error(f"❌ Ошибка автоочистки корзины: {e}")
            db.rollback()
        finally:
            db.close()


# Глобальный экземпляр планировщика
scheduler = OrderSyncScheduler()


# Пример использования
if __name__ == "__main__":
    import time
    
    print("Запуск планировщика...")
    scheduler.start()
    
    print("Статус:", scheduler.get_status())
    
    print("\nПланировщик работает. Нажми Ctrl+C для остановки...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка...")
        scheduler.stop()
        print("Готово!")
