#!/bin/bash
# Скрипт для перезапуска Telegram бота

echo "🔄 Перезапуск Telegram бота..."

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source venv/bin/activate

# Останавливаем бота если запущен
echo "🛑 Останавливаем старый процесс бота..."
pkill -f "start_telegram_bot.py" 2>/dev/null
sleep 1

# Запускаем бота
echo "🚀 Запускаем бота с новыми изменениями..."
python3 start_telegram_bot.py
