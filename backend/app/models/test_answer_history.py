from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.db import Base


class TestAnswerAnalysisHistory(Base):
    __tablename__ = "test_answer_analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=False)
    judgement = Column(String, nullable=False, default="不完全")
    issues_json = Column(Text, nullable=False, default="[]")
    suggestions_json = Column(Text, nullable=False, default="[]")
    correct_answer = Column(Text, nullable=False, default="")
    feedback = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
