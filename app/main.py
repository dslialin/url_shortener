from fastapi import FastAPI, HTTPException, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
import random
import string
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from database import SessionLocal, engine
import models, schemas
from redis_client import (
    get_cached_link, set_cached_link, delete_cached_link,
    increment_access_count, get_link_stats, set_link_stats
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.post("/links/shorten", response_model=schemas.LinkResponse)
async def create_short_link(link: schemas.LinkCreate, db: Session = Depends(get_db)):
    if link.custom_alias:
        existing_link = db.query(models.Link).filter(models.Link.short_code == link.custom_alias).first()
        if existing_link:
            raise HTTPException(status_code=400, detail="Custom alias already in use")
        short_code = link.custom_alias
    else:
        short_code = generate_short_code()
        while db.query(models.Link).filter(models.Link.short_code == short_code).first():
            short_code = generate_short_code()
    
    db_link = models.Link(
        original_url=str(link.original_url),
        short_code=short_code,
        expires_at=link.expires_at,
        created_at=datetime.utcnow()
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    
    link_data = {
        "original_url": str(link.original_url),
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "access_count": 0,
        "last_accessed": None
    }
    set_cached_link(short_code, link_data)
    
    return db_link

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
async def delete_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    delete_cached_link(short_code)
    
    db.delete(link)
    db.commit()
    return {"message": "Link deleted successfully"}

@app.put("/links/{short_code}", response_model=schemas.LinkResponse)
async def update_link(short_code: str, link_update: schemas.LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link_update.original_url:
        link.original_url = str(link_update.original_url)
    if link_update.expires_at:
        link.expires_at = link_update.expires_at
    
    db.commit()
    
    link_data = {
        "original_url": link.original_url,
        "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        "access_count": link.access_count,
        "last_accessed": link.last_accessed.isoformat() if link.last_accessed else None
    }
    set_cached_link(short_code, link_data)
    
    return link

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