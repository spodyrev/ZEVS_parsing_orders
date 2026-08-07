"""
Модуль для работы с авторизацией Taobao
Управление cookies и сессиями
"""

import json
import os
from typing import Optional, Dict
from datetime import datetime, timedelta
from loguru import logger


class TaobaoAuth:
    """
    Управление авторизацией на Taobao
    """
    
    def __init__(self, cookies_file: str = "cookies.json"):
        self.cookies_file = cookies_file
    
    def save_cookies(self, cookies: list) -> bool:
        """
        Сохраняет cookies в файл
        
        Args:
            cookies: Список cookies из браузера
            
        Returns:
            bool: True если успешно сохранено
        """
        try:
            # Добавляем метаданные
            data = {
                "saved_at": datetime.now().isoformat(),
                "cookies": cookies
            }
            
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cookies сохранены в {self.cookies_file}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения cookies: {e}")
            return False
    
    def load_cookies(self) -> Optional[list]:
        """
        Загружает cookies из файла
        
        Returns:
            list: Список cookies или None если файл не найден
        """
        if not os.path.exists(self.cookies_file):
            logger.warning(f"Файл cookies не найден: {self.cookies_file}")
            return None
        
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Проверяем возраст cookies
            saved_at = datetime.fromisoformat(data.get("saved_at", "2000-01-01"))
            age = datetime.now() - saved_at
            
            if age > timedelta(days=30):
                logger.warning(f"Cookies устарели (возраст: {age.days} дней)")
                return None
            
            logger.info("Cookies загружены успешно")
            return data.get("cookies", [])
            
        except Exception as e:
            logger.error(f"Ошибка загрузки cookies: {e}")
            return None
    
    def is_valid(self) -> bool:
        """
        Проверяет, есть ли валидные cookies
        
        Returns:
            bool: True если cookies существуют и не устарели
        """
        cookies = self.load_cookies()
        return cookies is not None and len(cookies) > 0
    
    def clear(self):
        """
        Удаляет сохраненные cookies
        """
        if os.path.exists(self.cookies_file):
            os.remove(self.cookies_file)
            logger.info("Cookies удалены")
    
    def get_session_info(self) -> Dict:
        """
        Получает информацию о сессии
        
        Returns:
            Dict: Информация о сессии
        """
        if not os.path.exists(self.cookies_file):
            return {
                "authenticated": False,
                "message": "Cookies не найдены"
            }
        
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            saved_at = datetime.fromisoformat(data.get("saved_at", "2000-01-01"))
            age = datetime.now() - saved_at
            
            return {
                "authenticated": True,
                "saved_at": saved_at.isoformat(),
                "age_days": age.days,
                "expires_soon": age.days > 25
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации о сессии: {e}")
            return {
                "authenticated": False,
                "message": f"Ошибка: {str(e)}"
            }


# Пример использования
if __name__ == "__main__":
    auth = TaobaoAuth()
    
    # Проверяем статус
    info = auth.get_session_info()
    print("Статус авторизации:", info)
    
    # Проверяем валидность
    if auth.is_valid():
        print("✅ Авторизация действительна")
    else:
        print("❌ Нужна повторная авторизация")
