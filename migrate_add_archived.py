#!/usr/bin/env python3
"""
Миграция: добавление поля archived
"""

import sys
import os
from loguru import logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
from sqlalchemy import text


def migrate_add_archived():
    """Добавляет поле archived в таблицу orders"""
    logger.info("=" * 60)
    logger.info("🔄 МИГРАЦИЯ: Добавление поля archived")
    logger.info("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Проверяем существование поля
        result = db.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result]
        
        if 'archived' in columns:
            logger.info("✅ Поле archived уже существует")
            return True
        
        # Добавляем поле
        logger.info("Добавляем поле archived...")
        db.execute(text(
            "ALTER TABLE orders ADD COLUMN archived INTEGER DEFAULT 0 NOT NULL"
        ))
        db.commit()
        
        logger.info("✅ Поле archived добавлено")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = migrate_add_archived()
    sys.exit(0 if success else 1)
