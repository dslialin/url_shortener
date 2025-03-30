from database import SessionLocal, engine
from models import Link

def check_db():
    db = SessionLocal()
    try:
        links = db.query(Link).all()
        print(f"Found {len(links)} links:")
        for link in links:
            print(f"- {link.short_code}: {link.original_url}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db() 