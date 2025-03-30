from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models, crud
from .database import SessionLocal
from app.celery_app import celery_app
from app.redis_client import delete_cached_link
import logging

logger = logging.getLogger(__name__)

def cleanup_unused_links():
    """Очистка неиспользуемых ссылок"""
    db = SessionLocal()
    try:
        # Получаем настройку периода неиспользования
        settings = crud.get_setting(db, "unused_links_days")
        if not settings:
            # Если настройка не найдена, создаем с значением по умолчанию (30 дней)
            crud.create_setting(
                db,
                models.Settings(
                    key="unused_links_days",
                    value="30",
                    description="Количество дней неиспользования ссылки перед удалением"
                )
            )
            days = 30
        else:
            days = int(settings.value)

        # Находим ссылки, которые не использовались более указанного периода
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        unused_links = db.query(models.Link).filter(
            models.Link.last_used_at < cutoff_date,
            models.Link.last_used_at.isnot(None)  # Исключаем ссылки, которые никогда не использовались
        ).all()

        # Удаляем найденные ссылки
        for link in unused_links:
            crud.delete_link(db, link.id)

        return len(unused_links)
    finally:
        db.close()

@celery_app.task
def cleanup_expired_links():
    """Удаляет из базы данных просроченные ссылки"""
    logger.info("Starting cleanup of expired links")
    db = SessionLocal()
    try:
        # Найти все просроченные ссылки
        expired_links = db.query(models.Link).filter(
            models.Link.expires_at <= datetime.utcnow()
        ).all()
        
        # Удалить их из БД и кэша
        for link in expired_links:
            delete_cached_link(link.short_code)
            db.delete(link)
        
        db.commit()
        logger.info(f"Deleted {len(expired_links)} expired links")
        return len(expired_links)
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up expired links: {e}")
        raise
    finally:
        db.close()

@celery_app.task
def cleanup_inactive_links(days=30):
    """Удаляет из базы данных неактивные ссылки
    
    Args:
        days: Количество дней неактивности, после которых ссылка считается неиспользуемой
    """
    logger.info(f"Starting cleanup of inactive links (older than {days} days)")
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Найти ссылки, которые не использовались больше days дней
        inactive_links = db.query(models.Link).filter(
            models.Link.last_accessed <= cutoff_date
        ).all()
        
        # Удалить их из БД и кэша
        for link in inactive_links:
            delete_cached_link(link.short_code)
            db.delete(link)
        
        db.commit()
        logger.info(f"Deleted {len(inactive_links)} inactive links")
        return len(inactive_links)
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up inactive links: {e}")
        raise
    finally:
        db.close() 