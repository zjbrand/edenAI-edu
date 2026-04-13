from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.db import Base


class CodeReviewHistory(Base):
    __tablename__ = "code_review_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    is_code = Column(Boolean, nullable=False, default=True)
    message = Column(Text, nullable=False)
    correctness = Column(Integer, nullable=False, default=0)
    style = Column(Integer, nullable=False, default=0)
    efficiency = Column(Integer, nullable=False, default=0)
    total_score = Column(Integer, nullable=False, default=0)
    issues_json = Column(Text, nullable=False, default="[]")
    improvements_json = Column(Text, nullable=False, default="[]")
    llm_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
