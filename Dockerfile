FROM python:3.9-slim

WORKDIR /app

# Установка сборочных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Удаление сборочных зависимостей (опционально, для уменьшения размера образа)
# RUN apt-get purge -y --auto-remove build-essential python3-dev

# Копирование исходного кода
# Сначала явно копируем папку tests
COPY tests ./tests/
# Затем копируем все остальное
COPY . .

# Делаем entrypoint скрипт исполняемым
RUN chmod +x docker-entrypoint.sh

# Определяем порт, который слушает приложение
EXPOSE 8000

# Устанавливаем entrypoint скрипт
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 