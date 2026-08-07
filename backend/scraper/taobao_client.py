"""
Клиент для работы с Taobao
Основной класс для получения заказов
"""

import json
import os
import time
import hashlib
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright, Browser, Page
import httpx
from loguru import logger

import sys
sys.path.append('..')
from config import settings
from scraper.parser import TaobaoParser


class TaobaoClient:
    """
    Клиент для работы с Taobao
    
    Использует Playwright для автоматизации браузера
    """
    
    def __init__(self):
        """Инициализация клиента"""
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.cookies_file = settings.taobao_cookies_file
        self.is_authenticated = False
        
        logger.info("TaobaoClient инициализирован")
    
    def start_browser(self):
        """
        Запускает браузер Playwright
        """
        logger.info("Запуск браузера...")
        playwright = sync_playwright().start()
        
        # Запускаем браузер (headless=False чтобы видеть, что происходит)
        self.browser = playwright.chromium.launch(
            headless=False,  # Измени на True когда все заработает
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Создаем контекст с настройками, чтобы выглядеть как обычный пользователь
        context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN'
        )
        
        self.page = context.new_page()
        logger.info("Браузер запущен")
    
    def load_cookies(self) -> bool:
        """
        Загружает сохраненные cookies
        
        Returns:
            bool: True если cookies загружены успешно
        """
        if not os.path.exists(self.cookies_file):
            logger.warning(f"Файл cookies не найден: {self.cookies_file}")
            return False
        
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # Добавляем cookies в браузер
            self.page.context.add_cookies(cookies)
            logger.info("Cookies загружены успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки cookies: {e}")
            return False
    
    def save_cookies(self):
        """
        Сохраняет текущие cookies в файл
        """
        try:
            cookies = self.page.context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Cookies сохранены в {self.cookies_file}")
        except Exception as e:
            logger.error(f"Ошибка сохранения cookies: {e}")
    
    def login(self) -> bool:
        """
        Авторизация на Taobao
        
        TODO: Реализовать автоматическую авторизацию
        Пока что этот метод открывает страницу логина и ждет,
        пока ты войдешь вручную
        
        Returns:
            bool: True если авторизация успешна
        """
        logger.info("Начало авторизации...")
        
        if not self.browser:
            self.start_browser()
        
        # Пытаемся загрузить сохраненные cookies
        if self.load_cookies():
            # Проверяем, валидны ли cookies
            if self.check_auth():
                logger.info("Авторизация через cookies успешна")
                return True
        
        # Если cookies не сработали, открываем страницу входа
        logger.info("Открываем страницу входа Taobao...")
        self.page.goto('https://login.taobao.com/')
        
        logger.info("⚠️  ВОЙДИ ВРУЧНУЮ В БРАУЗЕРЕ")
        logger.info("После успешного входа нажми Enter в терминале...")
        input("Нажми Enter после входа: ")
        
        # Сохраняем cookies после успешного входа
        self.save_cookies()
        self.is_authenticated = True
        
        return True
    
    def check_auth(self) -> bool:
        """
        Проверяет, авторизован ли пользователь
        
        Returns:
            bool: True если авторизован
        """
        try:
            # Переходим на страницу "Мои заказы"
            self.page.goto('https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm')
            self.page.wait_for_load_state('networkidle', timeout=10000)
            
            # Если нас не перебросило на логин, значит авторизованы
            current_url = self.page.url
            if 'login' not in current_url:
                logger.info("Авторизация действительна")
                self.is_authenticated = True
                return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки авторизации: {e}")
        
        return False
    
    def _get_cookies_dict(self) -> Dict[str, str]:
        """
        Извлекает cookies из браузера в формате словаря
        Если браузер не запущен, загружает из файла
        
        Returns:
            Dict[str, str]: Словарь cookies {name: value}
        """
        cookies_dict = {}
        
        # Пытаемся получить из браузера если он запущен
        if self.page:
            try:
                cookies = self.page.context.cookies()
                for cookie in cookies:
                    cookies_dict[cookie['name']] = cookie['value']
                logger.debug(f"Извлечено {len(cookies_dict)} cookies из браузера")
                return cookies_dict
            except Exception as e:
                logger.warning(f"Не удалось получить cookies из браузера: {e}")
        
        # Загружаем из файла
        return self._load_cookies_from_file()
    
    def _load_cookies_from_file(self) -> Dict[str, str]:
        """
        Загружает cookies из файла
        
        Returns:
            Dict[str, str]: Словарь cookies {name: value}
        """
        cookies_dict = {}
        
        if not os.path.exists(self.cookies_file):
            logger.warning(f"Файл cookies не найден: {self.cookies_file}")
            return cookies_dict
        
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            for cookie in cookies:
                cookies_dict[cookie['name']] = cookie['value']
            
            logger.debug(f"Загружено {len(cookies_dict)} cookies из файла")
            
            # Проверяем важные cookies
            important = ['_m_h5_tk', '_tb_token_', 'cookie2', 't']
            missing = [c for c in important if c not in cookies_dict]
            
            if missing:
                logger.warning(f"Отсутствуют важные cookies: {', '.join(missing)}")
                logger.warning("Возможно, нужна повторная авторизация")
            
            return cookies_dict
            
        except Exception as e:
            logger.error(f"Ошибка загрузки cookies из файла: {e}")
            return cookies_dict
    
    def get_orders(self, page: int = 1, page_size: int = 15) -> List[Dict]:
        """
        Получает список заказов через Taobao API (БЕЗ Playwright)
        Использует сохраненные cookies из файла
        
        Args:
            page: Номер страницы
            page_size: Количество заказов на странице
            
        Returns:
            List[Dict]: Список заказов
        """
        logger.info(f"Получение заказов (страница {page})...")
        
        # Загружаем cookies из файла
        cookies_dict = self._load_cookies_from_file()
        if not cookies_dict:
            logger.error("❌ Cookies не найдены!")
            logger.error("Запусти: python3 auth_taobao.py для авторизации")
            return []
        
        try:
            # API эндпоинт Taobao
            base_url = "https://h5api.m.taobao.com/h5/mtop.taobao.order.queryboughtlistv2/1.0/"
            
            # Генерируем timestamp
            timestamp = str(int(time.time() * 1000))
            
            # Получаем cookies из браузера
            cookies_dict = self._get_cookies_dict()
            
            # Получаем _m_h5_tk из cookies для подписи
            m_h5_tk = cookies_dict.get("_m_h5_tk", "")
            token = m_h5_tk.split("_")[0] if "_" in m_h5_tk else m_h5_tk
            
            # Параметры запроса (для генерации подписи)
            data_param = json.dumps({
                "tabCode": "all",
                "page": page,
                "OrderType": "OrderList",
                "appName": "tborder",
                "appVersion": "3.0",
                "condition": json.dumps({"directRouteToTm2Scene": "1"}),
                "__needlessClearProtocol__": True
            }, separators=(',', ':'))
            
            # Генерируем подпись (sign)
            sign_string = f"{token}&{timestamp}&12574478&{data_param}"
            sign = hashlib.md5(sign_string.encode()).hexdigest()
            
            # Query параметры
            params = {
                "jsv": "2.7.2",
                "appKey": "12574478",
                "t": timestamp,
                "sign": sign,
                "v": "1.0",
                "ecode": "1",
                "timeout": "8000",
                "dataType": "json",
                "valueType": "original",
                "ttid": "1@tbwang_mac_1.0.0#pc",
                "needLogin": "true",
                "type": "originaljson",
                "isHttps": "1",
                "needRetry": "true",
                "api": "mtop.taobao.order.queryboughtlistV2",
                "__customTag__": "boughtList_all_OrderList",
                "preventFallback": "true",
                "data": data_param
            }
            
            # Headers
            headers = {
                "accept": "application/json",
                "accept-language": "ru,en;q=0.9",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                "referer": "https://buyertrade.taobao.com/",
                "origin": "https://buyertrade.taobao.com"
            }
            
            # Делаем запрос (POST, не GET!)
            logger.info(f"Запрос к API: {base_url}")
            client = httpx.Client(timeout=30.0)
            
            # POST запрос с data в теле
            response = client.post(
                base_url,
                params={k: v for k, v in params.items() if k != 'data'},  # Все кроме data в URL
                data={'data': data_param},  # data в теле запроса
                headers=headers,
                cookies=cookies_dict
            )
            
            logger.debug(f"Статус ответа: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Ошибка API: статус {response.status_code}")
                return []
            
            # Парсим ответ
            response_json = response.json()
            
            # Сохраняем для отладки
            self.last_response = response_json
            
            # Проверяем успешность
            if not response_json.get("ret"):
                logger.error(f"API вернул ошибку: {response_json}")
                return []
            
            # Проверяем ret формат ["SUCCESS::0"]
            ret_list = response_json.get("ret", [])
            if not ret_list or not any("SUCCESS" in str(r) for r in ret_list):
                logger.error(f"API вернул неуспешный статус: {ret_list}")
                return []
            
            # Парсим заказы
            logger.info("Парсинг данных заказов...")
            orders = TaobaoParser.parse_orders_list(response_json)
            
            logger.info(f"Получено {len(orders)} заказов")
            return orders
            
        except Exception as e:
            logger.error(f"Ошибка получения заказов: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def get_order_details(self, order_id: str) -> Optional[Dict]:
        """
        Получает детальную информацию о заказе через API mtop.taobao.order.query.detailv2
        
        Args:
            order_id: ID заказа (bizOrderId)
            
        Returns:
            Dict: Полный JSON ответ от API, или None при ошибке
        """
        logger.info(f"Получение деталей заказа {order_id}...")
        
        # Загружаем cookies
        cookies_dict = self._load_cookies_from_file()
        if not cookies_dict:
            logger.error("❌ Cookies не найдены!")
            return None
        
        try:
            # API эндпоинт для деталей заказа
            base_url = "https://h5api.m.taobao.com/h5/mtop.taobao.order.query.detailv2/1.0/"
            
            # Генерируем timestamp
            timestamp = str(int(time.time() * 1000))
            
            # Получаем token из cookies
            m_h5_tk = cookies_dict.get("_m_h5_tk", "")
            token = m_h5_tk.split("_")[0] if "_" in m_h5_tk else m_h5_tk
            
            # Параметры запроса (упрощенная версия с ключевыми полями)
            data_param = json.dumps({
                "bizOrderId": order_id,
                "appVersion": "3.0",
                "appName": "tborder",
                "useV2": "true",
                "archive": False
            }, separators=(',', ':'))
            
            # Генерируем подпись (sign)
            sign_string = f"{token}&{timestamp}&12574478&{data_param}"
            sign = hashlib.md5(sign_string.encode()).hexdigest()
            
            # Query параметры (базовые, проверенные)
            params = {
                "jsv": "2.7.2",
                "appKey": "12574478",
                "t": timestamp,
                "sign": sign,
                "v": "1.0",
                "timeout": "6000",
                "dataType": "json",
                "valueType": "original",
                "ttid": "1@tbwang_mac_1.0.0#pc",
                "needLogin": "true",
                "type": "originaljson",
                "isHttps": "1",
                "api": "mtop.taobao.order.query.detailv2"
            }
            
            # Headers (полные, как в браузере)
            headers = {
                "accept": "application/json",
                "accept-language": "ru,en;q=0.9",
                "content-type": "application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
                "referer": f"https://trade.taobao.com/trade/detail/trade_order_detail.htm?biz_order_id={order_id}",
                "origin": "https://trade.taobao.com",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site"
            }
            
            # Делаем POST запрос
            logger.debug(f"Запрос к API деталей: {base_url}")
            logger.debug(f"📝 data_param: {data_param}")
            logger.debug(f"🔑 sign: {sign}")
            logger.debug(f"📋 params: {params}")
            
            client = httpx.Client(timeout=30.0)
            
            response = client.post(
                base_url,
                params=params,
                data={'data': data_param},
                headers=headers,
                cookies=cookies_dict
            )
            
            logger.debug(f"Статус ответа: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Ошибка API деталей: статус {response.status_code}")
                return None
            
            # Парсим ответ
            response_json = response.json()
            
            # Проверяем успешность
            ret_list = response_json.get("ret", [])
            if not ret_list or not any("SUCCESS" in str(r) for r in ret_list):
                logger.error(f"API деталей вернул неуспешный статус: {ret_list}")
                return None
            
            logger.info(f"✅ Детали заказа {order_id} получены")
            return response_json
            
        except Exception as e:
            logger.error(f"Ошибка получения деталей заказа {order_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    
    def get_tracking_number_browser(self, order_id: str) -> Optional[str]:
        """
        Получает трек-номер заказа через браузер (Playwright)
        
        Этот метод использует браузер вместо API, так как API
        не возвращает logisticsPackages для программного доступа.
        
        Args:
            order_id: ID заказа
            
        Returns:
            str: Трек-номер или None
        """
        logger.info(f"Получение трек-номера через браузер для заказа {order_id}...")
        
        try:
            # Запускаем браузер если еще не запущен
            if not self.browser:
                self.start_browser()
            
            # Загружаем cookies если есть
            if os.path.exists(self.cookies_file):
                self.load_cookies()
            
            # Открываем страницу логистики
            logistics_url = f"https://market.m.taobao.com/app/dinamic/pc-trade-logistics/home.html?orderId={order_id}&entrance=pc"
            logger.debug(f"Открываем страницу логистики: {logistics_url}")
            
            # Используем более мягкую стратегию ожидания (domcontentloaded вместо networkidle)
            self.page.goto(logistics_url, wait_until="domcontentloaded", timeout=60000)
            
            # Ждем загрузки данных (даем странице время на инициализацию)
            time.sleep(5)
            
            # Делаем снимок экрана для отладки
            screenshot_path = "debug_logistics_page.png"
            self.page.screenshot(path=screenshot_path)
            logger.debug(f"📸 Снимок экрана сохранен: {screenshot_path}")
            
            # Пытаемся найти трек-номер на странице
            # Вариант 1: Ищем по тексту "运单号" (номер накладной)
            try:
                tracking_element = self.page.locator('text=/运单号[:：]?\\s*([A-Z0-9]+)/').first
                tracking_text = tracking_element.inner_text(timeout=5000)
                
                # Извлекаем номер (после двоеточия)
                if ':' in tracking_text or '：' in tracking_text:
                    tracking_number = tracking_text.split(':')[-1].split('：')[-1].strip()
                    logger.info(f"✅ Трек-номер найден: {tracking_number}")
                    return tracking_number
            except Exception as e:
                logger.debug(f"Не найден по паттерну '运单号': {e}")
            
            # Вариант 2: Ищем числовой код (обычно трек-номер - это длинная последовательность цифр)
            try:
                # Получаем весь текст страницы
                page_text = self.page.inner_text('body')
                
                # Ищем паттерн трек-номера (обычно 10-20 цифр подряд)
                import re
                matches = re.findall(r'\b\d{10,20}\b', page_text)
                
                if matches:
                    # Берем первое совпадение (обычно это и есть трек-номер)
                    tracking_number = matches[0]
                    logger.info(f"✅ Трек-номер найден (по паттерну): {tracking_number}")
                    return tracking_number
            except Exception as e:
                logger.debug(f"Не найден по числовому паттерну: {e}")
            
            logger.warning(f"❌ Трек-номер не найден на странице логистики для заказа {order_id}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения трек-номера через браузер: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def close(self):
        """Закрывает браузер"""
        if self.browser:
            self.browser.close()
            logger.info("Браузер закрыт")


# Пример использования
if __name__ == "__main__":
    client = TaobaoClient()
    
    # Авторизация
    if client.login():
        print("✅ Авторизация успешна!")
        
        # Получаем заказы
        orders = client.get_orders()
        print(f"Найдено заказов: {len(orders)}")
        
        # Закрываем браузер
        client.close()
    else:
        print("❌ Ошибка авторизации")
