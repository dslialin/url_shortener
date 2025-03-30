from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from . import models, crud
from .database import SessionLocal

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