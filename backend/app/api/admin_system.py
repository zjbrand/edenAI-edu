# backend/app/api/admin_system.py
# 先生向け：システム状態

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db import get_db
from app.models.ai_feedback import AIResponseFeedback
from app.models.knowledge import KnowledgeDoc
from app.models.user import User
from app.services.llm_service import GROQ_API_KEY
from app.settings import settings

router = APIRouter(prefix="/admin/system", tags=["admin-system"])


@router.get("/status")
def system_status(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """システム状態"""
    user_count = db.query(User).count()
    student_count = db.query(User).filter(User.role.in_(["student", "user"])).count()
    teacher_count = db.query(User).filter(User.role.in_(["teacher", "admin"])).count()
    inactive_student_count = db.query(User).filter(User.role.in_(["student", "user"]), User.is_active == False).count()  # noqa: E712
    inactive_teacher_count = db.query(User).filter(User.role.in_(["teacher", "admin"]), User.is_active == False).count()  # noqa: E712
    doc_count = db.query(KnowledgeDoc).count()

    db_status = "ok"
    llm_status = "ok" if GROQ_API_KEY else "ng"
    vector_status = "ok" if (settings.KNOWLEDGE_ENABLE_DB or settings.KNOWLEDGE_ENABLE_STATIC) else "ng"

    return {
        "ok": db_status == "ok",
        "services": {
            # 既存画面互換
            "llm": llm_status,
            "vector_store": vector_status,
            # 運用確認向け
            "api": "ok",
            "db": db_status,
        },
        "stats": {
            "users": user_count,
            "student_count": student_count,
            "teacher_count": teacher_count,
            "inactive_student_count": inactive_student_count,
            "inactive_teacher_count": inactive_teacher_count,
            "knowledge_docs": doc_count,
        },
    }


@router.get("/ai-feedback")
def ai_feedback_summary(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    rated_query = db.query(AIResponseFeedback).filter(AIResponseFeedback.rating.isnot(None))
    total_reviews = rated_query.count()
    average_rating = rated_query.with_entities(func.avg(AIResponseFeedback.rating)).scalar() or 0
    total_responses = db.query(AIResponseFeedback).count()

    distribution = {}
    for stars in range(5, 0, -1):
        distribution[str(stars)] = (
            db.query(AIResponseFeedback)
            .filter(AIResponseFeedback.rating == stars)
            .count()
        )

    return {
        "average_rating": float(average_rating),
        "total_reviews": total_reviews,
        "total_responses": total_responses,
        "unrated_count": max(total_responses - total_reviews, 0),
        "distribution": distribution,
    }
