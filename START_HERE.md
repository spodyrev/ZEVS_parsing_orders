# 🚀 НАЧАТЬ ЗДЕСЬ - Telegram бот готов!

## ✅ Бот настроен и работает!

**Ваш бот:** [@ZEVS_Parsing_orders_bot](https://t.me/ZEVS_Parsing_orders_bot)  
**Статус:** ✅ Подключен к Telegram API

## 📱 Как начать использовать (1 минута)

### Шаг 1: Запустите бота

Откройте терминал и выполните:

```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate
python start_telegram_bot.py
```

Вы увидите:
```
🤖 Telegram Bot для отслеживания товаров на складе
============================================================

Bot started successfully!
Bot username: @ZEVS_Parsing_orders_bot
Bot name: ZEVS Parsing orders
Bot ID: 8986805321
Waiting for messages...
```

### Шаг 2: Откройте бота в Telegram

Нажмите на эту ссылку: **https://t.me/ZEVS_Parsing_orders_bot**

Или найдите в поиске Telegram: `@ZEVS_Parsing_orders_bot`

### Шаг 3: Отправьте `/start`

Бот ответит приветствием и инструкцией.

### Шаг 4: Протестируйте

**Отправьте боту:**

1. Любое фото 📸
2. Трек-номер для теста: `435301476185280`

**Бот ответит:**
```
✅ Товар отмечен как полученный на складе

Трек-номер: 435301476185280
ID заказа: 3316188865004018566
Описание: [описание товара]
Фото: Сохранено

Дата получения: 2026-08-06 22:51:30
```

## 📦 Реальные трек-номера для тестирования

В вашей базе данных есть **24 заказа** с трек-номерами:

| Трек-номер | ID заказа | Статус |
|------------|-----------|--------|
| `435301476185280` | 3316188865004018566 | ⏳ Ожидает |
| `15811880672` | 3313358329547145777 | ✅ Получен |
| `435276498014633` | 3313526880203181787 | ✅ Получен |
| `113137930002` | 3313526880203045394 | ✅ Получен |

Используйте трек-номер со статусом ⏳ для первого теста.

## 🔄 Основной workflow

### Для склада:

1. **Получили товар?** → Откройте бота
2. **Сделайте фото товара** → Отправьте боту 📸
3. **Найдите трек-номер на упаковке** → Отправьте боту номер
4. **Готово!** ✅ Бот автоматически:
   - Найдет заказ в системе
   - Сохранит фото
   - Отметит товар как полученный
   - Пришлет подтверждение

### Что происходит в системе:

```
Telegram Bot → Поиск в БД → Обновление статуса → Сохранение фото
```

- **База данных:** `received_at_warehouse = 1`
- **Фото:** `warehouse_photos/435301476185280_20260806_225130.jpg`
- **Веб-интерфейс:** http://localhost:8000 (покажет обновленный статус)

## 📂 Где что находится

```
/Users/macprospodyrev/Projects/MySyte/
├── start_telegram_bot.py          ← ЗАПУСК БОТА
├── test_bot_connection.py         ← Проверка подключения
├── test_bot_setup.py              ← Тест настройки
├── warehouse_photos/               ← Фото товаров (автоматически)
│   └── 435301476185280_*.jpg
├── logs/                           ← Логи бота
│   └── telegram_bot_2026-08-06.log
└── backend/telegram_bot/           ← Код бота
    ├── bot.py
    ├── handlers.py
    ├── tracking_parser.py
    └── config.py
```

## 🛠️ Полезные команды

### Запуск/остановка

```bash
# Запустить
python start_telegram_bot.py

# Остановить
Ctrl + C

# Запустить в фоне (macOS/Linux)
nohup python start_telegram_bot.py > bot.log 2>&1 &

# Проверить запущен ли
ps aux | grep start_telegram_bot

# Остановить фоновый
pkill -f start_telegram_bot.py
```

### Проверка

```bash
# Тест подключения
python test_bot_connection.py

# Тест настройки
python test_bot_setup.py

# Логи в реальном времени
tail -f logs/telegram_bot_$(date +%Y-%m-%d).log

# Последние 50 строк логов
tail -n 50 logs/telegram_bot_$(date +%Y-%m-%d).log
```

### Статистика

```bash
# Сколько товаров получено
grep "marked as received" logs/telegram_bot_*.log | wc -l

# Последние обработанные трек-номера
grep "Found tracking number" logs/telegram_bot_*.log | tail -10

# Ошибки
grep ERROR logs/telegram_bot_*.log
```

## 📖 Документация

| Файл | Описание |
|------|----------|
| **START_HERE.md** | ← Вы здесь |
| [TELEGRAM_BOT_QUICKSTART.md](TELEGRAM_BOT_QUICKSTART.md) | Быстрый старт за 3 минуты |
| [TELEGRAM_BOT_GUIDE.md](TELEGRAM_BOT_GUIDE.md) | Полное руководство (336 строк) |
| [TELEGRAM_BOT_CHEATSHEET.md](TELEGRAM_BOT_CHEATSHEET.md) | Шпаргалка с командами |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Детали реализации |

## 🎯 Следующие шаги

### 1. Запустите бота (1 минута)
```bash
python start_telegram_bot.py
```

### 2. Протестируйте (2 минуты)
- Откройте https://t.me/ZEVS_Parsing_orders_bot
- Отправьте `/start`
- Отправьте фото
- Отправьте трек-номер: `435301476185280`

### 3. Проверьте результат (1 минута)
```bash
# Проверить БД
python -c "
from backend.database import SessionLocal
from backend.models import Order
db = SessionLocal()
order = db.query(Order).filter(Order.tracking_number == '435301476185280').first()
print(f'Получен на складе: {bool(order.received_at_warehouse)}')
"

# Проверить фото
ls -lh warehouse_photos/435301476185280_*.jpg
```

### 4. Начните использовать в работе!
- Дайте ссылку складу: https://t.me/ZEVS_Parsing_orders_bot
- Объясните процесс: фото → номер → готово
- Следите за логами для контроля

## 💡 Советы

1. **Запуск 24/7:** Используйте `nohup` или systemd для постоянной работы
2. **Мониторинг:** Периодически проверяйте логи
3. **Backup:** Фото в `warehouse_photos/` сохраняются навсегда
4. **База данных:** Веб-интерфейс показывает актуальную информацию

## ❓ Вопросы?

### Бот не отвечает?
- Проверьте что `python start_telegram_bot.py` запущен
- Посмотрите логи: `tail -f logs/telegram_bot_*.log`

### Трек-номер не найден?
- Синхронизируйте заказы: `python update_tracking_numbers.py`
- Проверьте написание номера

### Фото не сохраняется?
- Проверьте права на папку: `ls -ld warehouse_photos/`
- Посмотрите логи на ошибки

## 🎉 Готово!

Ваш Telegram бот **@ZEVS_Parsing_orders_bot** полностью настроен и готов к работе!

**Все работает:**
- ✅ Бот подключен к Telegram
- ✅ База данных доступна (30 заказов, 24 с трек-номерами)
- ✅ Парсер трек-номеров работает
- ✅ Фото сохраняются в warehouse_photos/
- ✅ Логирование настроено
- ✅ Документация готова

**Запустите прямо сейчас:**
```bash
python start_telegram_bot.py
```

**Тестовая ссылка:**
https://t.me/ZEVS_Parsing_orders_bot

Удачи! 🚀
