#!/usr/bin/env python3
"""
Инициализация базы данных
Создает таблицы если их нет
"""

import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from loguru import logger
from database import engine
from models import Base

logger.info("=" * 60)
logger.info("🗄️  ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
logger.info("=" * 60)

try:
    # Создаем все таблицы
    logger.info("\nСоздание таблиц...")
    Base.metadata.create_all(bind=engine)
    
    logger.info("✅ Таблицы созданы успешно!")
    
    # Проверяем какие таблицы есть
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    logger.info(f"\n📋 Созданные таблицы:")
    for table in tables:
        logger.info(f"   - {table}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ БАЗА ДАННЫХ ГОТОВА")
    logger.info("=" * 60)
    logger.info("\n📝 Теперь можешь запустить:")
    logger.info("   python3 test_sync.py")
    logger.info("\n" + "=" * 60)
    
except Exception as e:
    logger.error(f"\n❌ Ошибка инициализации: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
