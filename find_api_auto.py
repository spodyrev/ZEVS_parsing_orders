#!/usr/bin/env python3
"""
Автоматический поиск Taobao API запросов
Этот скрипт откроет браузер и поможет найти правильный API эндпоинт
"""

import sys
import os
import json
import time
from typing import List, Dict

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from playwright.sync_api import sync_playwright, Route
from loguru import logger

logger.info("=" * 70)
logger.info("🔍 АВТОМАТИЧЕСКИЙ ПОИСК TAOBAO API")
logger.info("=" * 70)

# Список для сохранения перехваченных запросов
intercepted_requests = []

def intercept_request(route: Route):
    """Перехватывает все сетевые запросы"""
    request = route.request
    
    # Продолжаем запрос
    route.continue_()
    
    # Сохраняем только XHR/Fetch запросы к API
    if 'h5api.m.taobao.com' in request.url and 'querybought' in request.url.lower():
        logger.info(f"✅ НАЙДЕН API ЗАПРОС!")
        logger.info(f"   URL: {request.url[:100]}...")
        
        intercepted_requests.append({
            'url': request.url,
            'method': request.method,
            'headers': request.headers,
            'timestamp': time.time()
        })

def main():
    logger.info("\n📋 Инструкция:")
    logger.info("1. Сейчас откроется браузер")
    logger.info("2. Войди в свой аккаунт Taobao")
    logger.info("3. Перейди на страницу 'Мои заказы' (已买到的宝贝)")
    logger.info("4. Скрипт автоматически перехватит API запросы")
    logger.info("5. Нажми Enter когда увидишь свои заказы\n")
    
    input("Нажми Enter чтобы начать...")
    
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
        
        # Включаем перехват запросов
        page.route("**/*", intercept_request)
        
        logger.info("✅ Браузер запущен")
        logger.info("\n⚠️  ВАЖНО:")
        logger.info("   Сейчас я открою страницу Taobao")
        logger.info("   1. Войди в аккаунт если нужно")
        logger.info("   2. Перейди в 'Мои заказы'")
        logger.info("   3. Дождись загрузки заказов")
        logger.info("   4. Вернись в терминал и нажми Enter\n")
        
        # Открываем страницу заказов
        try:
            page.goto('https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm', 
                     timeout=60000)
            logger.info("✅ Страница открыта")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки страницы: {e}")
            logger.info("Попробуй вручную перейти на страницу заказов")
        
        # Ждем действий пользователя
        input("\n👉 Когда увидишь свои заказы, нажми Enter...")
        
        # Анализируем перехваченные запросы
        logger.info("\n" + "=" * 70)
        logger.info("📊 РЕЗУЛЬТАТЫ ПЕРЕХВАТА")
        logger.info("=" * 70)
        
        if not intercepted_requests:
            logger.warning("\n⚠️ API запросы не найдены!")
            logger.warning("\nВозможные причины:")
            logger.warning("  1. Страница еще не загрузилась")
            logger.warning("  2. Страница использует другой API")
            logger.warning("  3. Нужно перезагрузить страницу")
            logger.warning("\nЧто делать:")
            logger.warning("  1. В открытом браузере нажми F5 (перезагрузи страницу)")
            logger.warning("  2. Дождись загрузки заказов")
            logger.warning("  3. Нажми Enter в терминале еще раз")
            
            input("\n👉 Нажми Enter после перезагрузки страницы...")
            
            time.sleep(2)  # Даем время на перехват
        
        if intercepted_requests:
            logger.info(f"\n✅ Найдено API запросов: {len(intercepted_requests)}")
            
            # Берем последний запрос (обычно самый актуальный)
            request = intercepted_requests[-1]
            
            logger.info("\n" + "=" * 70)
            logger.info("🎯 НАЙДЕН ПРАВИЛЬНЫЙ API ЗАПРОС!")
            logger.info("=" * 70)
            
            # Разбираем URL
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(request['url'])
            params = parse_qs(parsed_url.query)
            
            logger.info(f"\n📍 URL:")
            logger.info(f"   {parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}")
            
            logger.info(f"\n📋 Метод: {request['method']}")
            
            logger.info(f"\n🔑 Важные параметры:")
            important_params = ['api', 'appKey', 't', 'sign', 'data']
            for param in important_params:
                if param in params:
                    value = params[param][0]
                    if len(value) > 50:
                        value = value[:50] + "..."
                    logger.info(f"   {param}: {value}")
            
            # Сохраняем в файл
            output_file = 'found_api_request.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'url': request['url'],
                    'method': request['method'],
                    'headers': dict(request['headers']),
                    'timestamp': request['timestamp']
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n💾 Запрос сохранен в файл: {output_file}")
            
            # Пытаемся получить Response
            logger.info("\n📥 Пытаюсь получить Response...")
            try:
                # Делаем еще один запрос чтобы получить response
                response = page.goto(request['url'], wait_until='networkidle', timeout=10000)
                
                if response and response.ok:
                    try:
                        response_json = response.json()
                        
                        # Сохраняем response
                        response_file = 'found_api_response.json'
                        with open(response_file, 'w', encoding='utf-8') as f:
                            json.dump(response_json, f, indent=2, ensure_ascii=False)
                        
                        logger.info(f"✅ Response сохранен в файл: {response_file}")
                        
                        # Проверяем структуру
                        if 'data' in response_json and 'data' in response_json['data']:
                            data = response_json['data']['data']
                            
                            # Ищем заказы
                            order_count = len([k for k in data.keys() if k.startswith('shopInfo_')])
                            logger.info(f"\n📦 Найдено заказов в ответе: {order_count}")
                            
                            if order_count > 0:
                                logger.info("\n✅✅✅ УСПЕХ! Это правильный API запрос!")
                            else:
                                logger.warning("\n⚠️ Ответ получен, но заказов не найдено")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось распарсить JSON: {e}")
                
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить Response: {e}")
            
            # Генерируем cURL команду
            logger.info("\n" + "=" * 70)
            logger.info("📋 cURL КОМАНДА")
            logger.info("=" * 70)
            
            curl_cmd = f"curl '{request['url']}' \\\n"
            for header_name, header_value in request['headers'].items():
                if header_name.lower() in ['cookie', 'user-agent', 'accept', 'referer']:
                    curl_cmd += f"  -H '{header_name}: {header_value[:100]}...' \\\n"
            
            logger.info(f"\n{curl_cmd}")
            
            # Сохраняем cURL
            curl_file = 'found_api_curl.sh'
            with open(curl_file, 'w') as f:
                f.write(curl_cmd)
            
            logger.info(f"\n💾 cURL команда сохранена в файл: {curl_file}")
            
        else:
            logger.error("\n❌ API запросы так и не были найдены")
            logger.error("\nЧто делать дальше:")
            logger.error("  1. Открой DevTools (F12) в открытом браузере")
            logger.error("  2. Перейди на вкладку Network")
            logger.error("  3. Установи фильтр Fetch/XHR")
            logger.error("  4. Перезагрузи страницу")
            logger.error("  5. Найди запрос 'queryboughtlistv2' вручную")
            logger.error("  6. Скопируй 'Copy as cURL' и дай мне")
        
        # Сохраняем cookies
        logger.info("\n💾 Сохранение cookies...")
        cookies = context.cookies()
        
        cookies_file = 'taobao_cookies.json'
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Cookies сохранены в файл: {cookies_file}")
        logger.info(f"   (всего cookies: {len(cookies)})")
        
        logger.info("\n⚠️ Браузер останется открытым на 10 секунд...")
        logger.info("   Можешь проверить что-то вручную если нужно")
        time.sleep(10)
        
        # Закрываем браузер
        browser.close()
        logger.info("✅ Браузер закрыт")
    
    # Итог
    logger.info("\n" + "=" * 70)
    logger.info("📊 ИТОГОВЫЕ ФАЙЛЫ")
    logger.info("=" * 70)
    
    files_created = []
    
    if os.path.exists('found_api_request.json'):
        files_created.append('found_api_request.json - Информация о запросе')
    if os.path.exists('found_api_response.json'):
        files_created.append('found_api_response.json - JSON ответ от API')
    if os.path.exists('found_api_curl.sh'):
        files_created.append('found_api_curl.sh - cURL команда')
    if os.path.exists('taobao_cookies.json'):
        files_created.append('taobao_cookies.json - Cookies для авторизации')
    
    if files_created:
        logger.info("\n✅ Созданы файлы:")
        for file in files_created:
            logger.info(f"   - {file}")
        
        logger.info("\n🎯 Следующие шаги:")
        logger.info("   1. Проверь файл found_api_response.json")
        logger.info("   2. Убедись, что там есть твои заказы")
        logger.info("   3. Если все ОК - система уже настроена!")
        logger.info("   4. Запусти ./start.sh и попробуй синхронизацию")
    else:
        logger.warning("\n⚠️ Файлы не созданы - API не найден")
        logger.warning("Следуй инструкциям в HOW_TO_FIND_CORRECT_API.md")
    
    logger.info("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Прервано пользователем")
    except Exception as e:
        logger.error(f"\n❌ Ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
