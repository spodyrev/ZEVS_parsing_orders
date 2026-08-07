# Руководство: Получение трек-номеров из Taobao

## Проблема
Трек-номера НЕ доступны в API списка заказов (`mtop.taobao.order.queryboughtlistv2`).
Они находятся только на странице деталей конкретного заказа.

## Решение

### Шаг 1: Найти API endpoint для деталей заказа

1. **Откройте Chrome DevTools** (F12)
2. **Перейдите на вкладку Network**
3. **Кликните на любой заказ** в списке заказов Taobao
4. **Ищите XHR запрос**, который загружает детали заказа

#### Возможные варианты endpoint:
```
https://h5api.m.taobao.com/h5/mtop.taobao.order.queryo rderdetail/...
https://trade.taobao.com/trade/detail/trade_order_detail.htm?biz_order_id=XXX
https://buyertrade.taobao.com/trade/detail/...
```

### Шаг 2: Анализ запроса

Когда найдете запрос за деталями заказа:

1. **Скопируйте URL** полностью
2. **Посмотрите Query Parameters:**
   - `orderId` или `biz_order_id` - ID заказа
   - `sign` - подпись запроса (если есть)
   - другие параметры

3. **Посмотрите Response:**
   - Найдите поле с трек-номером
   - Обычно это: `logisticsNo`, `trackingNumber`, `waybillNum`, `expressNo`

### Шаг 3: Структура ожидаемого ответа

```json
{
  "data": {
    "orderId": "3316521288174009384",
    "tracking": {
      "companyName": "中通快递",
      "trackingNumber": "75480803526593",
      "status": "已签收"
    },
    "logistics": [
      {
        "time": "2026-08-10 14:30",
        "status": "已签收，签收人：本人签收"
      }
    ]
  }
}
```

### Шаг 4: Получение данных

#### Вариант A: Через API (если есть endpoint)

```python
def get_order_tracking(order_id, cookies):
    url = f"https://h5api.m.taobao.com/h5/mtop.taobao.order.queryorderdetail/..."
    params = {
        "orderId": order_id,
        # другие параметры
    }
    headers = {
        "Cookie": cookies,
        "User-Agent": "...",
    }
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    # Извлекаем трек-номер
    tracking_number = data["data"]["tracking"]["trackingNumber"]
    return tracking_number
```

#### Вариант B: Парсинг HTML страницы (если API недоступен)

```python
from playwright.sync_api import sync_playwright

def get_order_tracking_from_page(order_id, cookies):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Загружаем cookies
        context.add_cookies(cookies)
        
        page = context.new_page()
        
        # Переходим на страницу заказа
        url = f"https://trade.taobao.com/trade/detail/trade_order_detail.htm?biz_order_id={order_id}"
        page.goto(url)
        
        # Ждем загрузки
        page.wait_for_load_state('networkidle')
        
        # Ищем трек-номер на странице
        tracking_element = page.query_selector('.tracking-number') # Нужно найти правильный селектор
        if tracking_element:
            tracking_number = tracking_element.text_content()
            return tracking_number
        
        browser.close()
        return None
```

#### Вариант C: Перехват API запросов через Playwright

```python
def get_tracking_via_intercept(order_id, cookies):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies)
        
        page = context.new_page()
        
        tracking_data = None
        
        # Перехватываем API запросы
        def handle_response(response):
            nonlocal tracking_data
            if 'orderdetail' in response.url or 'tracking' in response.url:
                try:
                    data = response.json()
                    # Извлекаем трек-номер из ответа
                    tracking_data = parse_tracking_from_response(data)
                except:
                    pass
        
        page.on('response', handle_response)
        
        # Открываем страницу заказа
        url = f"https://trade.taobao.com/trade/detail/trade_order_detail.htm?biz_order_id={order_id}"
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        browser.close()
        return tracking_data
```

### Шаг 5: Интеграция в систему

1. **Добавить метод в `taobao_client.py`:**
   ```python
   def get_order_details(self, order_id: str) -> Dict:
       """Получает детальную информацию о заказе"""
       pass
   ```

2. **Обновить синхронизацию:**
   - После получения списка заказов
   - Для каждого заказа без трек-номера
   - Запросить детали и обновить tracking_number

3. **Добавить rate limiting:**
   - Не делать слишком много запросов сразу
   - Добавить задержки между запросами (1-2 секунды)
   - Возможно, делать это только для "В пути" заказов

### Шаг 6: Оптимизация

1. **Кеширование:**
   - Не запрашивать tracking для заказов, которые уже доставлены
   - Запоминать, когда последний раз проверяли

2. **Приоритеты:**
   - Сначала обновлять tracking для заказов в статусе "shipped"
   - Пропускать "delivered" и "cancelled"

3. **Фоновое обновление:**
   - Делать это асинхронно
   - Не блокировать основную синхронизацию

## Инструкция для пользователя

### Что нужно сделать СЕЙЧАС:

1. **Откройте DevTools** в браузере
2. **Откройте страницу "Мои заказы"** на Taobao
3. **Кликните на любой заказ** (откроется детальная страница)
4. **В Network найдите XHR запрос**, который загрузил детали
5. **Скопируйте:**
   - URL запроса
   - Response (JSON ответ)
   - Найдите в нем поле с трек-номером

6. **Создайте файл** `tracking_api_example.json` с примером ответа

Это поможет реализовать функцию получения трек-номеров!

## Примеры реальных endpoint'ов (могут отличаться):

```
# Детали заказа
https://h5api.m.taobao.com/h5/mtop.trade.order.detail.get/4.0/

# Информация о доставке
https://h5api.m.taobao.com/h5/mtop.taobao.logistics.info.get/1.0/

# Мобильная версия деталей
https://trade.m.taobao.com/trade/detail/detail.html?tradeId=XXX
```

## Следующие шаги:

После того как найдете правильный endpoint:
1. Реализуем функцию получения трек-номера
2. Добавим в процесс синхронизации
3. Обновим существующие заказы
4. Проверим отображение в веб-интерфейсе

