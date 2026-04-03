from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db import Base


class AIUnansweredMessage(Base):
    __tablename__ = "ai_unanswered_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String, nullable=False, default="プログラミング")
    question = Column(Text, nullable=False)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
