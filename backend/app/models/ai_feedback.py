from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db import Base


class AIResponseFeedback(Base):
    __tablename__ = "ai_response_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String, nullable=False, default="プログラミング")
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    rated_at = Column(DateTime, nullable=True)
