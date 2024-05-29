from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_collector: Optional[bool] = False
    is_admin: Optional[bool] = False

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    is_collector: bool
    is_admin: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DonationLocationCreate(BaseModel):
    name: str
    location: str
    hygiene: Optional[bool] = False
    food: Optional[bool] = False
    clothes: Optional[bool] = False

class DonationLocationUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    hygiene: Optional[bool] = None
    food: Optional[bool] = None
    clothes: Optional[bool] = None

class DonationLocation(BaseModel):
    id: int
    name: str
    location: str
    hygiene: bool
    food: bool
    clothes: bool
    collector_id: int

    class Config:
        orm_mode = True

class DonationLocationDeleteResponse(BaseModel):
    detail: str
