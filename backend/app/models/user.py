# backend/app/models/user.py
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    role = Column(String, nullable=False, default="student")
    is_active = Column(Boolean, nullable=False, default=True)
