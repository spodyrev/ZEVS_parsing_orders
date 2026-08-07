# Система аутентификации MySyte

## Обзор

В проект добавлена полноценная система аутентификации через Telegram с админ-панелью для управления пользователями.

## Что было реализовано

### 1. Аутентификация через Telegram Login Widget

✅ **Официальный виджет Telegram** - безопасная OAuth аутентификация
✅ **JWT токены** - для управления сессиями (срок действия 7 дней)
✅ **Валидация подписи** - проверка данных от Telegram согласно официальной документации
✅ **HttpOnly cookies** - защита от XSS атак

### 2. Модель данных

**Таблица `users` в БД:**
- `telegram_id` - уникальный ID из Telegram (обязательное)
- `phone_number` - номер телефона (опциональное)
- `first_name`, `last_name` - имя из Telegram
- `username` - username из Telegram
- `photo_url` - аватар пользователя
- `is_admin` - флаг администратора (0 или 1)
- `is_active` - флаг активности (0 или 1)
- `created_at` - дата создания
- `last_login` - последний вход

### 3. Страницы и endpoints

#### Публичные страницы:
- `GET /login` - страница входа с Telegram Widget
- `GET /api/auth/telegram/callback` - обработка авторизации от Telegram

#### Защищенные страницы:
- `GET /` - главная (список заказов)
- `GET /archive` - архив заказов
- `GET /trash` - корзина
- `GET /admin` - админ-панель (только для администраторов)

#### API endpoints:
- `GET /api/auth/me` - информация о текущем пользователе
- `GET /api/auth/logout` - выход из системы
- `GET /api/admin/users` - список пользователей (admin)
- `POST /api/admin/users` - создать пользователя (admin)
- `GET /api/admin/users/{id}` - получить пользователя (admin)
- `PUT /api/admin/users/{id}` - обновить пользователя (admin)
- `DELETE /api/admin/users/{id}` - удалить пользователя (admin)
- `POST /api/admin/users/{id}/toggle-active` - активировать/деактивировать (admin)

### 4. Админ-панель

**Функционал:**
- ✅ Просмотр всех пользователей
- ✅ Добавление новых пользователей (по Telegram ID)
- ✅ Редактирование прав доступа
- ✅ Активация/деактивация пользователей
- ✅ Удаление пользователей
- ✅ Статистика (всего, активных, админов)
- ✅ Красивый UI в стиле проекта

### 5. Безопасность

✅ **JWT токены** с подписью SECRET_KEY
✅ **Проверка подписи Telegram** - защита от подделки данных
✅ **CORS middleware** - ограничение доступа по доменам
✅ **HttpOnly cookies** - защита от XSS
✅ **SameSite=lax** - защита от CSRF
✅ **Проверка активности** - деактивированные пользователи не могут войти
✅ **Exception handler** - автоматический редирект на /login при 401

### 6. Файлы для деплоя

✅ **Dockerfile** - контейнеризация приложения
✅ **mysyte.service** - systemd service для веб-приложения
✅ **telegram-bot.service** - systemd service для Telegram бота
✅ **nginx.conf** - конфигурация Nginx с SSL
✅ **.dockerignore** - исключения для Docker
✅ **README_DEPLOYMENT.md** - полное руководство по деплою

### 7. Утилиты

✅ **create_admin.py** - интерактивный скрипт создания администратора
✅ **Обновленный .env.example** - с подробной документацией всех переменных

## Архитектура

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Browser   │ HTTPS   │    Nginx     │  Proxy  │   FastAPI    │
│  (Telegram  ├────────►│  (SSL/HTTPS) ├────────►│   (app.py)   │
│   Widget)   │         │ Reverse Proxy│         │              │
└─────────────┘         └──────────────┘         └──────┬───────┘
                                                          │
                                                          │
                                                   ┌──────▼───────┐
                                                   │   SQLite     │
                                                   │  (orders.db) │
                                                   │   - orders   │
                                                   │   - users    │
                                                   └──────────────┘
```

## Как это работает

### Процесс авторизации:

1. **Пользователь заходит на сайт** → перенаправляется на `/login`
2. **Нажимает "Login with Telegram"** → Telegram виджет
3. **Авторизуется в Telegram** → Telegram возвращает данные
4. **Backend проверяет подпись** → `verify_telegram_auth()`
5. **Ищет пользователя в БД** → по `telegram_id`
6. **Если найден и активен** → создает JWT токен
7. **Устанавливает cookie** → `access_token` с токеном
8. **Перенаправляет на главную** → пользователь авторизован

### Проверка на защищенных страницах:

1. **Запрос к защищенному роуту** → например `/` или `/admin`
2. **Dependency `get_current_user()`** → извлекает токен из cookie
3. **Проверяет JWT токен** → валидность и срок действия
4. **Находит пользователя в БД** → по `telegram_id` из токена
5. **Проверяет `is_active`** → пользователь должен быть активен
6. **Для админки проверяет `is_admin`** → дополнительная проверка
7. **Возвращает объект User** → или выбрасывает 401/403

## Использование

### Локальное тестирование

```bash
# 1. Установите зависимости
pip install -r requirements.txt

# 2. Настройте .env
cp .env.example .env
nano .env  # Установите SECRET_KEY и TELEGRAM_BOT_TOKEN

# 3. Создайте первого администратора
python create_admin.py

# 4. Запустите приложение
python backend/app.py

# 5. Откройте в браузере
open http://localhost:8000/login
```

### Создание пользователей

**Вариант 1: Через админ-панель** (рекомендуется)
1. Войдите как администратор
2. Откройте http://localhost:8000/admin
3. Нажмите "Добавить пользователя"
4. Введите Telegram ID сотрудника

**Вариант 2: Через скрипт**
```bash
python create_admin.py
# Выберите пункт 1
```

### Получение Telegram ID

Пользователь должен:
1. Открыть Telegram
2. Найти бота [@userinfobot](https://t.me/userinfobot)
3. Отправить `/start`
4. Скопировать свой ID

## Деплой

### Быстрый деплой на Render.com (бесплатно)

1. Загрузите проект на GitHub
2. Зайдите на [render.com](https://render.com)
3. Создайте Web Service из вашего репозитория
4. Добавьте переменные окружения
5. Создайте Persistent Disk для `/data`
6. Деплой!

**Подробная инструкция:** см. [README_DEPLOYMENT.md](README_DEPLOYMENT.md)

### Деплой на VPS

```bash
# Клонируйте проект
git clone <repo> /opt/mysyte

# Установите зависимости
cd /opt/mysyte
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройте .env
cp .env.example .env
nano .env

# Создайте администратора
python create_admin.py

# Установите systemd services
sudo cp mysyte.service telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mysyte telegram-bot
sudo systemctl start mysyte telegram-bot

# Настройте Nginx
sudo cp nginx.conf /etc/nginx/sites-available/mysyte
sudo ln -s /etc/nginx/sites-available/mysyte /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Настройте SSL
sudo certbot --nginx -d yourdomain.com
```

## Безопасность в production

### Обязательно измените:

1. **SECRET_KEY** - уникальный криптографически стойкий ключ
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **DEBUG=False** - отключите debug mode

3. **ALLOWED_ORIGINS** - укажите реальные домены
   ```bash
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. **Права доступа к файлам**
   ```bash
   sudo chown -R www-data:www-data /opt/mysyte
   chmod 600 /opt/mysyte/.env
   ```

5. **Firewall**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

## Troubleshooting

### "Invalid Telegram auth signature"
- Проверьте `TELEGRAM_BOT_TOKEN` в `.env`
- Убедитесь что время на сервере синхронизировано

### "User not found"
- Создайте пользователя через `create_admin.py`
- Или добавьте через админ-панель

### 401 Unauthorized
- Очистите cookies браузера
- Проверьте что `SECRET_KEY` одинаковый при создании токена и проверке
- Убедитесь что пользователь активен (`is_active=1`)

### Админ-панель недоступна
- Убедитесь что у пользователя `is_admin=1`
- Проверьте права через `python create_admin.py` → пункт 2

## Roadmap (будущие улучшения)

- [ ] Rate limiting (защита от брутфорса)
- [ ] Двухфакторная аутентификация
- [ ] Логи входов пользователей
- [ ] Роли пользователей (viewer, editor, admin)
- [ ] Email уведомления
- [ ] API токены для интеграций
- [ ] OAuth для других провайдеров (Google, GitHub)

## Технологии

- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM
- **python-jose** - JWT токены
- **Telegram Login Widget** - OAuth аутентификация
- **Bootstrap 5** - UI фреймворк
- **Nginx** - reverse proxy
- **Let's Encrypt** - SSL сертификаты

---

**Система готова к использованию!** 🚀

Для получения дополнительной информации см.:
- [README_DEPLOYMENT.md](README_DEPLOYMENT.md) - руководство по деплою
- [START_HERE.md](START_HERE.md) - общая информация о проекте
