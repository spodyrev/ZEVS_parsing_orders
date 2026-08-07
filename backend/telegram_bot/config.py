"""
Конфигурация Telegram бота
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class TelegramBotSettings(BaseSettings):
    """Настройки для Telegram бота"""
    
    telegram_bot_token: str
    warehouse_photos_dir: str = "warehouse_photos"
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def get_photos_path(self) -> Path:
        """Получить абсолютный путь к директории с фотографиями"""
        base_path = Path(__file__).parent.parent.parent
        return base_path / self.warehouse_photos_dir


def get_settings() -> TelegramBotSettings:
    """Получить настройки бота"""
    return TelegramBotSettings()
