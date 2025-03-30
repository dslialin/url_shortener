from celery import Celery
from celery.schedules import crontab
import os
from datetime import timedelta

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")
redis_db = os.getenv("REDIS_DB", "0")

celery_app = Celery(
    "url_shortener",
    broker=f"redis://{redis_host}:{redis_port}/{redis_db}",
    backend=f"redis://{redis_host}:{redis_port}/{redis_db}",
    include=["app.tasks"]
)

# Настройка Celery Beat для выполнения периодических задач
celery_app.conf.beat_schedule = {
    # Удаление просроченных ссылок
    'cleanup-expired-links-every-hour': {
        'task': 'app.tasks.cleanup_expired_links',
        'schedule': crontab(minute=0, hour='*'),  # Каждый час в 0 минут
    },
    # Удаление неактивных ссылок
    'cleanup-inactive-links-every-day': {
        'task': 'app.tasks.cleanup_inactive_links',
        'schedule': crontab(minute=0, hour=0),  # Каждый день в полночь
        'kwargs': {'days': 30},  # Ссылки, неактивные более 30 дней
    },
}

celery_app.conf.timezone = 'UTC'

if __name__ == '__main__':
    celery_app.start() 