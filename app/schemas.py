from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class LinkBase(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkCreate(LinkBase):
    pass

class LinkUpdate(BaseModel):
    original_url: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkResponse(LinkBase):
    short_code: str
    created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    class Config:
        from_attributes = True

class LinkStats(LinkResponse):
    pass 