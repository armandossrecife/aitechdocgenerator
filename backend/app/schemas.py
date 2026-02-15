from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import JobStatus

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class JobResponse(BaseModel):
    id: int
    repository_id: int
    status: JobStatus
    created_at: datetime
    error_message: Optional[str] = None
    class Config:
        orm_mode = True

class RepositoryCreate(BaseModel):
    url: str

class RepositoryResponse(BaseModel):
    id: int
    full_name: str
    url: str
    created_at: datetime
    jobs: List[JobResponse] = []
    class Config:
        orm_mode = True
