# Сервис сокращения ссылок

Полнофункциональный сервис для сокращения URL-адресов, построенный на FastAPI с поддержкой аутентификации, кэширования и фоновых задач.

## Возможности

- Регистрация и аутентификация пользователей через JWT токены
- Создание коротких ссылок из длинных URL-адресов
- Поддержка пользовательских алиасов (псевдонимов)
- Установка срока действия ссылок
- Статистика использования (количество переходов, время последнего доступа)
- Кэширование популярных ссылок в Redis
- Поиск по оригинальному URL
- Обновление и удаление ссылок (только для авторизованных пользователей)
- Автоматическое удаление просроченных и неактивных ссылок через Celery
- Docker и Docker Compose для простого развертывания

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
- `GET /links` - Получение всех ссылок
- `GET /test` - Тестовый эндпоинт для проверки работоспособности API

## Установка и запуск

### Запуск с помощью Docker (рекомендуемый способ)

1. Убедитесь, что у вас установлены Docker и Docker Compose
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/url_shortener.git
   cd url_shortener
   ```
3. Запустите приложение с помощью Docker Compose:
   ```bash
   docker-compose up -d
   ```

Сервис будет доступен по адресу http://localhost:8000

Контейнеры, запускаемые Docker Compose:
- **app**: FastAPI приложение
- **redis**: Кэш-сервер Redis
- **celery**: Обработчик фоновых задач
- **celery-beat**: Планировщик периодических задач

### Запуск локально

1. Убедитесь, что у вас установлен Python 3.8 или выше
2. Установите Redis (для кэширования)
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Создайте файл .env в корневой директории:
   ```
   DATABASE_URL=sqlite:///./url_shortener.db
   SECRET_KEY=your-secret-key-here
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```
5. Запустите сервер:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Для запуска Celery worker (опционально):
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```
7. Для запуска Celery beat (планировщик задач):
   ```bash
   celery -A app.celery_app beat --loglevel=info
   ```

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

### Проверка переадресации
```bash
curl -i "http://localhost:8000/my-link"
```

## Структура базы данных

Проект использует SQLite для хранения данных. Основные таблицы:

### Таблица `users`
- `id`: INTEGER (Primary Key) - ID пользователя
- `username`: VARCHAR - Имя пользователя
- `email`: VARCHAR - Email пользователя
- `hashed_password`: VARCHAR - Хэшированный пароль
- `is_active`: BOOLEAN - Активен ли пользователь

### Таблица `links`
- `id`: INTEGER (Primary Key) - ID ссылки
- `original_url`: VARCHAR - Оригинальный URL
- `short_code`: VARCHAR - Короткий код для доступа
- `custom_alias`: VARCHAR (nullable) - Пользовательский алиас
- `created_at`: DATETIME - Дата создания
- `expires_at`: DATETIME (nullable) - Дата истечения срока действия
- `last_accessed`: DATETIME (nullable) - Дата последнего доступа
- `access_count`: INTEGER - Счетчик переходов
- `owner_id`: INTEGER (Foreign Key) - ID владельца (пользователя)

### Таблица `settings`
- `id`: INTEGER (Primary Key) - ID настройки
- `key`: VARCHAR - Ключ настройки
- `value`: VARCHAR - Значение настройки
- `description`: VARCHAR (nullable) - Описание настройки
- `created_at`: DATETIME - Дата создания
- `updated_at`: DATETIME - Дата последнего обновления

## Фоновые задачи (Celery)

Приложение использует Celery для выполнения следующих фоновых задач:

- **cleanup_expired_links**: Удаление просроченных ссылок (запускается каждый час)
- **cleanup_inactive_links**: Удаление неактивных ссылок, которые не использовались длительное время (запускается ежедневно в полночь)

## Кэширование (Redis)

Redis используется для:
- Кэширования часто используемых ссылок для ускорения доступа
- Хранения статистики использования
- Очереди задач для Celery

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
│   ├── tasks.py       # Задачи Celery для автоматической очистки
│   ├── celery_app.py  # Настройка Celery
│   ├── redis_client.py # Клиент Redis для кэширования
│   ├── cache.py       # Функции для работы с кэшем
│   └── check_db.py    # Скрипт для проверки базы данных
├── Dockerfile         # Файл для сборки Docker образа
├── docker-compose.yml # Конфигурация Docker Compose
├── docker-entrypoint.sh # Скрипт инициализации для Docker
├── .dockerignore      # Исключения для Docker сборки
├── .env               # Переменные окружения
├── requirements.txt   # Зависимости проекта
├── url_shortener.db   # SQLite база данных
└── README.md          # Документация
```

## Технический стек

- **Backend**: FastAPI, Uvicorn
- **База данных**: SQLite, SQLAlchemy ORM
- **Кэширование**: Redis
- **Фоновые задачи**: Celery, Celery Beat
- **Аутентификация**: JWT (JSON Web Tokens)
- **Контейнеризация**: Docker, Docker Compose

## Автоматическая очистка

Система автоматически удаляет:
- Ссылки с истекшим сроком действия
- Ссылки, которые не использовались более 30 дней (настраивается) 