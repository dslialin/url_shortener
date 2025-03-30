# URL Shortener

Сервис для сокращения длинных URL-адресов на основе FastAPI с кэшированием Redis и аутентификацией пользователей.

## Возможности

- Регистрация и аутентификация пользователей
- Создание коротких URL с пользовательскими алиасами
- Перенаправление на оригинальные URL
- Получение статистики по URL
- Кэширование Redis для улучшения производительности
- Поиск по оригинальному URL
- Просмотр всех сокращенных URL
- Обновление и удаление URL (для аутентифицированных пользователей)
- Установка времени истечения срока действия URL

## Требования

- Python 3.8+
- Redis
- SQLite (включен)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <url-вашего-репозитория>
cd url_shortener
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите сервер Redis (если не запущен)

5. Запустите приложение:
```bash
uvicorn main:app --reload --port 8090
```

## API Endpoints

### Аутентификация
- `POST /register` - Регистрация нового пользователя
- `POST /token` - Получение токена доступа (вход)
- `GET /users/me` - Получение информации о текущем пользователе

### Управление URL
- `POST /links/shorten` - Создание нового короткого URL (требует аутентификации)
- `GET /{short_code}` - Перенаправление на оригинальный URL
- `GET /links/{short_code}/stats` - Получение статистики по URL
- `GET /links/search` - Поиск по оригинальному URL
- `GET /links` - Просмотр всех сокращенных URL
- `PUT /links/{short_code}` - Обновление URL (требует аутентификации)
- `DELETE /links/{short_code}` - Удаление URL (требует аутентификации)

## Примеры использования

### Регистрация нового пользователя:
```bash
curl -X POST "http://localhost:8090/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'
```

### Получение токена доступа:
```bash
curl -X POST "http://localhost:8090/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass123"
```

### Создание короткого URL (с аутентификацией):
```bash
curl -X POST "http://localhost:8090/links/shorten" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://www.example.com", "custom_alias": "my-link", "expires_at": "2025-12-31T23:59:59"}'
```

### Получение статистики по URL:
```bash
curl "http://localhost:8090/links/{short_code}/stats"
```

### Обновление URL (с аутентификацией):
```bash
curl -X PUT "http://localhost:8090/links/{short_code}" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://www.new-url.com"}'
```

### Удаление URL (с аутентификацией):
```bash
curl -X DELETE "http://localhost:8090/links/{short_code}" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Регистрация и аутентификация

### Регистрация пользователя
Для использования сервиса необходимо зарегистрироваться. При регистрации требуется указать:
- Имя пользователя (уникальное)
- Email (уникальный)
- Пароль (минимум 8 символов)

После успешной регистрации вы получите доступ к созданию и управлению короткими URL.

### Аутентификация
После регистрации для доступа к защищенным эндпоинтам необходимо получить токен доступа. Токен используется в заголовке `Authorization: Bearer YOUR_ACCESS_TOKEN` для всех защищенных запросов.

## Функции безопасности

- Хеширование паролей с использованием bcrypt
- Аутентификация на основе JWT
- Контроль доступа для управления URL
- Валидация email
- Проверка уникальности имени пользователя и email

## Лицензия

MIT 