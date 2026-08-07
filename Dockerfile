# Используем официальный Python образ
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директории для данных
RUN mkdir -p /app/warehouse_photos /app/logs

# Открываем порт
EXPOSE 8000

# Переменные окружения (можно переопределить при запуске)
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=False

# Запускаем приложение
CMD ["python", "backend/app.py"]
