#!/usr/bin/env python3
"""
Быстрый тест подключения к Telegram боту
"""
import sys
import asyncio
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from telegram import Bot
from telegram_bot.config import get_settings

async def test_connection():
    """Проверить подключение к боту"""
    try:
        settings = get_settings()
        bot = Bot(token=settings.telegram_bot_token)
        
        print("🔄 Подключение к Telegram API...")
        me = await bot.get_me()
        
        print("✅ Подключение успешно!")
        print(f"   Имя бота: {me.first_name}")
        print(f"   Username: @{me.username}")
        print(f"   ID: {me.id}")
        print(f"   Ссылка: https://t.me/{me.username}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
