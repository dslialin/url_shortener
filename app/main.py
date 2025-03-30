from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import random
import string

from .database import SessionLocal, engine
from . import models, schemas

# Create database tables
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
def create_short_link(link: schemas.LinkCreate, db: Session = Depends(get_db)):
    if link.custom_alias:
        existing_link = db.query(models.Link).filter(models.Link.short_code == link.custom_alias).first()
        if existing_link:
            raise HTTPException(status_code=400, detail="Custom alias already exists")
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
    
    return db_link

@app.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.expires_at and link.expires_at < datetime.utcnow():
        db.delete(link)
        db.commit()
        raise HTTPException(status_code=410, detail="Link has expired")
    
    link.last_accessed = datetime.utcnow()
    link.access_count += 1
    db.commit()
    
    return RedirectResponse(url=link.original_url, status_code=307, headers={"Cache-Control": "no-cache"})

@app.get("/links/{short_code}/stats", response_model=schemas.LinkStats)
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@app.delete("/links/{short_code}")
def delete_link(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db.delete(link)
    db.commit()
    return {"message": "Link deleted successfully"}

@app.put("/links/{short_code}", response_model=schemas.LinkResponse)
def update_link(short_code: str, link_update: schemas.LinkUpdate, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link_update.original_url:
        link.original_url = str(link_update.original_url)
    if link_update.expires_at:
        link.expires_at = link_update.expires_at
    
    db.commit()
    db.refresh(link)
    
    return link

@app.get("/links/search")
def search_link(original_url: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.original_url == original_url).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link 