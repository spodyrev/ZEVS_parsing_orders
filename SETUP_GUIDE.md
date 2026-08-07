# Пошаговая инструкция для новичка

Привет! Это подробная инструкция, как запустить проект с нуля.

## Что мы будем делать?

1. Установим Python и все нужные программы
2. Создадим изолированное окружение для проекта
3. Установим библиотеки
4. Запустим приложение
5. Посмотрим веб-интерфейс

## Часть 1: Проверка и установка Python

### macOS:

1. Открой **Terminal** (Терминал)
   - Нажми `Cmd + Space`
   - Введи "Terminal" и нажми Enter

2. Проверь версию Python:
   ```bash
   python3 --version
   ```
   
   Должно показать что-то типа `Python 3.10.0` или новее.
   
3. Если Python не установлен, установи через Homebrew:
   ```bash
   # Установка Homebrew (если еще нет)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Установка Python
   brew install python@3.11
   ```

### Windows:

1. Скачай Python с [python.org](https://www.python.org/downloads/)
2. Запусти установщик
3. ⚠️ **ВАЖНО:** Поставь галочку "Add Python to PATH"
4. Нажми "Install Now"

### Linux:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

## Часть 2: Переход в папку проекта

В терминале перейди в папку проекта:

```bash
cd /Users/macprospodyrev/Projects/MySyte
```

Проверь, что ты в правильной папке:

```bash
ls
```

Ты должен увидеть файлы: `README.md`, `requirements.txt`, папки `backend`, `frontend`.

## Часть 3: Создание виртуального окружения

**Что это?** Виртуальное окружение - это изолированная папка, где хранятся все библиотеки только для этого проекта. Это как отдельная коробка с инструментами.

```bash
# Создание виртуального окружения
python3 -m venv venv
```

Подожди несколько секунд, создастся папка `venv`.

## Часть 4: Активация виртуального окружения

### macOS/Linux:
```bash
source venv/bin/activate
```

### Windows:
```bash
venv\Scripts\activate
```

✅ **Проверка:** Перед строкой в терминале должно появиться `(venv)`:

```
(venv) macprospodyrev@MacBook MySyte %
```

## Часть 5: Установка зависимостей

Теперь установим все нужные библиотеки:

```bash
pip install -r requirements.txt
```

Это займет 1-3 минуты. Увидишь много текста - это нормально.

После установки, установи браузеры для Playwright:

```bash
playwright install chromium
```

## Часть 6: Создание файла настроек

Скопируй пример настроек:

```bash
cp .env.example .env
```

Если хочешь изменить настройки (например, интервал проверки):

```bash
# macOS/Linux
nano .env

# Windows
notepad .env
```

## Часть 7: Первый запуск!

Запусти приложение:

```bash
# Вариант 1: Через скрипт (рекомендуется)
./start.sh

# Вариант 2: Вручную
cd backend
python app.py
```

Ты увидишь:

```
🚀 Запуск приложения...
✅ База данных инициализирована
🌐 Сервер доступен по адресу: http://127.0.0.1:8000
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Часть 8: Открываем веб-интерфейс

1. Открой браузер
2. Перейди по адресу: http://localhost:8000
3. Ты увидишь главную страницу проекта!

## Часть 9: Добавляем тестовый заказ

Пока парсер Taobao не готов, можно добавить тестовый заказ:

1. Открой в браузере: http://localhost:8000/api/test/add-order
2. Или нажми на ссылку в веб-интерфейсе
3. Перезагрузи главную страницу - появится тестовый заказ!

## Часть 10: Остановка приложения

В терминале нажми: `Ctrl + C`

## Что дальше?

### 1. Исследование Taobao API

Прочитай файл `TAOBAO_API_RESEARCH.md` - там подробная инструкция, как найти API эндпоинты Taobao.

### 2. Настройка парсера

После того как найдешь API:
- Отредактируй `backend/scraper/taobao_client.py`
- Отредактируй `backend/scraper/parser.py`

### 3. Тестирование

Запусти тест парсера:

```bash
cd backend/scraper
python taobao_client.py
```

## Частые проблемы

### Ошибка "python: command not found"

Попробуй `python3` вместо `python`:

```bash
python3 --version
```

### Ошибка "Permission denied: ./start.sh"

Сделай файл исполняемым:

```bash
chmod +x start.sh
```

### Ошибка "ModuleNotFoundError: No module named 'fastapi'"

Убедись, что виртуальное окружение активировано (должно быть `(venv)` в начале строки).

Если нет, активируй:

```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Ошибка "Address already in use"

Порт 8000 уже занят. Измени порт в `.env`:

```
PORT=8001
```

### Браузер не открывается в Playwright

Установи зависимости системы:

```bash
# macOS
brew install --cask playwright

# Linux
playwright install-deps
```

## Полезные команды

### Проверить статус виртуального окружения:
```bash
which python
# Должен показать путь с venv
```

### Просмотреть установленные пакеты:
```bash
pip list
```

### Обновить все пакеты:
```bash
pip install --upgrade -r requirements.txt
```

### Очистить базу данных:
```bash
rm orders.db
# База создастся заново при следующем запуске
```

## Структура проекта (для понимания)

```
MySyte/
├── venv/                    # Виртуальное окружение (не трогай)
├── backend/                 # Весь серверный код
│   ├── app.py              # Главный файл - запускаем его
│   ├── models.py           # Описание таблиц БД
│   ├── database.py         # Подключение к БД
│   ├── config.py           # Настройки из .env
│   ├── scheduler.py        # Автоматическая проверка
│   └── scraper/            # Парсер Taobao
│       ├── taobao_client.py
│       ├── auth.py
│       └── parser.py
├── frontend/               # Веб-интерфейс
│   ├── static/            # CSS, JS
│   └── templates/         # HTML страницы
├── requirements.txt       # Список библиотек
├── .env                   # Твои настройки (не в Git!)
├── .env.example          # Пример настроек
├── start.sh              # Скрипт запуска
└── orders.db             # База данных (создается автоматически)
```

## Следующие шаги

1. ✅ Установка и запуск - **готово!**
2. 🔍 Исследование Taobao API - читай `TAOBAO_API_RESEARCH.md`
3. 🛠️ Разработка парсера - адаптация под реальный API
4. ✨ Тестирование и улучшения

Удачи! Если что-то не работает - перечитай инструкцию внимательно, обычно причина в пропущенном шаге.
