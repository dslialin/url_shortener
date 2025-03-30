from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import redis
import json
from . import crud, models, schemas
from .database import SessionLocal, engine
from .auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_active_user
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis клиент
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Фоновая задача для очистки неиспользуемых ссылок
async def cleanup_unused_links_task():
    from .tasks import cleanup_unused_links
    cleanup_unused_links()

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@app.post("/links/shorten", response_model=schemas.LinkResponse)
def create_short_link(
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    return crud.create_link(db=db, link=link, user_id=current_user.id)

@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    # Проверяем, не является ли short_code специальным маршрутом
    special_routes = ["register", "token", "users", "links", "settings", "cleanup"]
    if short_code in special_routes:
        raise HTTPException(status_code=404, detail="Not Found")
    
    # Проверяем кэш Redis
    cached_url = redis_client.get(f"url:{short_code}")
    if cached_url:
        crud.increment_click_count(db, short_code)
        return {"url": cached_url.decode()}
    
    # Если нет в кэше, ищем в базе данных
    db_link = crud.get_link(db, short_code)
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Проверяем срок действия
    if db_link.expires_at and db_link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link has expired")
    
    # Сохраняем в кэш и обновляем статистику
    redis_client.setex(f"url:{short_code}", 3600, str(db_link.original_url))
    crud.increment_click_count(db, short_code)
    
    return {"url": str(db_link.original_url)}

@app.get("/links/{short_code}/stats", response_model=schemas.LinkStats)
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    db_link = crud.get_link(db, short_code)
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    return db_link

@app.get("/links/search")
def search_links(original_url: str, db: Session = Depends(get_db)):
    return crud.search_links(db, original_url)

@app.get("/links", response_model=List[schemas.LinkResponse])
def list_links(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    return crud.get_links(db, skip=skip, limit=limit)

@app.put("/links/{short_code}", response_model=schemas.LinkResponse)
def update_link(
    short_code: str,
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_link = crud.get_link(db, short_code)
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    if db_link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return crud.update_link(db, db_link.id, link)

@app.delete("/links/{short_code}")
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_link = crud.get_link(db, short_code)
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    if db_link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    crud.delete_link(db, db_link.id)
    return {"message": "Link deleted"}

@app.get("/settings/unused-links-days", response_model=schemas.Settings)
def get_unused_links_days(db: Session = Depends(get_db)):
    """Получение настройки периода неиспользования ссылок"""
    setting = crud.get_setting(db, "unused_links_days")
    if not setting:
        # Создаем настройку по умолчанию
        setting = crud.create_setting(
            db,
            models.Settings(
                key="unused_links_days",
                value="30",
                description="Количество дней неиспользования ссылки перед удалением"
            )
        )
    return setting

@app.put("/settings/unused-links-days", response_model=schemas.Settings)
def update_unused_links_days(
    days: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Обновление настройки периода неиспользования ссылок"""
    if days < 1:
        raise HTTPException(
            status_code=400,
            detail="Количество дней должно быть положительным числом"
        )
    setting = crud.update_setting(db, "unused_links_days", str(days))
    return setting

@app.get("/links/expired", response_model=List[schemas.ExpiredLink])
def get_expired_links(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Получение списка истекших ссылок"""
    return crud.get_expired_links(db)

@app.post("/cleanup", response_model=dict)
async def trigger_cleanup(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_active_user)
):
    """Запуск очистки неиспользуемых ссылок"""
    background_tasks.add_task(cleanup_unused_links_task)
    return {"message": "Очистка неиспользуемых ссылок запущена"} 