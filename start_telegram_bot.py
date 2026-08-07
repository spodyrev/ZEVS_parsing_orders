#!/usr/bin/env python3
"""
Скрипт запуска Telegram бота для отслеживания товаров на складе

Использование:
    python start_telegram_bot.py

Или с активированным venv:
    source venv/bin/activate
    python start_telegram_bot.py

Остановка:
    Ctrl+C
"""
import sys
import asyncio
from pathlib import Path

# Добавляем путь к backend в sys.path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from loguru import logger
from telegram_bot.bot import start_bot


def setup_logging():
    """Настроить логирование"""
    # Создаем директорию для логов если не существует
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Настраиваем логирование
    logger.remove()  # Удаляем стандартный handler
    
    # Консольный вывод с цветами
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )
    
    # Файловый лог
    logger.add(
        logs_dir / "telegram_bot_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )
    
    logger.info("Logging configured")


def check_env_file():
    """Проверить наличие .env файла и необходимых переменных"""
    env_file = Path(__file__).parent / ".env"
    
    if not env_file.exists():
        logger.error("❌ Файл .env не найден!")
        logger.info("Создайте файл .env на основе .env.example:")
        logger.info("  cp .env.example .env")
        logger.info("\nЗатем добавьте в него TELEGRAM_BOT_TOKEN:")
        logger.info("  TELEGRAM_BOT_TOKEN=your_bot_token_here")
        logger.info("\nПолучить токен можно у @BotFather в Telegram")
        sys.exit(1)
    
    # Проверяем наличие токена
    with open(env_file, 'r') as f:
        content = f.read()
        if 'TELEGRAM_BOT_TOKEN' not in content or 'your_bot_token_here' in content.lower():
            logger.warning("⚠️  TELEGRAM_BOT_TOKEN не настроен в .env файле")
            logger.info("Добавьте в .env:")
            logger.info("  TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather")
            logger.info("\nПолучить токен:")
            logger.info("  1. Найдите @BotFather в Telegram")
            logger.info("  2. Отправьте команду /newbot")
            logger.info("  3. Следуйте инструкциям")
            logger.info("  4. Скопируйте токен в .env файл")
            sys.exit(1)


def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🤖 Telegram Bot для отслеживания товаров на складе")
    print("=" * 60)
    print()
    
    # Настраиваем логирование
    setup_logging()
    
    # Проверяем конфигурацию
    logger.info("Checking configuration...")
    check_env_file()
    
    logger.info("Starting bot...")
    logger.info("Press Ctrl+C to stop")
    print()
    
    try:
        # Запускаем бота
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\n")
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
        print("\n✅ Бот остановлен")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")
        print("Проверьте логи в директории logs/")
        sys.exit(1)


if __name__ == "__main__":
    main()
