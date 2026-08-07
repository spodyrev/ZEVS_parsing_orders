# Исправление обработки нескольких фото

## Проблема
При отправке 5 фотографий с одним трек-номером бот обрабатывал только первое фото.

## Решение
Изменена логика обработки медиа-групп в `backend/telegram_bot/handlers.py`:

### Что было:
- Каждое фото в группе запускало свою обработку после задержки в 1 секунду
- Первое фото успевало обработаться и удалить группу до прихода остальных

### Что стало:
- Каждое новое фото **отменяет предыдущую задачу** обработки
- Создается новая задача с задержкой в 2 секунды
- Обработка происходит только после того, как прошло 2 секунды с момента получения **последнего** фото
- Все фото обрабатываются вместе

### Как это работает:
1. Фото 1 → планируем обработку через 2 секунды
2. Фото 2 → отменяем предыдущую задачу, планируем новую через 2 секунды
3. Фото 3 → отменяем, планируем новую
4. Фото 4 → отменяем, планируем новую
5. Фото 5 → отменяем, планируем новую
6. **Через 2 секунды после фото 5** → обрабатываем все 5 фото вместе

## Как запустить бота с исправлениями

### 1. Убедитесь, что FastAPI сервер запущен
```bash
cd /Users/macprospodyrev/Projects/MySyte/backend
source ../venv/bin/activate
python3 app.py
```

### 2. В новом терминале запустите бота
```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate
python3 start_telegram_bot.py
```

Вы должны увидеть:
```
✅ Telegram Bot Started Successfully
🤖 Bot: @...
📱 Ready to receive messages!
```

## Как протестировать

### Тест 1: Одно фото с одним трек-номером
1. Отправьте одно фото с подписью: `773432543923485`
2. Бот должен ответить:
   ```
   📦 Обработано номеров: 1
   📸 Сохранено фото: 1
   ✅ Успешно: 1
   ```

### Тест 2: Пять фото с одним трек-номером (основной тест)
1. Выберите 5 фотографий в Telegram
2. Добавьте подпись: `773432543923485`
3. Отправьте все вместе
4. Бот должен подождать ~2 секунды после получения всех фото
5. Бот должен ответить:
   ```
   📦 Обработано номеров: 1
   📸 Сохранено фото: 5
   ✅ Успешно: 1
   ```

### Тест 3: Несколько фото с несколькими трек-номерами
1. Выберите 3 фотографии
2. Добавьте подпись: `773432543923485 331335832954713`
3. Отправьте
4. Бот должен ответить:
   ```
   📦 Обработано номеров: 2
   📸 Сохранено фото: 6 (по 3 для каждого заказа)
   ✅ Успешно: 2
   ```

## Проверка сохраненных фото

### В базе данных:
```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate
python3
```

```python
from backend.database import SessionLocal
from backend.models import Order
import json

db = SessionLocal()
order = db.query(Order).filter(Order.tracking_number == "773432543923485").first()
if order:
    photos = json.loads(order.warehouse_photo_path)
    print(f"Количество фото: {len(photos)}")
    print("Файлы:")
    for photo in photos:
        print(f"  - {photo}")
```

### На портале:
1. Откройте http://127.0.0.1:8000
2. Найдите заказ `773432543923485`
3. Должен отображаться бейдж `+5` (если 5 фото)
4. Нажмите на фото
5. Откроется галерея с навигацией
6. Стрелками (или клавишами ← →) можно листать все 5 фото

## Логи

Бот пишет подробные логи:
```
Media group {id}: added photo 1, caption: True
Cancelled previous processing task for media group {id}
Scheduled processing for media group {id} after delay
Media group {id}: added photo 2, caption: False
...
Processing media group {id} with 5 photos
Found 1 tracking numbers: ['773432543923485']
Photo copied to: .../773432543923485_20260806_225130_1.jpg
Photo copied to: .../773432543923485_20260806_225130_2.jpg
...
```

## Изменения в коде

### Файл: `backend/telegram_bot/handlers.py`

1. **Добавлены новые структуры данных:**
```python
media_group_tasks: Dict[str, asyncio.Task] = {}
```

2. **Добавлена функция обработки медиа-группы:**
```python
async def process_media_group(media_group_id: str, message) -> None:
    # Ждет 2 секунды, собирает все фото, обрабатывает
```

3. **Изменена логика в `photo_handler`:**
```python
# Отменяем предыдущую задачу
if media_group_id in media_group_tasks:
    media_group_tasks[media_group_id].cancel()

# Создаем новую задачу с задержкой
task = asyncio.create_task(process_media_group(media_group_id, message))
media_group_tasks[media_group_id] = task
```

## Дата исправления
6 августа 2026, 23:14 UTC-3
