"""
Модуль для перевода текста с китайского на русский
Использует Google Gemini API (бесплатный) + fallback на googletrans
"""

import os
from typing import Optional
from loguru import logger

class Translator:
    """
    Переводчик текста с китайского на русский
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Инициализация переводчика
        
        Args:
            gemini_api_key: API ключ Google Gemini (опционально)
        """
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.gemini_available = False
        self.googletrans_available = False
        
        # Пытаемся инициализировать Gemini
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                self.gemini_available = True
                logger.info("✅ Google Gemini API инициализирован")
            except Exception as e:
                logger.warning(f"⚠️  Google Gemini недоступен: {e}")
        
        # Fallback: googletrans
        try:
            from googletrans import Translator as GoogleTranslator
            self.google_translator = GoogleTranslator()
            self.googletrans_available = True
            logger.info("✅ Google Translate (googletrans) инициализирован")
        except Exception as e:
            logger.warning(f"⚠️  Googletrans недоступен: {e}")
    
    def translate(self, text: str, max_retries: int = 2) -> Optional[str]:
        """
        Переводит текст с китайского на русский
        
        Args:
            text: Текст для перевода
            max_retries: Количество попыток
            
        Returns:
            str: Переведенный текст или None
        """
        if not text or not text.strip():
            return None
        
        # Пытаемся перевести через Gemini
        if self.gemini_available:
            result = self._translate_with_gemini(text, max_retries)
            if result:
                return result
        
        # Fallback на googletrans
        if self.googletrans_available:
            result = self._translate_with_googletrans(text, max_retries)
            if result:
                return result
        
        logger.error(f"❌ Не удалось перевести текст: {text[:50]}...")
        return None
    
    def _translate_with_gemini(self, text: str, max_retries: int) -> Optional[str]:
        """
        Перевод через Google Gemini API
        """
        for attempt in range(max_retries):
            try:
                prompt = f"""Переведи следующее описание товара с китайского на русский язык.
Сделай перевод максимально естественным и понятным для русскоязычного человека.
Убери лишние символы, эмодзи и технические детали.
Оставь только суть: название товара и его основные характеристики.

Китайский текст:
{text}

Переведи на русский:"""
                
                response = self.gemini_model.generate_content(prompt)
                translated = response.text.strip()
                
                if translated and len(translated) > 3:
                    logger.debug(f"✅ Gemini перевод: {text[:30]}... → {translated[:50]}...")
                    return translated
                    
            except Exception as e:
                logger.warning(f"⚠️  Gemini ошибка (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
        
        return None
    
    def _translate_with_googletrans(self, text: str, max_retries: int) -> Optional[str]:
        """
        Перевод через googletrans (неофициальный API)
        """
        for attempt in range(max_retries):
            try:
                result = self.google_translator.translate(text, src='zh-cn', dest='ru')
                translated = result.text.strip()
                
                if translated and len(translated) > 3:
                    logger.debug(f"✅ Googletrans перевод: {text[:30]}... → {translated[:50]}...")
                    return translated
                    
            except Exception as e:
                logger.warning(f"⚠️  Googletrans ошибка (попытка {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
        
        return None
    
    def translate_batch(self, texts: list[str], delay: float = 0.5) -> dict[str, str]:
        """
        Переводит несколько текстов
        
        Args:
            texts: Список текстов для перевода
            delay: Задержка между запросами (секунды)
            
        Returns:
            dict: Словарь {оригинал: перевод}
        """
        import time
        
        results = {}
        
        for i, text in enumerate(texts):
            logger.info(f"Перевод {i+1}/{len(texts)}: {text[:50]}...")
            
            translated = self.translate(text)
            if translated:
                results[text] = translated
            
            # Задержка между запросами
            if i < len(texts) - 1:
                time.sleep(delay)
        
        return results


# Пример использования
if __name__ == "__main__":
    translator = Translator()
    
    # Тестовый перевод
    test_text = "圆柱滚筒磨刀器厨房家用多功能快速手工磨刀石菜刀剪刀磁吸开刃器"
    result = translator.translate(test_text)
    
    print(f"Оригинал: {test_text}")
    print(f"Перевод: {result}")
