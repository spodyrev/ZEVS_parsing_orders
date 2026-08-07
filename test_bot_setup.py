#!/usr/bin/env python3
"""
Тестовый скрипт для проверки настройки Telegram бота

Проверяет:
1. Наличие необходимых зависимостей
2. Конфигурацию (.env файл и токен)
3. Доступность базы данных
4. Наличие трек-номеров для тестирования
5. Парсер трек-номеров
"""
import sys
from pathlib import Path

# Добавляем путь к backend
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """Проверка импортов"""
    print("1. Проверка зависимостей...")
    
    try:
        import telegram
        print("   ✅ python-telegram-bot установлен")
    except ImportError:
        print("   ❌ python-telegram-bot не найден")
        print("      Установите: pip install python-telegram-bot==20.8")
        return False
    
    try:
        import aiofiles
        print("   ✅ aiofiles установлен")
    except ImportError:
        print("   ❌ aiofiles не найден")
        print("      Установите: pip install aiofiles==23.2.1")
        return False
    
    try:
        from sqlalchemy import __version__
        print(f"   ✅ SQLAlchemy {__version__} установлен")
    except ImportError:
        print("   ❌ SQLAlchemy не найден")
        return False
    
    return True


def test_config():
    """Проверка конфигурации"""
    print("\n2. Проверка конфигурации...")
    
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        print("   ❌ Файл .env не найден")
        print("      Создайте: cp .env.example .env")
        return False
    
    print("   ✅ Файл .env существует")
    
    try:
        from telegram_bot.config import get_settings
        settings = get_settings()
        
        if not settings.telegram_bot_token or "your_bot_token_here" in settings.telegram_bot_token.lower():
            print("   ⚠️  TELEGRAM_BOT_TOKEN не настроен")
            print("      Добавьте токен от @BotFather в .env")
            return False
        
        print("   ✅ TELEGRAM_BOT_TOKEN настроен")
        print(f"      Токен начинается с: {settings.telegram_bot_token[:10]}...")
        
        photos_dir = settings.get_photos_path()
        if photos_dir.exists():
            print(f"   ✅ Директория для фото существует: {photos_dir}")
        else:
            print(f"   ⚠️  Директория для фото не найдена: {photos_dir}")
            print("      Создается автоматически при первом использовании")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при чтении конфигурации: {e}")
        return False


def test_database():
    """Проверка базы данных"""
    print("\n3. Проверка базы данных...")
    
    try:
        from database import SessionLocal
        from models import Order
        
        db = SessionLocal()
        
        # Проверяем подключение
        total_orders = db.query(Order).count()
        print(f"   ✅ База данных доступна")
        print(f"      Всего заказов: {total_orders}")
        
        # Проверяем наличие трек-номеров
        orders_with_tracking = db.query(Order).filter(
            Order.tracking_number.isnot(None),
            Order.tracking_number != ""
        ).all()
        
        print(f"      Заказов с трек-номером: {len(orders_with_tracking)}")
        
        if orders_with_tracking:
            print("\n   📦 Примеры трек-номеров для тестирования:")
            for order in orders_with_tracking[:5]:
                status = "✅" if order.received_at_warehouse else "⏳"
                print(f"      {status} {order.tracking_number} (Заказ: {order.order_id})")
        else:
            print("   ⚠️  Трек-номера не найдены")
            print("      Запустите: python update_tracking_numbers.py")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка при работе с БД: {e}")
        return False


def test_parser():
    """Проверка парсера трек-номеров"""
    print("\n4. Проверка парсера трек-номеров...")
    
    try:
        from telegram_bot.tracking_parser import TrackingNumberParser
        
        test_cases = [
            ("79023797293946", "79023797293946"),
            ("Получен товар 79023797293946", "79023797293946"),
            ("LP123456789CN", "LP123456789CN"),
            ("SF1234567890123", "SF1234567890123"),
            ("Трек: EA987654321CN номер", "EA987654321CN"),
        ]
        
        all_passed = True
        for text, expected in test_cases:
            result = TrackingNumberParser.extract_first_tracking_number(text)
            if result == expected:
                print(f"   ✅ '{text[:30]}...' → {result}")
            else:
                print(f"   ❌ '{text[:30]}...' → ожидалось {expected}, получено {result}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"   ❌ Ошибка в парсере: {e}")
        return False


def test_handlers():
    """Проверка импортов обработчиков"""
    print("\n5. Проверка обработчиков...")
    
    try:
        from telegram_bot.handlers import photo_handler, text_handler, start_command
        print("   ✅ Обработчики импортированы успешно")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка при импорте обработчиков: {e}")
        return False


def main():
    """Основная функция"""
    print("=" * 60)
    print("🧪 Тест настройки Telegram бота")
    print("=" * 60)
    
    results = []
    
    results.append(("Зависимости", test_imports()))
    results.append(("Конфигурация", test_config()))
    results.append(("База данных", test_database()))
    results.append(("Парсер", test_parser()))
    results.append(("Обработчики", test_handlers()))
    
    print("\n" + "=" * 60)
    print("📊 Результаты тестирования:")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:20s} {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 Все тесты пройдены! Бот готов к запуску.")
        print("\nЗапустите бота:")
        print("  python start_telegram_bot.py")
    else:
        print("\n⚠️  Некоторые тесты не прошли. Исправьте ошибки перед запуском.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
