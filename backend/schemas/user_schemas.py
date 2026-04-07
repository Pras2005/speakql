from typing import Optional
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str


class UserLogin(SQLModel):
    username: str
    password: str

