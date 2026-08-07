# 🚀 Быстрый старт Telegram бота

## 📝 За 3 минуты до запуска

### Шаг 1: Получите токен бота (2 минуты)

1. Откройте Telegram и найдите [@BotFather](https://t.me/botfather)
2. Отправьте команду: `/newbot`
3. Введите имя бота: `MySyte Warehouse Bot`
4. Введите username: `mysyte_warehouse_bot` (или любой доступный)
5. Скопируйте токен (выглядит так: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Шаг 2: Добавьте токен в .env (30 секунд)

Откройте файл `.env` и замените:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

На ваш токен:
```bash
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Шаг 3: Запустите бота (30 секунд)

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
Bot username: @mysyte_warehouse_bot
Waiting for messages...
```

## ✅ Готово! Теперь используйте бота

1. Найдите вашего бота в Telegram: `@mysyte_warehouse_bot`
2. Отправьте `/start`
3. Отправьте фото товара 📸
4. Отправьте трек-номер: `435301476185280`
5. Получите подтверждение ✅

## 🧪 Тестирование

Проверьте настройку перед запуском:
```bash
python test_bot_setup.py
```

Должно показать:
```
Зависимости          ✅ PASSED
Конфигурация         ✅ PASSED
База данных          ✅ PASSED
Парсер               ✅ PASSED
Обработчики          ✅ PASSED

🎉 Все тесты пройдены! Бот готов к запуску.
```

## 📦 Примеры трек-номеров из вашей БД

Для тестирования можете использовать эти реальные трек-номера:
- `435301476185280`
- `15811880672`
- `435276498014633`
- `113137930002`

## 🆘 Помощь

**Проблема:** "TELEGRAM_BOT_TOKEN not found"
- **Решение:** Добавьте токен от @BotFather в файл `.env`

**Проблема:** "Трек-номер не найден"
- **Решение:** Сначала синхронизируйте заказы: `python update_tracking_numbers.py`

**Проблема:** "Module not found"
- **Решение:** Установите зависимости: `pip install -r requirements.txt`

## 📖 Полная документация

См. [TELEGRAM_BOT_GUIDE.md](TELEGRAM_BOT_GUIDE.md) для подробной информации.
