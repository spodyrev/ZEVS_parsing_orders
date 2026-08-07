# 🤖 Telegram Bot для отслеживания товаров на складе

## 📋 Описание

Telegram бот автоматически отслеживает получение товаров на складе. Когда склад отправляет фото и трек-номер полученного товара, бот:
- Сохраняет фотографию в файловую систему
- Находит заказ в базе данных по трек-номеру
- Отмечает заказ как полученный на складе (`received_at_warehouse = 1`)
- Отправляет подтверждение с деталями заказа

## 🚀 Быстрый старт

### 1. Создание бота в Telegram

1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Введите имя бота (например: "MySyte Warehouse Bot")
   - Введите username бота (например: "mysyte_warehouse_bot")
4. BotFather вышлет вам токен вида: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Настройка токена

Добавьте токен в файл `.env`:

```bash
# Откройте .env файл
nano .env

# Добавьте или обновите строку:
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
```

### 3. Запуск бота

```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate
python start_telegram_bot.py
```

Вы увидите сообщение:
```
🤖 Telegram Bot для отслеживания товаров на складе
============================================================

2026-08-06 22:00:00 | INFO     | Bot started successfully!
2026-08-06 22:00:00 | INFO     | Bot username: @your_bot_username
2026-08-06 22:00:00 | INFO     | Waiting for messages...
```

## 📱 Использование бота

### Основной процесс

1. **Отправьте фото товара** 📸
   - Бот ответит: "📸 Фото получено! Теперь отправьте трек-номер товара."

2. **Отправьте трек-номер** 📦
   - Просто напишите номер: `79023797293946`
   - Или с текстом: "Получен товар 79023797293946"

3. **Получите подтверждение** ✅
   ```
   ✅ Товар отмечен как полученный на складе
   
   Трек-номер: 79023797293946
   ID заказа: 3316188865004009384
   Описание: Смартфон xiaomi redmi note 12
   Фото: Сохранено (79023797293946_20260806_220530.jpg)
   
   Дата получения: 2026-08-06 22:05:30
   ```

### Поддерживаемые форматы трек-номеров

- **Числовые:** `79023797293946`
- **China Post:** `LP123456789CN`
- **SF Express:** `SF1234567890123`
- **EMS China:** `EA123456789CN`
- **Общий формат:** любые 10-20 символов (цифры и латинские буквы)

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Приветствие и инструкция |
| `/help` | Подробная справка |

## 🔧 Технические детали

### Структура проекта

```
MySyte/
├── backend/
│   └── telegram_bot/
│       ├── __init__.py
│       ├── bot.py              # Основная логика
│       ├── config.py           # Конфигурация
│       ├── handlers.py         # Обработчики сообщений
│       └── tracking_parser.py  # Парсинг трек-номеров
├── warehouse_photos/           # Сохраненные фото
│   └── {tracking_number}_{timestamp}.jpg
├── logs/
│   └── telegram_bot_*.log      # Логи бота
└── start_telegram_bot.py       # Скрипт запуска
```

### Сохранение фотографий

Фотографии сохраняются в директории `warehouse_photos/` с именами:
```
79023797293946_20260806_153045.jpg
LP123456789CN_20260806_154123.jpg
```

Формат имени: `{трек-номер}_{дата}_{время}.jpg`

### Обновление базы данных

При получении трек-номера бот:

```sql
UPDATE orders 
SET received_at_warehouse = 1, 
    updated_at = NOW()
WHERE tracking_number = '79023797293946';
```

## 🐛 Решение проблем

### Бот не запускается

**Проблема:** `TELEGRAM_BOT_TOKEN not found`

**Решение:**
1. Проверьте файл `.env`
2. Убедитесь, что токен добавлен правильно
3. Нет лишних пробелов или кавычек

**Проблема:** `ModuleNotFoundError: No module named 'telegram'`

**Решение:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Трек-номер не найден

**Проблема:** Бот пишет "❌ Трек-номер не найден в базе данных"

**Возможные причины:**
1. Заказ еще не синхронизирован с Taobao
   - Запустите синхронизацию: `python update_tracking_numbers.py`
2. Трек-номер указан неверно
   - Проверьте написание
3. Трек-номер пустой в БД
   - Обновите трек-номера вручную

### Проверка трек-номеров в БД

```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate

python -c "
from backend.database import SessionLocal
from backend.models import Order

db = SessionLocal()
orders = db.query(Order).filter(Order.tracking_number.isnot(None)).all()
print(f'Заказов с трек-номером: {len(orders)}')
for order in orders[:5]:
    print(f'{order.order_id}: {order.tracking_number}')
"
```

## 📊 Просмотр логов

Логи сохраняются в `logs/telegram_bot_YYYY-MM-DD.log`

```bash
# Последние 50 строк
tail -n 50 logs/telegram_bot_$(date +%Y-%m-%d).log

# Следить за логами в реальном времени
tail -f logs/telegram_bot_$(date +%Y-%m-%d).log

# Поиск ошибок
grep ERROR logs/telegram_bot_*.log
```

## 🔐 Безопасность

### Текущая конфигурация

- ✅ Бот принимает сообщения от любых пользователей
- ✅ Нет аутентификации (как указано в требованиях)

### Для production (опционально)

Если нужно ограничить доступ, можно добавить whitelist в `.env`:

```bash
TELEGRAM_ALLOWED_USERS=123456789,987654321
TELEGRAM_ALLOWED_CHATS=-1001234567890
```

И модифицировать `handlers.py` для проверки `update.message.from_user.id`.

## 🚀 Запуск в production

### Systemd service (Linux)

Создайте `/etc/systemd/system/mysyte-telegram-bot.service`:

```ini
[Unit]
Description=MySyte Telegram Warehouse Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/MySyte
Environment="PATH=/path/to/MySyte/venv/bin"
ExecStart=/path/to/MySyte/venv/bin/python start_telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запуск:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mysyte-telegram-bot
sudo systemctl start mysyte-telegram-bot
sudo systemctl status mysyte-telegram-bot
```

### Docker (опционально)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "start_telegram_bot.py"]
```

## 📈 Мониторинг

### Проверка статуса

```bash
# Количество обработанных товаров
grep "marked as received" logs/telegram_bot_*.log | wc -l

# Ошибки за последний час
grep ERROR logs/telegram_bot_$(date +%Y-%m-%d).log | tail -20

# Последние обработанные трек-номера
grep "Found tracking number" logs/telegram_bot_$(date +%Y-%m-%d).log | tail -10
```

## 🔄 Обновление бота

```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate

# Обновить зависимости
pip install -r requirements.txt --upgrade

# Перезапустить бота
# Ctrl+C в терминале с ботом, затем:
python start_telegram_bot.py
```

## 💡 Полезные советы

1. **Запуск в фоне (macOS/Linux):**
   ```bash
   nohup python start_telegram_bot.py > bot.log 2>&1 &
   ```

2. **Проверка процесса:**
   ```bash
   ps aux | grep start_telegram_bot
   ```

3. **Остановка фонового процесса:**
   ```bash
   pkill -f start_telegram_bot.py
   ```

4. **Тестирование парсера:**
   ```python
   from backend.telegram_bot.tracking_parser import TrackingNumberParser
   
   text = "Получен товар 79023797293946"
   number = TrackingNumberParser.extract_first_tracking_number(text)
   print(number)  # 79023797293946
   ```

## ❓ FAQ

**Q: Можно ли обрабатывать несколько товаров одновременно?**  
A: Да, но каждую пару (фото + трек-номер) нужно отправлять отдельно.

**Q: Что если отправить только трек-номер без фото?**  
A: Бот обработает и отметит заказ, просто не будет сохранено фото.

**Q: Можно ли просматривать фото через веб-интерфейс?**  
A: Сейчас фото сохраняются только в файловую систему. Интеграция с веб-интерфейсом - в планах на будущее.

**Q: Бот работает только с одним чатом?**  
A: Нет, бот может работать с любыми чатами и пользователями.

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/telegram_bot_*.log`
2. Убедитесь, что бот запущен
3. Проверьте правильность трек-номера в БД
4. Попробуйте команду `/help` в боте

## 🎉 Готово!

Теперь ваш Telegram бот готов к работе и будет автоматически отслеживать получение товаров на складе!
