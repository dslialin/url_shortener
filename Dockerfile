FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Копирование исходного кода
COPY . .

# Делаем entrypoint скрипт исполняемым
RUN chmod +x docker-entrypoint.sh

# Определяем порт, который слушает приложение
EXPOSE 8000

# Устанавливаем entrypoint скрипт
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Команда для запуска приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 