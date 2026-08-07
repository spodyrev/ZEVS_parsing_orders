# 🚀 Telegram Bot - Шпаргалка

## ⚡ Быстрые команды

### Запуск
```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate
python start_telegram_bot.py
```

### Остановка
```
Ctrl + C
```

### Тестирование настройки
```bash
python test_bot_setup.py
```

## 🔑 Настройка (первый раз)

1. **Получить токен**
   - Telegram → @BotFather
   - `/newbot`
   - Скопировать токен

2. **Добавить в .env**
   ```bash
   TELEGRAM_BOT_TOKEN=1234567890:ABCdef...
   ```

3. **Запустить**
   ```bash
   python start_telegram_bot.py
   ```

## 💬 Использование в Telegram

### Процесс получения товара
1. Отправить фото 📸
2. Отправить трек-номер (например: `435301476185280`)
3. Получить подтверждение ✅

### Команды бота
- `/start` - начало работы
- `/help` - справка

## 🔍 Форматы трек-номеров

| Формат | Пример | Regex |
|--------|--------|-------|
| Числовой | `79023797293946` | `\d{10,20}` |
| China Post | `LP123456789CN` | `[A-Z]{2}\d{9,13}[A-Z]{2}` |
| SF Express | `SF1234567890123` | `SF\d{13}` |
| EMS China | `EA123456789CN` | `E[A-Z0-9]{9,13}CN` |

## 📁 Где что лежит

```
MySyte/
├── start_telegram_bot.py      # Запуск
├── test_bot_setup.py          # Тестирование
├── backend/telegram_bot/       # Код бота
│   ├── bot.py
│   ├── handlers.py
│   ├── config.py
│   └── tracking_parser.py
├── warehouse_photos/           # Фото (создается автоматически)
│   └── {tracking}_{date}.jpg
├── logs/                       # Логи
│   └── telegram_bot_*.log
└── .env                        # Токен здесь!
```

## 🐛 Решение проблем

### Бот не запускается
```bash
# Проверить токен
grep TELEGRAM_BOT_TOKEN .env

# Проверить зависимости
pip list | grep telegram

# Переустановить
pip install --upgrade python-telegram-bot
```

### Трек-номер не найден
```bash
# Проверить БД
python test_bot_setup.py

# Обновить трек-номера
python update_tracking_numbers.py
```

### Посмотреть логи
```bash
# Сегодняшние
tail -f logs/telegram_bot_$(date +%Y-%m-%d).log

# Последние ошибки
grep ERROR logs/telegram_bot_*.log | tail -20

# Последние обработанные
grep "marked as received" logs/telegram_bot_*.log | tail -10
```

## 📊 Проверка работы

### В базе данных
```bash
python -c "
from backend.database import SessionLocal
from backend.models import Order
db = SessionLocal()
received = db.query(Order).filter(Order.received_at_warehouse == 1).count()
print(f'Получено на складе: {received}')
"
```

### Фотографии
```bash
ls -lh warehouse_photos/*.jpg | tail -10
```

### Статус бота
```bash
ps aux | grep start_telegram_bot
```

## 🔄 Обновление

```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate

# Обновить код (если изменили)
git pull

# Обновить зависимости
pip install -r requirements.txt --upgrade

# Перезапустить
# Ctrl+C в окне с ботом
python start_telegram_bot.py
```

## 🚀 Production

### Запуск в фоне
```bash
nohup python start_telegram_bot.py > bot.log 2>&1 &

# Проверить
ps aux | grep start_telegram_bot

# Остановить
pkill -f start_telegram_bot.py
```

### Systemd (Linux)
```bash
# Создать service
sudo nano /etc/systemd/system/mysyte-bot.service

# Запустить
sudo systemctl start mysyte-bot
sudo systemctl enable mysyte-bot

# Статус
sudo systemctl status mysyte-bot
```

## 📞 Справка

- 📖 Полное руководство: `TELEGRAM_BOT_GUIDE.md`
- 🚀 Быстрый старт: `TELEGRAM_BOT_QUICKSTART.md`
- 📝 Детали реализации: `IMPLEMENTATION_SUMMARY.md`

## 💡 Полезные команды

### Python shell для тестирования
```python
# Тест парсера
from backend.telegram_bot.tracking_parser import TrackingNumberParser
TrackingNumberParser.extract_first_tracking_number("Получен 79023797293946")
# → '79023797293946'

# Проверка БД
from backend.database import SessionLocal
from backend.models import Order
db = SessionLocal()
order = db.query(Order).filter(Order.tracking_number == "435301476185280").first()
print(f"Получен: {bool(order.received_at_warehouse)}")
```

### Очистка временных файлов
```bash
# Удалить temp фото
rm warehouse_photos/temp_*.jpg

# Очистить старые логи (>30 дней)
find logs -name "telegram_bot_*.log" -mtime +30 -delete
```

## ✅ Чеклист запуска

- [ ] Получил токен от @BotFather
- [ ] Добавил TELEGRAM_BOT_TOKEN в .env
- [ ] Запустил `python test_bot_setup.py` - все ✅
- [ ] Запустил `python start_telegram_bot.py`
- [ ] Отправил `/start` боту в Telegram
- [ ] Протестировал с реальным трек-номером
- [ ] Проверил warehouse_photos/ - фото появилось
- [ ] Проверил БД - received_at_warehouse = 1

## 🎉 Готово!

Теперь склад может отправлять фото и номера прямо в Telegram, а система автоматически всё обработает!
