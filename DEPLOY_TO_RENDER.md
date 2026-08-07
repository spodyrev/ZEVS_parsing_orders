# 🚀 Автоматический деплой на Render.com

## Шаг 1: Создайте GitHub репозиторий

### Вариант A: Через веб-интерфейс (проще)

1. Откройте https://github.com/new
2. Название репозитория: `MySyte` (или любое другое)
3. Сделайте репозиторий **Private** или **Public** (на ваш выбор)
4. **НЕ ДОБАВЛЯЙТЕ** README, .gitignore, или лицензию (у нас уже есть)
5. Нажмите **"Create repository"**
6. Скопируйте команды из раздела "…or push an existing repository from the command line"

### Вариант B: Через командную строку (если установлен gh CLI)

```bash
gh repo create MySyte --private --source=. --remote=origin --push
```

## Шаг 2: Push в GitHub

Выполните команды из GitHub (замените YOUR_USERNAME на ваше имя):

```bash
cd /Users/macprospodyrev/Projects/MySyte

git remote add origin https://github.com/YOUR_USERNAME/MySyte.git
git branch -M main
git push -u origin main
```

**Важно:** При запросе логина используйте **Personal Access Token** вместо пароля.

### Как создать Personal Access Token:

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Выберите scopes: `repo` (полный доступ к репозиториям)
4. Скопируйте токен и используйте его вместо пароля

## Шаг 3: Деплой на Render.com

### 3.1 Создайте аккаунт

1. Откройте https://render.com
2. Зарегистрируйтесь через GitHub (рекомендуется)
3. Подтвердите email

### 3.2 Создайте Web Service

1. В Render Dashboard нажмите **"New +"** → **"Web Service"**
2. Выберите **"Connect a repository"**
3. Найдите и выберите ваш репозиторий `MySyte`
4. Нажмите **"Connect"**

### 3.3 Настройте сервис

Render автоматически обнаружит `render.yaml`, но проверьте настройки:

**Basic Settings:**
- Name: `mysyte-web` (или ваше название)
- Environment: `Python 3`
- Region: `Oregon` (или ближайший)
- Branch: `main`
- Build Command: `./build.sh`
- Start Command: `./start.sh`

**Free Plan:**
- Instance Type: `Free`

### 3.4 Добавьте переменные окружения

Нажмите **"Environment"** и добавьте:

**Обязательные:**
- `TELEGRAM_BOT_TOKEN`: `ВАШ_ТОКЕН_БОТА` (возьмите из .env файла)
- `SECRET_KEY`: (нажмите "Generate" или используйте ваш ключ)

**Опциональные:**
- `GEMINI_API_KEY`: `ВАШ_GEMINI_KEY` (возьмите из .env файла, если используете)
- `DEBUG`: `false`
- `LOG_LEVEL`: `INFO`

**Автоматические (уже настроены):**
- `PORT` - Render установит автоматически
- `DATABASE_URL` - SQLite (для простоты)

### 3.5 Запустите деплой

1. Нажмите **"Create Web Service"**
2. Render начнет деплой (занимает 3-5 минут)
3. Следите за логами в реальном времени

## Шаг 4: Настройте Telegram бота

После успешного деплоя вы получите URL типа: `https://mysyte-web.onrender.com`

### 4.1 Настройте домен в @BotFather

1. Откройте Telegram, найдите **@BotFather**
2. Отправьте: `/setdomain`
3. Выберите: `@ZEVS_Parsing_orders_bot`
4. Введите: `mysyte-web.onrender.com` (без https://)

### 4.2 Обновите ALLOWED_ORIGINS (если нужно)

В Render Environment добавьте/обновите:
- `ALLOWED_ORIGINS`: `https://mysyte-web.onrender.com`

## Шаг 5: Создайте администратора

После деплоя нужно создать первого администратора.

### Через Render Shell:

1. В Render Dashboard откройте ваш сервис
2. Нажмите **"Shell"** (справа вверху)
3. Выполните:

```bash
python create_admin.py
```

4. Введите ваш Telegram ID: `242165070`
5. Заполните остальные данные

### Или через SSH (если настроен):

```bash
ssh $(render ps:ssh mysyte-web)
python create_admin.py
```

## Шаг 6: Тестирование

1. Откройте: `https://mysyte-web.onrender.com/login`
2. Нажмите **"Войти через Telegram"**
3. Подтвердите авторизацию
4. Вы должны попасть на главную страницу!

## Шаг 7: Админ-панель

Откройте: `https://mysyte-web.onrender.com/admin`

Здесь вы можете:
- Добавлять новых пользователей
- Управлять правами доступа
- Деактивировать пользователей

---

## 🎯 Краткая версия команд

```bash
# 1. Push в GitHub
cd /Users/macprospodyrev/Projects/MySyte
git remote add origin https://github.com/YOUR_USERNAME/MySyte.git
git branch -M main
git push -u origin main

# 2. Render.com
# - Зайдите на render.com
# - New + → Web Service
# - Подключите репозиторий
# - Deploy!

# 3. @BotFather
# /setdomain
# @ZEVS_Parsing_orders_bot
# mysyte-web.onrender.com

# 4. Создайте админа через Render Shell
# python create_admin.py
```

---

## ⚠️ Важные заметки

### Free Plan ограничения:
- ✅ Бесплатно навсегда
- ⚠️ Спит после 15 минут неактивности
- ⚠️ Первый запрос после сна занимает 30-60 секунд
- ✅ 750 часов работы в месяц (достаточно для малого бизнеса)

### Для production (рекомендации):
- Upgrade до Starter Plan ($7/месяц) - без засыпания
- Используйте PostgreSQL вместо SQLite
- Настройте custom domain
- Добавьте мониторинг

---

## 🆘 Проблемы и решения

### "Build failed"
- Проверьте логи в Render
- Убедитесь что `build.sh` executable: `chmod +x build.sh`
- Проверьте `requirements.txt`

### "Application failed to start"
- Проверьте Start Command: `./start.sh`
- Проверьте переменную `PORT`
- Посмотрите логи

### "Bot domain invalid"
- Убедитесь что в @BotFather указан правильный домен
- Домен должен быть БЕЗ `https://` и БЕЗ `/login`
- Правильно: `mysyte-web.onrender.com`
- Неправильно: `https://mysyte-web.onrender.com/login`

### "401 Unauthorized"
- Создайте администратора через Render Shell
- Проверьте что `TELEGRAM_BOT_TOKEN` правильный
- Проверьте что `SECRET_KEY` установлен

---

## 🎉 Готово!

Ваше приложение теперь:
- ✅ Доступно из интернета
- ✅ Работает 24/7 (с перерывами на Free plan)
- ✅ Имеет HTTPS
- ✅ Готово для работы сотрудников

**URL вашего приложения:** https://mysyte-web.onrender.com

---

## 📱 Поделитесь с сотрудниками

Отправьте им:
```
🔗 Система отслеживания заказов ZEVS
https://mysyte-web.onrender.com/login

Войдите через Telegram для доступа
```
