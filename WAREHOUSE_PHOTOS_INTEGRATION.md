# 📸 Интеграция фото со склада

## ✅ Что добавлено

### 1. База данных
- **Новое поле:** `warehouse_photo_path` в таблице `orders`
- **Тип:** TEXT (хранит имя файла фото)
- **Миграция:** `migrate_add_warehouse_photo.py` (выполнена)

### 2. Backend (API)
- **Endpoint:** `GET /api/orders/{order_id}/warehouse-photo`
- **Функция:** Возвращает фото товара со склада
- **Формат:** JPEG image file

### 3. Telegram Bot
- **Обновлен:** `backend/telegram_bot/handlers.py`
- **Новое:** Сохраняет путь к фото в БД при обработке трек-номера
- **Поле:** `order.warehouse_photo_path = filename`

### 4. Веб-интерфейс
- **Новая колонка:** "Фото со склада" в таблице заказов
- **Отображение:** 
  - ✅ Миниатюра фото (60x60) с зеленой рамкой
  - ❌ "Фото отсутствует" если получен но нет фото
  - — Прочерк если товар не получен
- **Клик:** Открывает фото в полном размере в новой вкладке

## 🎯 Как это работает

### Workflow:

```
1. Склад отправляет фото в Telegram
   ↓
2. Бот сохраняет в warehouse_photos/temp_*.jpg
   ↓
3. Склад отправляет трек-номер
   ↓
4. Бот находит заказ в БД
   ↓
5. Бот переименовывает: 435301476185280_20260806_225130.jpg
   ↓
6. Бот сохраняет в БД: warehouse_photo_path = "435301476185280_20260806_225130.jpg"
   ↓
7. Веб-интерфейс показывает фото через API
```

## 📂 Структура

```
MySyte/
├── warehouse_photos/
│   ├── 435301476185280_20260806_225130.jpg  ← Фото со склада
│   ├── 15811880672_20260806_230145.jpg
│   └── ...
├── backend/
│   ├── app.py                                ← API endpoint добавлен
│   ├── models.py                             ← Поле добавлено
│   └── telegram_bot/
│       └── handlers.py                       ← Сохранение пути добавлено
└── frontend/
    └── templates/
        └── index.html                        ← Колонка добавлена
```

## 🔧 API Endpoint

### Запрос:
```http
GET /api/orders/3316188865004018566/warehouse-photo
```

### Ответ (успех):
```
Content-Type: image/jpeg
[binary image data]
```

### Ответ (ошибка):
```json
{
  "detail": "Фото не найдено"
}
```

## 💻 Веб-интерфейс

### Таблица заказов:

| Получен на складе | Фото со склада | Действия |
|-------------------|----------------|----------|
| ☑️ Да | ![Фото](thumbnail) | В архив |
| ☑️ Да | Фото отсутствует | В архив |
| ☐ Нет | — | В архив |

### Клик на фото:
- Открывает полное изображение в новой вкладке
- URL: `/api/orders/{order_id}/warehouse-photo`

## 🧪 Тестирование

### 1. Протестируйте Telegram бота:

```bash
# Запустите бота
python start_telegram_bot.py
```

В Telegram:
1. Отправьте фото
2. Отправьте трек-номер: `435301476185280`
3. Проверьте подтверждение

### 2. Проверьте файл:

```bash
ls -lh warehouse_photos/435301476185280_*.jpg
```

### 3. Проверьте БД:

```bash
python -c "
from backend.database import SessionLocal
from backend.models import Order
db = SessionLocal()
order = db.query(Order).filter(Order.tracking_number == '435301476185280').first()
print(f'Фото: {order.warehouse_photo_path}')
db.close()
"
```

### 4. Проверьте веб-интерфейс:

Откройте http://localhost:8000

Должны увидеть новую колонку "Фото со склада" с миниатюрой.

### 5. Проверьте API:

```bash
curl http://localhost:8000/api/orders/3316188865004018566/warehouse-photo --output test.jpg
open test.jpg  # macOS
# или
xdg-open test.jpg  # Linux
```

## 📊 Формат данных

### В базе данных:

```sql
SELECT 
  order_id,
  tracking_number,
  received_at_warehouse,
  warehouse_photo_path
FROM orders
WHERE warehouse_photo_path IS NOT NULL;
```

### Пример результата:

| order_id | tracking_number | received_at_warehouse | warehouse_photo_path |
|----------|-----------------|----------------------|---------------------|
| 3316188865004018566 | 435301476185280 | 1 | 435301476185280_20260806_225130.jpg |

### В API response (to_dict):

```json
{
  "order_id": "3316188865004018566",
  "tracking_number": "435301476185280",
  "received_at_warehouse": true,
  "warehouse_photo_path": "435301476185280_20260806_225130.jpg",
  ...
}
```

## 🎨 Стилизация

Фото на веб-интерфейсе:
- **Размер:** 60x60 пикселей
- **Рамка:** 2px solid #28a745 (зеленый)
- **Border-radius:** 4px
- **Object-fit:** cover
- **Cursor:** pointer (при наведении)

## 🔄 Откат изменений (если нужно)

Если нужно убрать функционал:

```bash
# 1. Удалить колонку из БД
python -c "
from backend.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE orders DROP COLUMN warehouse_photo_path'))
    conn.commit()
"

# 2. Откатить изменения в коде
git checkout backend/models.py
git checkout backend/app.py
git checkout backend/telegram_bot/handlers.py
git checkout frontend/templates/index.html
```

## 🚀 Готово!

Теперь система полностью интегрирована:
- ✅ Бот сохраняет фото и путь в БД
- ✅ API отдает фото по запросу
- ✅ Веб-интерфейс показывает миниатюры
- ✅ Клик открывает полное изображение

**Протестируйте прямо сейчас:**

1. Запустите бота: `python start_telegram_bot.py`
2. Отправьте фото + трек-номер
3. Откройте веб-интерфейс: http://localhost:8000
4. Увидите фото в таблице!

🎉 **Полная интеграция завершена!**
