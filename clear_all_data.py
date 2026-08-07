#!/usr/bin/env python3
"""
Скрипт для полной очистки базы данных и cookies
"""

import os
import sys
from loguru import logger

def clear_all_data():
    """Удаляет все данные: БД, cookies, временные файлы"""
    
    logger.info("🧹 Начинаем полную очистку...")
    
    files_to_delete = [
        "orders.db",  # ИСПРАВЛЕНО: база в корне проекта, не в backend/
        "taobao_cookies.json",
        "test_detail_response.json",
        "debug_logistics_page.png",
        "tracking_structure.json"
    ]
    
    deleted_count = 0
    
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"✅ Удален: {file_path}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка удаления {file_path}: {e}")
        else:
            logger.debug(f"⏭️  Пропущен (не существует): {file_path}")
    
    logger.info("=" * 60)
    logger.info(f"✅ Очистка завершена! Удалено файлов: {deleted_count}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📝 Следующие шаги:")
    logger.info("   1. Запусти авторизацию: python3 auth_taobao.py")
    logger.info("   2. Синхронизируй заказы: curl -X POST http://localhost:8000/api/sync")
    logger.info("   3. Обновь трек-номера: python3 update_tracking_numbers.py")
    logger.info("   4. Или просто запусти сервер: ./start.sh")
    logger.info("")

if __name__ == "__main__":
    clear_all_data()
