#!/bin/sh
set -e

# Создаем базу данных SQLite, если она еще не существует
python -c "
from app.database import Base, engine
import app.models

# Создаем таблицы базы данных
Base.metadata.create_all(bind=engine)
print('База данных SQLite инициализирована')
"

# Выполняем переданную команду (например, uvicorn)
exec "$@" 