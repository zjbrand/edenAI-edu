# backend/app/models/schemas.py
from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel
from pydantic import ConfigDict


# ========== 聊天 / 提问相关 ==========

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskRequest(BaseModel):
    question: str
    subject: str
    history: List[HistoryMessage] = []


class AskResponse(BaseModel):
    answer: str
    response_id: int | None = None


class AIResponseRatingRequest(BaseModel):
    response_id: int
    rating: int


class AIResponseRatingResponse(BaseModel):
    ok: bool
    response_id: int
    rating: int


# ========== 用户 / 登录相关 ==========

class UserBase(BaseModel):
    email: str
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(UserBase):
    id: int
    created_at: datetime

    # Pydantic v2: 替代 orm_mode = True
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
