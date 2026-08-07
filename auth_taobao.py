#!/usr/bin/env python3
"""
Скрипт для авторизации на Taobao и сохранения cookies
Запускается отдельно от основного сервера
"""

import sys
import os
import json

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.sync_api import sync_playwright
from loguru import logger
from config import settings

def authorize_taobao():
    """
    Авторизация на Taobao через браузер
    """
    logger.info("=" * 60)
    logger.info("🔐 АВТОРИЗАЦИЯ НА TAOBAO")
    logger.info("=" * 60)
    
    cookies_file = settings.taobao_cookies_file
    
    # Проверяем существующие cookies
    if os.path.exists(cookies_file):
        logger.info(f"\n📁 Найдены существующие cookies: {cookies_file}")
        response = input("Хочешь использовать существующие cookies? (y/n): ")
        
        if response.lower() == 'y':
            logger.info("✅ Используем существующие cookies")
            return True
        else:
            logger.info("🗑️  Удаляем старые cookies...")
            os.remove(cookies_file)
    
    logger.info("\n📋 Инструкция:")
    logger.info("1. Сейчас откроется браузер")
    logger.info("2. Войди в свой аккаунт Taobao")
    logger.info("3. Перейди на страницу 'Мои заказы'")
    logger.info("4. После успешного входа вернись в терминал и нажми Enter")
    
    input("\nНажми Enter чтобы продолжить...")
    
    with sync_playwright() as p:
        logger.info("\n🌐 Запуск браузера...")
        
        # Запускаем браузер
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Создаем контекст
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        # Создаем страницу
        page = context.new_page()
        
        logger.info("✅ Браузер запущен")
        
        # Открываем страницу логина
        try:
            logger.info("\n🔗 Открываем Taobao...")
            page.goto('https://login.taobao.com/', timeout=60000)
            logger.info("✅ Страница загружена")
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки страницы: {e}")
            browser.close()
            return False
        
        logger.info("\n⚠️  ВАЖНО:")
        logger.info("   1. Войди в свой аккаунт Taobao в открытом браузере")
        logger.info("   2. После входа перейди на страницу заказов:")
        logger.info("      https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm")
        logger.info("   3. Убедись, что видишь свои заказы")
        logger.info("   4. Вернись в терминал и нажми Enter")
        
        input("\n👉 Нажми Enter после успешного входа...")
        
        # Проверяем авторизацию
        logger.info("\n🔍 Проверка авторизации...")
        try:
            current_url = page.url
            
            if 'login' in current_url.lower():
                logger.warning("⚠️ Похоже, ты всё еще на странице входа")
                logger.warning("Перейди на страницу заказов и нажми Enter снова")
                input("\n👉 Нажми Enter когда будешь готов...")
            
            # Переходим на страницу заказов для проверки
            logger.info("Проверяем доступ к заказам...")
            page.goto('https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm', 
                     timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            current_url = page.url
            
            if 'login' in current_url.lower():
                logger.error("❌ Авторизация не удалась - перенаправлено на страницу входа")
                browser.close()
                return False
            
            logger.info("✅ Авторизация успешна!")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка проверки: {e}")
            logger.info("Продолжаем сохранение cookies...")
        
        # Сохраняем cookies
        logger.info("\n💾 Сохранение cookies...")
        try:
            cookies = context.cookies()
            
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Cookies сохранены в {cookies_file}")
            logger.info(f"   Количество cookies: {len(cookies)}")
            
            # Проверяем важные cookies
            important_cookies = ['_tb_token_', 'cookie2', 't', '_m_h5_tk', 'unb']
            found_cookies = [c['name'] for c in cookies if c['name'] in important_cookies]
            
            logger.info(f"\n🔑 Важные cookies найдены:")
            for cookie_name in found_cookies:
                logger.info(f"   ✅ {cookie_name}")
            
            missing_cookies = [c for c in important_cookies if c not in found_cookies]
            if missing_cookies:
                logger.warning(f"\n⚠️ Отсутствующие cookies:")
                for cookie_name in missing_cookies:
                    logger.warning(f"   ❌ {cookie_name}")
                logger.warning("\nЭто может быть проблемой. Возможно, нужно:")
                logger.warning("  1. Полностью войти в аккаунт")
                logger.warning("  2. Перейти на разные страницы Taobao")
                logger.warning("  3. Попробовать авторизацию еще раз")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения cookies: {e}")
            browser.close()
            return False
        
        # Закрываем браузер
        logger.info("\n🔄 Закрытие браузера через 3 секунды...")
        import time
        time.sleep(3)
        browser.close()
        logger.info("✅ Браузер закрыт")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ АВТОРИЗАЦИЯ ЗАВЕРШЕНА")
    logger.info("=" * 60)
    logger.info("\n📝 Следующие шаги:")
    logger.info("   1. Запусти сервер: ./start.sh")
    logger.info("   2. Открой http://localhost:8000")
    logger.info("   3. Нажми 'Синхронизировать заказы'")
    logger.info("   4. Заказы должны загрузиться автоматически!")
    logger.info("\n" + "=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = authorize_taobao()
        
        if success:
            logger.info("\n✅ Готово! Теперь можешь запустить сервер.")
            sys.exit(0)
        else:
            logger.error("\n❌ Авторизация не удалась")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
