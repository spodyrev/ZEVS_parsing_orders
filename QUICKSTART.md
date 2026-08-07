# Быстрый старт с аутентификацией

## 5 минут до запуска

### 1. Установите зависимости

```bash
cd /Users/macprospodyrev/Projects/MySyte
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройте .env

```bash
# Сгенерируйте секретный ключ
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Отредактируйте .env
nano .env
```

Убедитесь что установлены:
```bash
SECRET_KEY=<ваш_сгенерированный_ключ>
TELEGRAM_BOT_TOKEN=8986805321:AAGRXSKolZU6snMB9xZ_tpRUW0RVm5FqR2E
DEBUG=True
```

### 3. Создайте первого администратора

```bash
python create_admin.py
```

**Где взять Telegram ID:**
1. Откройте [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте `/start`
3. Скопируйте ваш ID

### 4. Запустите приложение

```bash
python backend/app.py
```

Вы увидите:
```
🚀 Запуск приложения...
✅ База данных инициализирована
🌐 Сервер доступен по адресу: http://127.0.0.1:8000
```

### 5. Войдите в систему

1. Откройте: http://localhost:8000/login
2. Нажмите "Login with Telegram"
3. Авторизуйтесь
4. Готово! Вы на главной странице

### 6. Управление пользователями

Откройте: http://localhost:8000/admin

Здесь вы можете:
- Добавлять новых сотрудников
- Управлять правами
- Деактивировать пользователей

## Добавление сотрудников

### Через админ-панель (рекомендуется):

1. Войдите как администратор
2. Откройте http://localhost:8000/admin
3. Нажмите "Добавить пользователя"
4. Попросите сотрудника получить его Telegram ID через [@userinfobot](https://t.me/userinfobot)
5. Введите Telegram ID и нажмите "Добавить"

### Через скрипт:

```bash
python create_admin.py
# Выберите пункт 1
```

## Важные ссылки

- **Страница входа:** http://localhost:8000/login
- **Главная страница:** http://localhost:8000/
- **Админ-панель:** http://localhost:8000/admin
- **API пользователя:** http://localhost:8000/api/auth/me
- **Выход:** http://localhost:8000/api/auth/logout

## Следующие шаги

### Для локальной разработки:
✅ Система готова к использованию!

### Для production деплоя:
📖 См. [README_DEPLOYMENT.md](README_DEPLOYMENT.md)

### Для понимания системы:
📖 См. [AUTHENTICATION_SYSTEM.md](AUTHENTICATION_SYSTEM.md)

## Частые вопросы

**Q: Как получить Telegram ID?**  
A: Откройте [@userinfobot](https://t.me/userinfobot) и отправьте `/start`

**Q: Забыл пароль**  
A: Пароля нет! Вход только через Telegram

**Q: Ошибка "User not found"**  
A: Добавьте пользователя через админ-панель или `create_admin.py`

**Q: Не могу зайти в админку**  
A: Убедитесь что у вашего пользователя `is_admin=1`

**Q: Как деплоить?**  
A: См. [README_DEPLOYMENT.md](README_DEPLOYMENT.md) - полная инструкция

---

**Готово!** Система работает 🚀
