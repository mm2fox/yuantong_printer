from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    real_name: Optional[str] = None
    role: Optional[str] = "普通用户"

class UserCreate(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    role: Optional[str] = "普通用户"
    is_active: Optional[bool] = True
    temple_id: Optional[int] = None

class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    temple_id: Optional[int] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    role: Optional[str] = None
    is_active: bool
    temple_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
