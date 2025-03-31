from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models, crud
from .database import SessionLocal
from app.celery_app import celery_app
from app.redis_client import delete_cached_link
import logging

logger = logging.getLogger(__name__)

def cleanup_unused_links():
    db = SessionLocal()
    try:
        settings = crud.get_setting(db, "unused_links_days")
        if not settings:
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

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        unused_links = db.query(models.Link).filter(
            models.Link.last_used_at < cutoff_date,
            models.Link.last_used_at.isnot(None)  # Исключаем ссылки, которые никогда не использовались
        ).all()

        for link in unused_links:
            crud.delete_link(db, link.id)

        return len(unused_links)
    finally:
        db.close()

@celery_app.task
def cleanup_expired_links():
    logger.info("Starting cleanup of expired links")
    db = SessionLocal()
    try:
        expired_links = db.query(models.Link).filter(
            models.Link.expires_at <= datetime.utcnow()
        ).all()
        
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
    logger.info(f"Starting cleanup of inactive links (older than {days} days)")
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        inactive_links = db.query(models.Link).filter(
            models.Link.last_accessed <= cutoff_date
        ).all()
        
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