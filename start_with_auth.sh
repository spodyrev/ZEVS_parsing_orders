#!/bin/bash

# Скрипт быстрого запуска MySyte с аутентификацией

echo "🚀 Запуск MySyte с системой аутентификации"
echo "============================================"
echo ""

# Переходим в корень проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    echo "✅ Активация виртуального окружения..."
    source venv/bin/activate
else
    echo "❌ Виртуальное окружение не найдено!"
    echo "   Создайте его: python3 -m venv venv"
    exit 1
fi

# Проверяем зависимости
if ! python -c "import jose" &> /dev/null; then
    echo "⚠️  Установка/обновление зависимостей..."
    pip install -r requirements.txt -q
    echo "✅ Зависимости установлены"
fi

# Проверяем .env
if ! grep -q "GWdCVnW9mvKXbHGNcIo2D6X" .env; then
    echo "❌ SECRET_KEY не настроен в .env!"
    exit 1
fi

echo ""
echo "📋 Что дальше:"
echo ""
echo "1️⃣  Создайте первого администратора (если еще не создали):"
echo "   python create_admin.py"
echo ""
echo "2️⃣  Запустите приложение:"
echo "   python backend/app.py"
echo ""
echo "3️⃣  Откройте браузер:"
echo "   http://localhost:8000/login"
echo ""
echo "============================================"
echo ""
