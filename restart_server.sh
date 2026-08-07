#!/bin/bash

# Скрипт для перезапуска сервера Taobao Parser

echo "🛑 Останавливаем сервер..."
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "⏳ Ждем 2 секунды..."
sleep 2

echo "🚀 Запускаем сервер..."
cd "$(dirname "$0")/backend"
python app.py

echo "✅ Сервер запущен!"
