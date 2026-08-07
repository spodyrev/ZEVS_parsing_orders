#!/usr/bin/env python3
"""
Скрипт для миграции базы данных
Добавляет поле translated_description в таблицу orders
"""

import sys
import os
from loguru import logger

# Добавляем backend в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, engine
from sqlalchemy import text


def migrate_add_translation_field():
    """
    Добавляет поле translated_description в таблицу orders
    """
    logger.info("=" * 60)
    logger.info("🔄 МИГРАЦИЯ БАЗЫ ДАННЫХ")
    logger.info("=" * 60)
    logger.info("")
    
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли уже поле
        result = db.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result]
        
        if 'translated_description' in columns:
            logger.info("✅ Поле translated_description уже существует")
            return True
        
        # Добавляем новое поле
        logger.info("Добавляем поле translated_description...")
        db.execute(text(
            "ALTER TABLE orders ADD COLUMN translated_description TEXT"
        ))
        db.commit()
        
        logger.info("✅ Поле translated_description добавлено")
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ МИГРАЦИЯ ЗАВЕРШЕНА")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = migrate_add_translation_field()
    sys.exit(0 if success else 1)
