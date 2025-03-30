from fastapi import FastAPI, HTTPException, Depends, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import random
import string
import logging
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from app.database import SessionLocal, engine, get_db
import app.models as models
import app.schemas as schemas
from app.redis_client import (
    get_cached_link, set_cached_link, delete_cached_link,
    increment_access_count, get_link_stats, set_link_stats
)
from app.auth import (
    get_current_active_user,
    get_password_hash,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    try:
        result = {
            "username": current_user.username,
            "email": current_user.email,
            "id": current_user.id,
            "is_active": current_user.is_active
        }
        return result
    except Exception as e:
        import traceback
        logger.error(f"Error in read_users_me: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/links/shorten", response_model=schemas.LinkResponse)
async def create_short_link(
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_active_user)
):
    try:
        logger.debug(f"Creating short link for URL: {link.original_url}, custom alias: {link.custom_alias}")
        if link.custom_alias:
            existing_link = db.query(models.Link).filter(models.Link.custom_alias == link.custom_alias).first()
            if existing_link:
                raise HTTPException(status_code=400, detail="Custom alias already in use")
            short_code = link.custom_alias
        else:
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            short_code = ''.join(secrets.choice(alphabet) for _ in range(6))
        
        logger.debug(f"Using short code: {short_code}")
        logger.debug(f"Current user: {current_user.username if current_user else None}")
        
        db_link = models.Link(
            original_url=str(link.original_url),
            short_code=short_code,
            custom_alias=link.custom_alias,
            expires_at=link.expires_at,
            owner_id=current_user.id if current_user else None,
            created_at=datetime.utcnow(),
            access_count=0
        )
        
        logger.debug("Adding link to database")
        db.add(db_link)
        db.commit()
        logger.debug("Link added to database")
        db.refresh(db_link)
        
        # Сохраняем в кэш
        cache_data = {
            "original_url": str(db_link.original_url),
            "expires_at": db_link.expires_at.isoformat() if db_link.expires_at else None,
            "access_count": db_link.access_count,
            "last_accessed": db_link.last_accessed.isoformat() if db_link.last_accessed else None
        }
        set_cached_link(short_code, cache_data)
        
        result = {
            "original_url": db_link.original_url,
            "short_code": db_link.short_code,
            "custom_alias": db_link.custom_alias,
            "created_at": db_link.created_at,
            "expires_at": db_link.expires_at,
            "last_accessed": db_link.last_accessed,
            "access_count": db_link.access_count,
            "owner_id": db_link.owner_id
        }
        logger.debug(f"Returning link: {result}")
        return result
    except Exception as e:
        db.rollback()
        import traceback
        logger.error(f"Error creating short link: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint works!"}

@app.get("/links")
async def list_links(db: Session = Depends(get_db)):
    links = db.query(models.Link).all()
    return [
        {
            "original_url": link.original_url,
            "short_code": link.short_code,
            "created_at": link.created_at
        }
        for link in links
    ]

@app.get("/links/search")
async def search_link(original_url: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.original_url == original_url).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@app.get("/links/{short_code}/stats", response_model=schemas.LinkStats)
async def get_link_stats_endpoint(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    cached_stats = get_link_stats(short_code)
    if cached_stats:
        link.access_count = cached_stats.get("access_count", link.access_count)
    
    return {
        "original_url": link.original_url,
        "custom_alias": None,
        "short_code": link.short_code,
        "created_at": link.created_at,
        "expires_at": link.expires_at,
        "last_accessed": link.last_accessed,
        "access_count": link.access_count
    }

@app.get("/{short_code}")
@app.head("/{short_code}")
async def redirect_to_url(short_code: str, db: Session = Depends(get_db)):

    cached_link = get_cached_link(short_code)
    if cached_link:
        if cached_link["expires_at"]:
            expires_at = datetime.fromisoformat(cached_link["expires_at"])
            if datetime.utcnow() > expires_at:
                delete_cached_link(short_code)
                raise HTTPException(status_code=404, detail="Link has expired")
        
        increment_access_count(short_code)
        cached_link["access_count"] += 1
        cached_link["last_accessed"] = datetime.utcnow().isoformat()
        set_cached_link(short_code, cached_link)
        
        return RedirectResponse(url=cached_link["original_url"])
    
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.expires_at and datetime.utcnow() > link.expires_at:
        db.delete(link)
        db.commit()
        raise HTTPException(status_code=404, detail="Link has expired")
    
    link.access_count += 1
    link.last_accessed = datetime.utcnow()
    db.commit()
    
    link_data = {
        "original_url": link.original_url,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "access_count": link.access_count,
        "last_accessed": link.last_accessed.isoformat()
    }
    set_cached_link(short_code, link_data)
    
    return RedirectResponse(url=link.original_url)

@app.delete("/links/{short_code}")
async def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this link")

    db.delete(link)
    db.commit()
    return {"message": "Link deleted successfully"}

@app.put("/links/{short_code}", response_model=schemas.LinkResponse)
async def update_link(
    short_code: str,
    link_update: schemas.LinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not db_link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if db_link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this link")
    
    # Update fields
    if link_update.original_url is not None:
        db_link.original_url = link_update.original_url
    if link_update.expires_at is not None:
        db_link.expires_at = link_update.expires_at

    db.commit()
    db.refresh(db_link)
    return db_link

@app.get("/all-links")
async def get_all_links(db: Session = Depends(get_db)):
    try:
        logger.debug("Getting all links")
        links = db.query(models.Link).all()
        logger.debug(f"Found {len(links)} links")
        result = [
            {
                "original_url": link.original_url,
                "custom_alias": None,
                "expires_at": link.expires_at,
                "short_code": link.short_code,
                "created_at": link.created_at,
                "last_accessed": link.last_accessed,
                "access_count": link.access_count
            }
            for link in links
        ]
        logger.debug(f"Returning result: {result}")
        return result
    except Exception as e:
        logger.error("Error getting all links", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 