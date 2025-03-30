# Сервис сокращения ссылок

Полнофункциональный сервис для сокращения URL-адресов, построенный на FastAPI с поддержкой аутентификации и кэширования.

## Возможности

- Регистрация и аутентификация пользователей через JWT токены
- Создание коротких ссылок из длинных URL-адресов
- Поддержка пользовательских алиасов (псевдонимов)
- Установка срока действия ссылок
- Статистика использования (количество переходов, время последнего доступа)
- Кэширование популярных ссылок в Redis
- Поиск по оригинальному URL
- Обновление и удаление ссылок (только для авторизованных пользователей)
- Автоматическое удаление просроченных ссылок

## API Endpoints

### Аутентификация
- `POST /register` - Регистрация нового пользователя
- `POST /token` - Получение JWT токена доступа
- `GET /users/me` - Информация о текущем пользователе

### Управление ссылками
- `POST /links/shorten` - Создание новой короткой ссылки
- `GET /{short_code}` - Перенаправление на оригинальный URL
- `GET /links/{short_code}/stats` - Получение статистики ссылки
- `DELETE /links/{short_code}` - Удаление ссылки (требуется авторизация)
- `PUT /links/{short_code}` - Обновление ссылки (требуется авторизация)
- `GET /links/search` - Поиск по оригинальному URL
- `GET /all-links` - Получение всех ссылок (для дебага)

## Установка и запуск

1. Убедитесь, что у вас установлен Python 3.8 или выше
2. Установите Redis (для кэширования)
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Создайте файл .env в корневой директории (опционально):
   ```
   DATABASE_URL=sqlite:///./url_shortener.db
   SECRET_KEY=your-secret-key-here
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```
5. Запустите сервер:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

Сервис будет доступен по адресу http://localhost:8000

## Документация API

После запуска сервиса вы можете получить доступ к:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Примеры использования

### Регистрация пользователя
```bash
curl -X POST "http://localhost:8000/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'
```

### Получение токена
```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass123"
```

### Создание короткой ссылки с авторизацией
```bash
curl -X POST "http://localhost:8000/links/shorten" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://example.com", "custom_alias": "my-link"}'
```

### Получение статистики ссылки
```bash
curl "http://localhost:8000/links/my-link/stats"
```

### Создание ссылки с датой истечения
```bash
curl -X POST "http://localhost:8000/links/shorten" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
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
│   ├── schemas.py     # Схемы Pydantic
│   ├── auth.py        # Аутентификация и авторизация
│   ├── database.py    # Настройка базы данных
│   └── redis_client.py # Клиент Redis для кэширования
├── requirements.txt   # Зависимости проекта
└── README.md          # Документация
``` 