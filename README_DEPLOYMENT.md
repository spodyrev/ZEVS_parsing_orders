# Руководство по развертыванию MySyte

Полное руководство по деплою системы отслеживания заказов MySyte с Telegram аутентификацией.

## Содержание

1. [Быстрый старт (локальное тестирование)](#быстрый-старт)
2. [Деплой на бесплатный хостинг](#деплой-на-бесплатный-хостинг)
3. [Деплой на физический сервер](#деплой-на-физический-сервер)
4. [Настройка SSL сертификата](#настройка-ssl)
5. [Создание первого администратора](#создание-администратора)
6. [Резервное копирование](#резервное-копирование)
7. [Troubleshooting](#troubleshooting)

---

## Быстрый старт

### 1. Установка зависимостей

```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и настройте:

```bash
cp .env.example .env
nano .env
```

**Обязательные параметры для локального тестирования:**

```bash
SECRET_KEY=your-generated-secret-key  # Сгенерируйте: python -c "import secrets; print(secrets.token_urlsafe(32))"
TELEGRAM_BOT_TOKEN=8986805321:AAGRXSKolZU6snMB9xZ_tpRUW0RVm5FqR2E  # Ваш существующий токен
DEBUG=True
HOST=127.0.0.1
PORT=8000
```

### 3. Создание первого администратора

```bash
python create_admin.py
```

Следуйте инструкциям:
1. Получите ваш Telegram ID через бота [@userinfobot](https://t.me/userinfobot)
2. Введите Telegram ID в скрипт
3. Опционально введите номер телефона и имя

### 4. Запуск приложения

```bash
python backend/app.py
```

### 5. Первый вход

1. Откройте браузер: http://localhost:8000/login
2. Нажмите "Login with Telegram"
3. Авторизуйтесь через Telegram
4. Вы будете перенаправлены на главную страницу

### 6. Доступ к админ-панели

После входа откройте: http://localhost:8000/admin

Здесь вы можете:
- Добавлять новых пользователей
- Управлять правами доступа
- Активировать/деактивировать пользователей

---

## Деплой на бесплатный хостинг

### Вариант 1: Render.com (рекомендуется)

**Преимущества:**
- Бесплатный tier
- Автоматический деплой из GitHub
- SSL сертификат из коробки
- Persistent Disk для SQLite

**Шаги:**

#### 1. Подготовка репозитория

```bash
# Инициализируйте git, если еще не сделали
git init
git add .
git commit -m "Initial commit: MySyte with Telegram auth"

# Создайте репозиторий на GitHub и запушьте
git remote add origin https://github.com/yourusername/mysyte.git
git push -u origin main
```

#### 2. Создание сервиса на Render

1. Зайдите на [render.com](https://render.com) и войдите
2. Нажмите "New +" → "Web Service"
3. Подключите ваш GitHub репозиторий
4. Настройте сервис:

**Build Settings:**
```
Build Command: pip install -r requirements.txt
Start Command: uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```

**Environment:**
- Runtime: Python 3
- Region: выберите ближайший к вам

#### 3. Environment Variables

Добавьте переменные окружения в Render:

```bash
SECRET_KEY=<сгенерируйте новый секретный ключ>
TELEGRAM_BOT_TOKEN=8986805321:AAGRXSKolZU6snMB9xZ_tpRUW0RVm5FqR2E
DEBUG=False
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=https://your-app-name.onrender.com
DATABASE_URL=/data/orders.db
```

#### 4. Persistent Disk (важно!)

1. В настройках сервиса найдите "Disks"
2. Создайте новый диск:
   - Name: `data`
   - Mount Path: `/data`
   - Size: 1 GB (хватит для небольших проектов)

Это сохранит вашу SQLite базу данных между перезапусками.

#### 5. Создание администратора на Render

После деплоя выполните команду через Render Shell:

```bash
python create_admin.py
```

#### 6. Настройка Telegram Bot

Обновите webhook URL для бота (если используете):

```bash
curl -X POST "https://api.telegram.org/bot8986805321:AAGRXSKolZU6snMB9xZ_tpRUW0RVm5FqR2E/setWebhook?url=https://your-app-name.onrender.com/webhook"
```

### Вариант 2: Railway.app

**Преимущества:**
- 500 часов бесплатно
- Проще настройка
- Хороший UI

**Шаги:**

1. Зайдите на [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. Railway автоматически определит Python проект
5. Добавьте переменные окружения (аналогично Render)
6. Настройте команду запуска: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`

### Вариант 3: Fly.io

```bash
# Установите Fly CLI
curl -L https://fly.io/install.sh | sh

# Войдите
fly auth login

# Инициализируйте проект
fly launch

# Деплой
fly deploy
```

---

## Деплой на физический сервер

### Требования

- Ubuntu 20.04+ / Debian 11+
- Root или sudo доступ
- Минимум 1GB RAM
- Домен (опционально, для SSL)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3 python3-pip python3-venv nginx git

# Создание пользователя для приложения (опционально)
sudo useradd -m -s /bin/bash mysyte
sudo usermod -aG www-data mysyte
```

### Шаг 2: Клонирование проекта

```bash
# Клонируйте в /opt/mysyte
sudo mkdir -p /opt/mysyte
sudo chown $USER:$USER /opt/mysyte
cd /opt/mysyte
git clone https://github.com/yourusername/mysyte.git .

# Или скопируйте файлы вручную
scp -r /Users/macprospodyrev/Projects/MySyte/* user@your-server:/opt/mysyte/
```

### Шаг 3: Настройка виртуального окружения

```bash
cd /opt/mysyte
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 4: Настройка .env

```bash
cp .env.example .env
nano .env
```

**Production настройки:**

```bash
SECRET_KEY=<сгенерируйте уникальный ключ>
TELEGRAM_BOT_TOKEN=8986805321:AAGRXSKolZU6snMB9xZ_tpRUW0RVm5FqR2E
DEBUG=False
HOST=0.0.0.0
PORT=8000
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DATABASE_URL=sqlite:///./orders.db
```

### Шаг 5: Создание администратора

```bash
python create_admin.py
```

### Шаг 6: Настройка systemd сервисов

#### Веб-приложение:

```bash
sudo cp mysyte.service /etc/systemd/system/
sudo nano /etc/systemd/system/mysyte.service
```

Отредактируйте пути если нужно, затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mysyte
sudo systemctl start mysyte
sudo systemctl status mysyte
```

#### Telegram бот:

```bash
sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

### Шаг 7: Создание директорий для логов

```bash
sudo mkdir -p /var/log/mysyte
sudo chown www-data:www-data /var/log/mysyte
```

### Шаг 8: Настройка Nginx

```bash
sudo cp nginx.conf /etc/nginx/sites-available/mysyte
sudo nano /etc/nginx/sites-available/mysyte
```

**Замените `yourdomain.com` на ваш реальный домен!**

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/mysyte /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Настройка SSL

### С помощью Let's Encrypt (бесплатно)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение сертификата
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автоматическое обновление
sudo certbot renew --dry-run
```

Certbot автоматически:
- Получит SSL сертификат
- Обновит конфигурацию Nginx
- Настроит автоматическое обновление

### Проверка SSL

Откройте: https://yourdomain.com

Вы должны увидеть:
- Зеленый замок в браузере
- Страницу логина
- Telegram Login Widget работает

---

## Создание администратора

### Локально

```bash
python create_admin.py
```

### На сервере

```bash
ssh user@your-server
cd /opt/mysyte
source venv/bin/activate
python create_admin.py
```

### Через Python напрямую

```python
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/mysyte/backend')

from database import SessionLocal
from models import User
from datetime import datetime

db = SessionLocal()
admin = User(
    telegram_id="YOUR_TELEGRAM_ID",  # Получите через @userinfobot
    phone_number="+79001234567",
    first_name="Admin",
    is_admin=1,
    is_active=1,
    created_at=datetime.now()
)
db.add(admin)
db.commit()
print("✅ Admin created!")
db.close()
EOF
```

---

## Управление сервисами

### Просмотр статуса

```bash
sudo systemctl status mysyte
sudo systemctl status telegram-bot
```

### Перезапуск

```bash
sudo systemctl restart mysyte
sudo systemctl restart telegram-bot
```

### Просмотр логов

```bash
# Логи приложения
sudo tail -f /var/log/mysyte/app.log

# Логи бота
sudo tail -f /var/log/mysyte/telegram_bot.log

# Логи systemd
sudo journalctl -u mysyte -f
sudo journalctl -u telegram-bot -f
```

### Остановка

```bash
sudo systemctl stop mysyte
sudo systemctl stop telegram-bot
```

---

## Резервное копирование

### Автоматический backup скрипт

Создайте `/opt/mysyte/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/mysyte/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup базы данных
cp /opt/mysyte/orders.db "$BACKUP_DIR/orders_$DATE.db"

# Backup фотографий со склада
tar -czf "$BACKUP_DIR/photos_$DATE.tar.gz" /opt/mysyte/warehouse_photos/

# Удаление старых backup (старше 30 дней)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "✅ Backup completed: $DATE"
```

Сделайте исполняемым:

```bash
chmod +x /opt/mysyte/backup.sh
```

### Настройка автоматического backup через cron

```bash
sudo crontab -e
```

Добавьте:

```bash
# Backup каждый день в 3:00 ночи
0 3 * * * /opt/mysyte/backup.sh >> /var/log/mysyte/backup.log 2>&1
```

### Восстановление из backup

```bash
# Остановите сервисы
sudo systemctl stop mysyte telegram-bot

# Восстановите БД
cp /opt/mysyte/backups/orders_20260807_030000.db /opt/mysyte/orders.db

# Восстановите фото
tar -xzf /opt/mysyte/backups/photos_20260807_030000.tar.gz -C /

# Запустите сервисы
sudo systemctl start mysyte telegram-bot
```

---

## Troubleshooting

### Проблема: Бот не отвечает на Telegram Login

**Решение:**

1. Проверьте `TELEGRAM_BOT_TOKEN` в `.env`
2. Проверьте что бот запущен: `sudo systemctl status telegram-bot`
3. Убедитесь что домен правильно указан в Telegram Login Widget

### Проблема: 401 Unauthorized при входе

**Решение:**

1. Проверьте что пользователь создан: `python create_admin.py` → выберите пункт 2
2. Проверьте что `SECRET_KEY` одинаковый в `.env` при создании админа и при запуске
3. Очистите cookies браузера

### Проблема: "Invalid Telegram auth signature"

**Решение:**

1. Убедитесь что `TELEGRAM_BOT_TOKEN` правильный
2. Проверьте что время на сервере синхронизировано:
   ```bash
   timedatectl
   sudo timedatectl set-ntp true
   ```

### Проблема: База данных недоступна

**Решение:**

```bash
# Проверьте права доступа
ls -la /opt/mysyte/orders.db
sudo chown www-data:www-data /opt/mysyte/orders.db

# Проверьте путь в .env
grep DATABASE_URL /opt/mysyte/.env
```

### Проблема: Nginx 502 Bad Gateway

**Решение:**

```bash
# Проверьте что приложение запущено
sudo systemctl status mysyte

# Проверьте что порт 8000 слушается
sudo netstat -tlnp | grep 8000

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/mysyte_error.log
```

### Проблема: SSL сертификат не работает

**Решение:**

```bash
# Проверьте сертификат
sudo certbot certificates

# Обновите сертификат принудительно
sudo certbot renew --force-renewal

# Перезагрузите Nginx
sudo systemctl reload nginx
```

---

## Мониторинг

### Простой мониторинг через systemd

```bash
# Настройка email уведомлений при падении сервиса
sudo systemctl edit mysyte --full
```

Добавьте в секцию `[Service]`:

```ini
[Service]
# ... existing lines ...
OnFailure=notify-email@%n.service
```

### Использование PM2 (альтернатива systemd)

```bash
npm install -g pm2

# Запуск
pm2 start backend/app.py --name mysyte --interpreter python3

# Мониторинг
pm2 monit

# Логи
pm2 logs mysyte

# Автозапуск
pm2 startup
pm2 save
```

---

## Обновление приложения

### На сервере

```bash
cd /opt/mysyte

# Backup текущей версии
./backup.sh

# Получить обновления
git pull origin main

# Активировать venv
source venv/bin/activate

# Обновить зависимости
pip install -r requirements.txt

# Перезапустить сервисы
sudo systemctl restart mysyte telegram-bot

# Проверить статус
sudo systemctl status mysyte
sudo systemctl status telegram-bot
```

---

## Полезные команды

```bash
# Проверка всех сервисов
sudo systemctl status mysyte telegram-bot nginx

# Просмотр всех логов
sudo journalctl -xe

# Тест Nginx конфигурации
sudo nginx -t

# Перезагрузка всего
sudo systemctl restart mysyte telegram-bot nginx

# Просмотр использования ресурсов
htop

# Размер БД
du -h /opt/mysyte/orders.db

# Количество пользователей
python3 -c "
import sys; sys.path.insert(0, '/opt/mysyte/backend')
from database import SessionLocal
from models import User
print(f'Users: {SessionLocal().query(User).count()}')
"
```

---

## Контакты и поддержка

- Telegram бот: [@ZEVS_Parsing_orders_bot](https://t.me/ZEVS_Parsing_orders_bot)
- Документация проекта: см. другие `.md` файлы в проекте

---

**Готово!** Ваша система MySyte теперь развернута и готова к использованию! 🚀
