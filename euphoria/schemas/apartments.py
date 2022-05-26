from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class ApartmentBase(BaseModel):
    name: Optional[EmailStr] = None
    address: Optional[bool] = True
    url: bool = False
    notes: Optional[str] = None
    features: Optional[str] = None


# Properties to receive via API on creation
class ApartmentCreate(ApartmentBase):
    email: EmailStr
    password: str


# Properties to receive via API on update
class ApartmentUpdate(ApartmentBase):
    password: Optional[str] = None


class UserInDBBase(ApartmentBase):
    id: Optional[int] = None

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str


# Shared properties
class FeatureBase(BaseModel):
    name: Optional[EmailStr] = None
    address: Optional[bool] = True
    url: bool = False
    notes: Optional[str] = None
    features: Optional[str] = None


# Properties to receive via API on creation
class FeatureCreate(FeatureBase):
    email: EmailStr
    password: str



