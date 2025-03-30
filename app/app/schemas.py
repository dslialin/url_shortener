from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional
from datetime import datetime

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
    original_url: HttpUrl
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkCreate(LinkBase):
    pass

class LinkResponse(LinkBase):
    id: int
    short_code: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    click_count: int
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True

class LinkStats(BaseModel):
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    click_count: int
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SettingsBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class SettingsCreate(SettingsBase):
    pass

class Settings(SettingsBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class ExpiredLink(BaseModel):
    id: int
    original_url: HttpUrl
    short_code: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    click_count: int
    expires_at: Optional[datetime] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True 