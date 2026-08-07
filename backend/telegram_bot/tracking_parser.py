"""
Парсинг трек-номеров из текста сообщений
"""
import re
from typing import Optional, List
from loguru import logger


class TrackingNumberParser:
    """Класс для извлечения трек-номеров из текста"""
    
    # Паттерны для различных типов трек-номеров
    PATTERNS = [
        # Стандартные числовые трек-номера (10-20 цифр)
        r'\b\d{10,20}\b',
        
        # China Post, SF Express и другие с буквами
        # Формат: 2 буквы + цифры + 2 буквы (например: LP123456789CN)
        r'\b[A-Z]{2}\d{9,13}[A-Z]{2}\b',
        
        # SF Express: SF + 13 цифр
        r'\bSF\d{13}\b',
        
        # EMS China: E + буквы/цифры + CN
        r'\bE[A-Z0-9]{9,13}CN\b',
        
        # Общий паттерн для буквенно-числовых номеров (10-20 символов)
        r'\b[A-Z0-9]{10,20}\b',
    ]
    
    @classmethod
    def extract_tracking_numbers(cls, text: str) -> List[str]:
        """
        Извлечь все возможные трек-номера из текста
        
        Args:
            text: Текст сообщения
            
        Returns:
            Список найденных трек-номеров (уникальные)
        """
        if not text:
            return []
        
        # Приводим к верхнему регистру для единообразия
        text_upper = text.upper()
        
        found_numbers = set()
        
        for pattern in cls.PATTERNS:
            matches = re.findall(pattern, text_upper)
            found_numbers.update(matches)
        
        # Преобразуем в список и сортируем по длине (более длинные - более специфичные)
        result = sorted(list(found_numbers), key=len, reverse=True)
        
        logger.debug(f"Extracted tracking numbers from text: {result}")
        
        return result
    
    @classmethod
    def extract_first_tracking_number(cls, text: str) -> Optional[str]:
        """
        Извлечь первый (наиболее вероятный) трек-номер из текста
        
        Args:
            text: Текст сообщения
            
        Returns:
            Первый найденный трек-номер или None
        """
        numbers = cls.extract_tracking_numbers(text)
        
        if numbers:
            tracking_number = numbers[0]
            logger.info(f"Found tracking number: {tracking_number}")
            return tracking_number
        
        logger.warning(f"No tracking number found in text: {text[:100]}")
        return None
    
    @classmethod
    def is_valid_tracking_number(cls, number: str) -> bool:
        """
        Проверить, является ли строка валидным трек-номером
        
        Args:
            number: Строка для проверки
            
        Returns:
            True если похоже на трек-номер
        """
        if not number:
            return False
        
        number_upper = number.upper()
        
        for pattern in cls.PATTERNS:
            if re.match(f"^{pattern}$", number_upper):
                return True
        
        return False
