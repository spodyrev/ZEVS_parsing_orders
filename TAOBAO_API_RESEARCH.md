# Инструкция по исследованию Taobao API

Это важнейший этап! Без понимания структуры API Taobao парсер не сможет получать данные.

## Шаг 1: Подготовка

1. Открой браузер Chrome или Edge (рекомендуется)
2. Перейди на сайт Taobao: https://www.taobao.com/
3. Авторизуйся в своем аккаунте через AliPay

## Шаг 2: Открываем DevTools

1. Нажми `F12` или `Cmd+Option+I` (macOS) для открытия DevTools
2. Перейди на вкладку **Network** (Сеть)
3. В фильтрах выбери **XHR** или **Fetch** (это API запросы)

## Шаг 3: Переходим в раздел заказов

1. Перейди на страницу "Мои заказы": https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm
2. Подожди, пока страница загрузится
3. В DevTools Network ты увидишь множество запросов

## Шаг 4: Находим нужный API эндпоинт

Ищи запросы, которые содержат информацию о заказах. Обычно это:

### Признаки нужного запроса:
- URL содержит слова типа `order`, `trade`, `list`, `query`
- Тип: `XHR` или `fetch`
- Метод: обычно `GET` или `POST`
- Response содержит JSON с данными заказов

### Примеры возможных эндпоинтов:
```
https://buyertrade.taobao.com/trade/itemlist/asyncBought.htm
https://trade.taobao.com/trade/itemlist/list_bought_items.htm
https://buyertrade.taobao.com/trade/itemlist/list.do
```

## Шаг 5: Анализируем запрос

Когда нашел нужный запрос, изучи его:

### Request (Запрос):
1. **Request Headers** - особенно важны:
   - `Cookie` - содержит данные авторизации
   - `User-Agent` - идентификатор браузера
   - `Referer` - откуда пришел запрос
   - Возможно есть специальные токены (типа `x-csrf-token`)

2. **Query Parameters** (если GET) или **Form Data** (если POST):
   - Параметры пагинации (page, pageSize)
   - Фильтры (status, dateRange)
   - ID пользователя или другие идентификаторы

### Response (Ответ):
1. Переключись на вкладку **Response**
2. Посмотри структуру JSON:

```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "orderId": "123456789",
        "status": "WAIT_BUYER_CONFIRM_GOODS",
        "title": "Товар название",
        "payment": 299.99,
        "logisticsNo": "RF123456789CN",
        ...
      }
    ]
  }
}
```

## Шаг 6: Копируем запрос

1. Правой кнопкой на нужном запросе
2. Выбери **Copy** -> **Copy as cURL** (или Copy as Fetch)
3. Сохрани в отдельный файл для анализа

## Шаг 7: Документируем находки

Создай файл `taobao_api_notes.txt` и запиши:

```
=== ЭНДПОИНТ ДЛЯ СПИСКА ЗАКАЗОВ ===
URL: [вставь URL]
Метод: GET/POST
Headers:
  - Cookie: [важно!]
  - User-Agent: [скопируй]
  - [другие важные headers]

Query Parameters:
  - page: номер страницы
  - pageSize: количество на странице
  - [другие параметры]

Структура ответа:
[вставь пример JSON]

=== ВАЖНЫЕ COOKIES ===
[скопируй значения cookies, которые относятся к авторизации]
Обычно это: _tb_token_, cookie2, t, etc.

=== СТАТУСЫ ЗАКАЗОВ ===
Найденные статусы и их значения:
- WAIT_BUYER_PAY = не оплачен
- WAIT_SELLER_SEND_GOODS = оплачен, ждет отправки
- WAIT_BUYER_CONFIRM_GOODS = отправлен
- TRADE_FINISHED = завершен
[добавь другие, которые найдешь]
```

## Шаг 8: Проверяем детали заказа

1. Кликни на один из заказов
2. В DevTools найди запрос за деталями этого заказа
3. Изучи его структуру (может быть другой эндпоинт)

## Шаг 9: Проверяем пагинацию

1. Перелистни на следующую страницу заказов
2. Посмотри, как изменились параметры запроса
3. Запиши логику пагинации

## Шаг 10: Тестируем запрос вручную

Можно протестировать запрос через Python:

```python
import requests

url = "URL_КОТОРЫЙ_НАШЕЛ"
headers = {
    "Cookie": "ТВОИ_COOKIES",
    "User-Agent": "ТВОЙ_USER_AGENT"
}

response = requests.get(url, headers=headers)
print(response.json())
```

## Важные замечания

⚠️ **Безопасность:**
- НЕ публикуй свои cookies в интернете
- Cookies дают полный доступ к твоему аккаунту
- Храни cookies.json в .gitignore

⚠️ **Антибот защита:**
- Taobao может использовать защиту от ботов
- Возможны капчи
- Могут требоваться специальные заголовки

⚠️ **Изменения API:**
- Taobao может изменить API в любой момент
- Сохраняй raw_data в БД для отладки

## Следующие шаги

После того как найдешь API эндпоинты:

1. Обнови `taobao_client.py`:
   - Замени URL на реальный
   - Добавь нужные headers
   - Реализуй метод `get_orders()`

2. Обнови `parser.py`:
   - Адаптируй под реальную структуру JSON
   - Добавь все возможные статусы

3. Протестируй:
   ```bash
   cd backend/scraper
   python taobao_client.py
   ```

## Альтернативный подход

Если API слишком сложный или защищен:

1. **Парсинг HTML** - извлекаем данные из HTML страницы
2. **Перехват через Playwright** - используем `page.on('response')` для перехвата запросов
3. **Ручной экспорт** - экспортируй данные вручную и импортируй в систему

## Полезные ресурсы

- [Playwright Documentation](https://playwright.dev/python/)
- [Chrome DevTools Network](https://developer.chrome.com/docs/devtools/network/)
- [HTTP requests in Python](https://requests.readthedocs.io/)
