#!/usr/bin/env python3
"""
Миграция: Добавление поля is_superadmin в таблицу users

Это позволит назначать суперадминистраторов через админ-панель,
без необходимости запускать команды при каждом деплое.

Использование:
    python migrate_add_superadmin.py
"""

import sys
import os

# Добавляем путь к backend в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, engine, Base
from models import User
from sqlalchemy import text


def migrate():
    """Добавить поле is_superadmin в таблицу users"""
    print("\n🔧 МИГРАЦИЯ: Добавление поля is_superadmin")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Проверяем, существует ли уже колонка
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        if 'is_superadmin' in columns:
            print("✅ Колонка is_superadmin уже существует")
            
            # Показываем текущих суперадминов
            superadmins = db.query(User).filter(User.is_superadmin == 1).all()
            if superadmins:
                print(f"\n📋 Текущие суперадминистраторы ({len(superadmins)}):")
                for sa in superadmins:
                    print(f"   - {sa.first_name or 'Без имени'} {sa.last_name or ''} (ID: {sa.telegram_id})")
            else:
                print("\n⚠️  Суперадминистраторов еще нет!")
                print("   Используйте create_admin.py для создания первого суперадмина")
            
            return True
        
        print("📝 Добавление колонки is_superadmin...")
        
        # Добавляем новую колонку
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN is_superadmin INTEGER DEFAULT 0 NOT NULL
        """))
        
        print("✅ Колонка is_superadmin успешно добавлена")
        
        # Преобразуем существующих администраторов в суперадминов
        print("\n📝 Обновление существующих администраторов...")
        result = db.execute(text("""
            UPDATE users 
            SET is_superadmin = 1 
            WHERE is_admin = 1
        """))
        
        updated_count = result.rowcount
        
        db.commit()
        
        print(f"✅ Обновлено {updated_count} администраторов -> суперадминистраторов")
        
        print("\n" + "="*60)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("="*60)
        print()
        print("📝 Что изменилось:")
        print()
        print("1. Добавлено поле is_superadmin в таблицу users")
        print("2. Все существующие администраторы стали суперадминами")
        print()
        print("🎯 Теперь вы можете:")
        print()
        print("• Назначать суперадминов через админ-панель")
        print("• Назначать обычных администраторов (для управления пользователями)")
        print("• Добавлять обычных пользователей (для работы с системой)")
        print()
        print("🔐 Права доступа:")
        print()
        print("├─ Суперадминистратор (is_superadmin=1):")
        print("│  └─ Полный доступ к админ-панели")
        print("│  └─ Может назначать других суперадминов")
        print("│  └─ Может назначать администраторов")
        print("│  └─ Может добавлять/удалять пользователей")
        print("│")
        print("├─ Администратор (is_admin=1, is_superadmin=0):")
        print("│  └─ Доступ к админ-панели")
        print("│  └─ Может добавлять/удалять обычных пользователей")
        print("│  └─ НЕ может назначать администраторов")
        print("│")
        print("└─ Пользователь (is_admin=0):")
        print("   └─ Доступ только к системе заказов")
        print("   └─ Может пользоваться ботом")
        print()
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка миграции: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
