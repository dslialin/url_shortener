from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timedelta
import random
import string
from typing import Optional, List

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_link(db: Session, short_code: str):
    return db.query(models.Link).filter(models.Link.short_code == short_code).first()

def get_link_by_id(db: Session, link_id: int):
    return db.query(models.Link).filter(models.Link.id == link_id).first()

def get_links(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Link).offset(skip).limit(limit).all()

def create_link(db: Session, link: schemas.LinkCreate, user_id: Optional[int] = None):
    short_code = generate_short_code()
    db_link = models.Link(
        original_url=str(link.original_url),
        short_code=short_code,
        custom_alias=link.custom_alias,
        expires_at=link.expires_at,
        owner_id=user_id
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def update_link(db: Session, link_id: int, link: schemas.LinkCreate):
    db_link = get_link_by_id(db, link_id)
    if db_link:
        db_link.original_url = str(link.original_url)
        if link.custom_alias:
            db_link.custom_alias = link.custom_alias
        if link.expires_at:
            db_link.expires_at = link.expires_at
        db.commit()
        db.refresh(db_link)
    return db_link

def delete_link(db: Session, link_id: int):
    db_link = get_link_by_id(db, link_id)
    if db_link:
        db.delete(db_link)
        db.commit()
        return True
    return False

def increment_click_count(db: Session, short_code: str):
    db_link = get_link(db, short_code)
    if db_link:
        db_link.click_count += 1
        db_link.last_used_at = datetime.utcnow()
        db.commit()
        db.refresh(db_link)
    return db_link

def search_links(db: Session, original_url: str):
    return db.query(models.Link).filter(models.Link.original_url.like(f"%{original_url}%")).all()

def generate_short_code(length: int = 6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def get_setting(db: Session, key: str):
    return db.query(models.Settings).filter(models.Settings.key == key).first()

def create_setting(db: Session, setting: models.Settings):
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting

def update_setting(db: Session, key: str, value: str):
    setting = get_setting(db, key)
    if setting:
        setting.value = value
        setting.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(setting)
    return setting

def get_expired_links(db: Session) -> List[models.Link]:
    """Получение списка истекших ссылок"""
    return db.query(models.Link).filter(
        models.Link.expires_at <= datetime.utcnow(),
        models.Link.expires_at.isnot(None)
    ).all()

def get_unused_links(db: Session, days: int) -> List[models.Link]:
    """Получение списка неиспользуемых ссылок"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return db.query(models.Link).filter(
        models.Link.last_used_at < cutoff_date,
        models.Link.last_used_at.isnot(None)
    ).all() 