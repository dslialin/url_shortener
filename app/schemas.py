from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

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
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True

class LinkStats(LinkResponse):
    pass 