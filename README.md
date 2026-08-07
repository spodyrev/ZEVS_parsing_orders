# ZEVS - Система отслеживания заказов

Веб-приложение для отслеживания заказов из Китая с интеграцией Telegram и аутентификацией.

## Возможности

- 🔐 Авторизация через Telegram
- 📦 Отслеживание заказов из Taobao
- 👥 Управление пользователями (админ-панель)
- 🤖 Telegram бот для складского учета
- 📱 Адаптивный веб-интерфейс

## Технологии

- **Backend:** FastAPI, SQLAlchemy, Python 3.9+
- **Database:** SQLite (для разработки), PostgreSQL (для продакшн)
- **Auth:** JWT, Telegram Login Widget
- **Frontend:** Jinja2, Bootstrap 5
- **Deployment:** Render.com, Docker

## Быстрый старт

### Локальная разработка

```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/MySyte.git
cd MySyte

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt

# Настройте .env файл
cp .env.example .env
# Отредактируйте .env и добавьте ваши токены

# Инициализируйте БД
python -c "from backend.database import init_db; init_db()"

# Создайте администратора
python create_admin.py

# Запустите приложение
python backend/app.py
```

Приложение будет доступно по адресу: http://127.0.0.1:8000

## Деплой на Render.com

### Автоматический деплой

1. Создайте аккаунт на [Render.com](https://render.com)
2. Подключите ваш GitHub репозиторий
3. Render автоматически обнаружит `render.yaml` и задеплоит приложение
4. Настройте переменные окружения:
   - `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
   - `GEMINI_API_KEY` - API ключ Google Gemini (опционально)
   - Остальные переменные генерируются автоматически

5. После деплоя настройте домен в @BotFather:
   - `/setdomain`
   - Выберите вашего бота
   - Введите домен: `your-app.onrender.com`

### Ручной деплой

См. подробные инструкции в `README_DEPLOYMENT.md`

## Документация

- `START_HERE.md` - Общее описание проекта
- `SETUP_GUIDE.md` - Подробная инструкция по настройке
- `README_DEPLOYMENT.md` - Инструкции по деплою
- `TELEGRAM_BOT_GUIDE.md` - Настройка Telegram бота
- `AUTHENTICATION_SYSTEM.md` - Описание системы аутентификации

## Структура проекта

```
MySyte/
├── backend/
│   ├── app.py              # Главное приложение FastAPI
│   ├── models.py           # Модели БД
│   ├── database.py         # Настройка БД
│   ├── auth.py             # Аутентификация
│   ├── config.py           # Конфигурация
│   ├── scheduler.py        # Планировщик задач
│   ├── scraper/            # Парсинг Taobao
│   └── telegram_bot/       # Telegram бот
├── frontend/
│   ├── templates/          # HTML шаблоны
│   └── static/             # CSS, JS, изображения
├── requirements.txt        # Python зависимости
├── .env.example           # Пример конфигурации
└── render.yaml            # Конфиг для Render.com
```

## Переменные окружения

Основные переменные (см. `.env.example`):

- `SECRET_KEY` - Секретный ключ для JWT
- `TELEGRAM_BOT_TOKEN` - Токен Telegram бота
- `DATABASE_URL` - URL базы данных
- `ALLOWED_ORIGINS` - CORS настройки
- `GEMINI_API_KEY` - API ключ для переводов (опционально)

## Безопасность

- ✅ JWT токены для сессий
- ✅ Telegram Login Widget для аутентификации
- ✅ CORS настройки
- ✅ Rate limiting
- ✅ Проверка подлинности Telegram данных

## Лицензия

MIT

## Автор

ZEVS Team

## Поддержка

Telegram: @ZEVS_Parsing_orders_bot
