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
- Управление неиспользуемыми ссылками

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
  - Поддерживает пользовательские алиасы
  - Позволяет установить срок действия ссылки
  - Автоматически генерирует короткий код, если алиас не указан
- `GET /{short_code}` - Перенаправление на оригинальный URL
- `GET /links/{short_code}/stats` - Получение статистики по URL (требует аутентификации)
  - Показывает количество переходов
  - Отображает дату последнего доступа
  - Включает информацию о сроке действия
- `GET /links/search` - Поиск по оригинальному URL (требует аутентификации)
- `GET /links` - Просмотр всех сокращенных URL пользователя (требует аутентификации)
- `PUT /links/{short_code}` - Обновление URL (требует аутентификации)
  - Можно обновить срок действия
  - Можно изменить пользовательский алиас
- `DELETE /links/{short_code}` - Удаление URL (требует аутентификации)

### Управление неиспользуемыми ссылками
- `GET /settings/unused-links-days` - Получение текущей настройки периода неиспользования ссылок
- `PUT /settings/unused-links-days` - Обновление периода неиспользования ссылок (требует аутентификации)
- `GET /links/expired` - Просмотр списка истекших ссылок (требует аутентификации)
- `POST /cleanup` - Запуск очистки неиспользуемых ссылок (требует аутентификации)

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
curl "http://localhost:8090/links/{short_code}/stats" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Поиск ссылок:
```bash
curl "http://localhost:8090/links/search?original_url=https://example.com" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Обновление ссылки:
```bash
curl -X PUT "http://localhost:8090/links/{short_code}" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"expires_at": "2025-12-31T23:59:59"}'
```

### Удаление ссылки:
```bash
curl -X DELETE "http://localhost:8090/links/{short_code}" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Управление настройками неиспользуемых ссылок:
```bash
# Получение текущей настройки
curl "http://localhost:8090/settings/unused-links-days"

# Обновление периода неиспользования (например, 60 дней)
curl -X PUT "http://localhost:8090/settings/unused-links-days?days=60" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Просмотр истекших ссылок
curl "http://localhost:8090/links/expired" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Запуск очистки неиспользуемых ссылок
curl -X POST "http://localhost:8090/cleanup" \
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

## Безопасность

- Все эндпоинты управления ссылками требуют аутентификации
- Пароли хешируются с использованием bcrypt
- Используется JWT для аутентификации
- Токены имеют ограниченный срок действия
- Все URL-адреса проверяются на валидность

## Ограничения

- Минимальная длина пароля: 8 символов
- Максимальная длина пользовательского алиаса: 50 символов
- Срок действия токена: 30 минут
- Максимальное количество попыток входа: 5 в минуту 