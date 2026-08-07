"""
Конфигурация приложения
Загружает настройки из .env файла
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # База данных (используем абсолютный путь от корня проекта)
    database_url: str = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'orders.db'))}"
    
    # Интервал синхронизации (в часах)
    sync_interval_hours: int = 2
    
    # Секретный ключ
    secret_key: str = "change-this-secret-key"
    
    # Настройки сервера
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Режим отладки
    debug: bool = True
    
    # Логирование
    log_level: str = "INFO"
    log_file: str = "app.log"
    
    # Файл с cookies Taobao
    taobao_cookies_file: Optional[str] = "taobao_cookies.json"
    
    # Google Gemini API ключ для переводов
    gemini_api_key: Optional[str] = None
    
    # Telegram Bot Token (для Login Widget и бота склада)
    telegram_bot_token: str = ""
    
    # CORS настройки (разрешенные домены)
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    
    class Config:
        # Загружать из .env файла (ищем в корне проекта)
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        env_file_encoding = "utf-8"
        extra = "ignore"  # Игнорировать дополнительные поля
        case_sensitive = False  # Нечувствительность к регистру переменных


# Создаем глобальный объект настроек
settings = Settings()
