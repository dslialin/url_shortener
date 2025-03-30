# Сервис сокращения ссылок

Простой сервис для сокращения URL-адресов, построенный на FastAPI.

## Возможности

- Создание коротких ссылок из длинных URL-адресов
- Поддержка пользовательских алиасов (псевдонимов)
- Установка срока действия ссылок
- Статистика использования (количество переходов, время последнего доступа)
- Поиск по оригинальному URL
- Обновление и удаление ссылок

## API Endpoints

- `POST /links/shorten` - Создание новой короткой ссылки
- `GET /{short_code}` - Перенаправление на оригинальный URL
- `GET /links/{short_code}/stats` - Получение статистики ссылки
- `DELETE /links/{short_code}` - Удаление ссылки
- `PUT /links/{short_code}` - Обновление ссылки
- `GET /links/search` - Поиск по оригинальному URL

## Установка и запуск

1. Убедитесь, что у вас установлен Python 3.8 или выше
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Запустите сервер:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

Сервис будет доступен по адресу http://localhost:8000

## Документация API

После запуска сервиса вы можете получить доступ к:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Примеры использования

Создание короткой ссылки:
```bash
curl -X POST "http://localhost:8000/links/shorten" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://example.com", "custom_alias": "my-link"}'
```

Получение статистики ссылки:
```bash
curl "http://localhost:8000/links/my-link/stats"
```

Создание ссылки с датой истечения:
```bash
curl -X POST "http://localhost:8000/links/shorten" \
     -H "Content-Type: application/json" \
     -d '{
       "original_url": "https://example.com",
       "custom_alias": "temp-link",
       "expires_at": "2024-12-31T23:59:59Z"
     }'
```

## Структура проекта

```
url_shortener/
├── app/
│   ├── __init__.py
│   ├── main.py        # Основной файл приложения
│   ├── models.py      # Модели данных
│   └── schemas.py     # Схемы Pydantic
├── requirements.txt   # Зависимости проекта
└── README.md         # Документация
``` 