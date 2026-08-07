#!/usr/bin/env python3
"""
Скрипт для создания администратора системы

Использование:
    python create_admin.py

Скрипт запросит Telegram ID и другие данные для создания первого администратора.
"""

import sys
import os

# Добавляем путь к backend в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal, init_db
from models import User
from datetime import datetime


def get_telegram_id_instructions():
    """Инструкции по получению Telegram ID"""
    print("\n" + "="*60)
    print("КАК ПОЛУЧИТЬ TELEGRAM ID:")
    print("="*60)
    print()
    print("1. Откройте Telegram и найдите бота: @userinfobot")
    print("2. Отправьте боту команду /start")
    print("3. Бот ответит вашим Telegram ID (числом)")
    print("4. Скопируйте этот ID и используйте ниже")
    print()
    print("="*60)
    print()


def create_admin_user():
    """Создать администратора"""
    print("\n🔧 СОЗДАНИЕ СУПЕРАДМИНИСТРАТОРА СИСТЕМЫ")
    print("="*60)
    
    # Инициализируем БД
    print("📦 Инициализация базы данных...")
    init_db()
    
    # Показываем инструкции
    get_telegram_id_instructions()
    
    # Получаем данные от пользователя
    try:
        telegram_id = input("Введите Telegram ID суперадминистратора: ").strip()
        
        if not telegram_id:
            print("❌ Telegram ID обязателен!")
            return False
        
        # Проверяем, не существует ли уже пользователь
        db = SessionLocal()
        existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if existing_user:
            print(f"\n⚠️  Пользователь с Telegram ID {telegram_id} уже существует!")
            print(f"   Имя: {existing_user.first_name} {existing_user.last_name or ''}")
            print(f"   Администратор: {'Да' if existing_user.is_admin else 'Нет'}")
            print(f"   Суперадминистратор: {'Да' if existing_user.is_superadmin else 'Нет'}")
            print(f"   Активен: {'Да' if existing_user.is_active else 'Нет'}")
            
            update = input("\nОбновить права суперадминистратора? (да/нет): ").strip().lower()
            
            if update in ['да', 'yes', 'y', 'д']:
                existing_user.is_admin = 1
                existing_user.is_superadmin = 1
                existing_user.is_active = 1
                db.commit()
                print("\n✅ Права суперадминистратора обновлены!")
                return True
            else:
                print("\n❌ Операция отменена")
                return False
        
        # Опциональные поля
        phone_number = input("Номер телефона (необязательно, Enter для пропуска): ").strip()
        first_name = input("Имя (необязательно, Enter для пропуска): ").strip()
        last_name = input("Фамилия (необязательно, Enter для пропуска): ").strip()
        
        # Создаем суперадминистратора
        admin = User(
            telegram_id=telegram_id,
            phone_number=phone_number if phone_number else None,
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None,
            is_admin=1,
            is_superadmin=1,
            is_active=1,
            created_at=datetime.now()
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n" + "="*60)
        print("✅ СУПЕРАДМИНИСТРАТОР УСПЕШНО СОЗДАН!")
        print("="*60)
        print(f"ID в БД: {admin.id}")
        print(f"Telegram ID: {admin.telegram_id}")
        print(f"Номер телефона: {admin.phone_number or 'не указан'}")
        print(f"Имя: {admin.first_name or 'не указано'} {admin.last_name or ''}")
        print(f"Администратор: Да")
        print(f"Суперадминистратор: Да")
        print(f"Активен: Да")
        print("="*60)
        print()
        print("📝 СЛЕДУЮЩИЕ ШАГИ:")
        print()
        print("1. Запустите веб-приложение:")
        print("   python backend/app.py")
        print()
        print("2. Откройте страницу логина:")
        print("   http://localhost:8000/login")
        print()
        print("3. Нажмите 'Login with Telegram' и авторизуйтесь")
        print()
        print("4. Вы попадете на главную страницу с заказами")
        print()
        print("5. Для управления пользователями перейдите:")
        print("   http://localhost:8000/admin")
        print()
        print("🎯 КАК СУПЕРАДМИНИСТРАТОР ВЫ МОЖЕТЕ:")
        print()
        print("• Добавлять обычных пользователей")
        print("• Назначать администраторов")
        print("• Назначать других суперадминистраторов")
        print("• Управлять всеми пользователями системы")
        print()
        print("="*60)
        
        db.close()
        return True
        
    except KeyboardInterrupt:
        print("\n\n❌ Операция прервана пользователем")
        return False
    except Exception as e:
        print(f"\n❌ Ошибка создания суперадминистратора: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def list_existing_users():
    """Показать существующих пользователей"""
    print("\n📋 СУЩЕСТВУЮЩИЕ ПОЛЬЗОВАТЕЛИ:")
    print("="*60)
    
    db = SessionLocal()
    users = db.query(User).all()
    
    if not users:
        print("Пользователей пока нет в системе.")
        print()
        return
    
    for user in users:
        print(f"\n{user.id}. {user.first_name or 'Без имени'} {user.last_name or ''}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Телефон: {user.phone_number or 'не указан'}")
        print(f"   Username: @{user.username or 'не указан'}")
        
        # Определяем роль
        if user.is_superadmin:
            role = 'Суперадминистратор'
        elif user.is_admin:
            role = 'Администратор'
        else:
            role = 'Пользователь'
        
        print(f"   Роль: {role}")
        print(f"   Статус: {'Активен' if user.is_active else 'Неактивен'}")
        print(f"   Создан: {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else 'н/д'}")
        if user.last_login:
            print(f"   Последний вход: {user.last_login.strftime('%d.%m.%Y %H:%M')}")
    
    print()
    print("="*60)
    db.close()


def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("🔐 УПРАВЛЕНИЕ СУПЕРАДМИНИСТРАТОРАМИ СИСТЕМЫ MYSYTE")
    print("="*60)
    print()
    print("1. Создать нового суперадминистратора")
    print("2. Показать существующих пользователей")
    print("3. Выход")
    print()
    
    try:
        choice = input("Выберите действие (1-3): ").strip()
        
        if choice == "1":
            create_admin_user()
        elif choice == "2":
            list_existing_users()
            print("\nНажмите Enter для выхода...")
            input()
        elif choice == "3":
            print("До свидания!")
        else:
            print("❌ Неверный выбор!")
            
    except KeyboardInterrupt:
        print("\n\nДо свидания!")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
