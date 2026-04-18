import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.test_answer_history import TestAnswerAnalysisHistory
from app.models.user import User
from app.services.test_answer_service import analyze_test_answer

router = APIRouter(prefix="/api/test-answer-analysis", tags=["test-answer-analysis"])


class TestAnswerAnalysisRequest(BaseModel):
    question: str
    user_answer: str


class TestAnswerAnalysisResponse(BaseModel):
    history_id: int | None = None
    judgement: str
    issues: list[str]
    suggestions: list[str]
    correct_answer: str
    feedback: str


class TestAnswerHistorySummary(BaseModel):
    id: int
    title: str
    judgement: str
    updated_at: str
    preview: str


class TestAnswerHistoryDetail(TestAnswerAnalysisResponse):
    id: int
    title: str
    question: str
    user_answer: str
    updated_at: str


class TestAnswerHistoryRenameRequest(BaseModel):
    title: str


def _build_history_title(question: str) -> str:
    first = next((line.strip() for line in question.splitlines() if line.strip()), "")
    if len(first) <= 28:
        return first or "新しい分析"
    return first[:28] + "..."


@router.post("/analyze", response_model=TestAnswerAnalysisResponse)
def analyze_answer(
    payload: TestAnswerAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = analyze_test_answer(payload.question, payload.user_answer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    history = TestAnswerAnalysisHistory(
        user_id=current_user.id,
        title=_build_history_title(payload.question),
        question=payload.question,
        user_answer=payload.user_answer,
        judgement=result["judgement"],
        issues_json=json.dumps(result["issues"], ensure_ascii=False),
        suggestions_json=json.dumps(result["suggestions"], ensure_ascii=False),
        correct_answer=result["correct_answer"],
        feedback=result["feedback"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return TestAnswerAnalysisResponse(history_id=history.id, **result)


@router.get("/history", response_model=list[TestAnswerHistorySummary])
def list_test_answer_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(TestAnswerAnalysisHistory)
        .filter(TestAnswerAnalysisHistory.user_id == current_user.id)
        .order_by(TestAnswerAnalysisHistory.updated_at.desc())
        .all()
    )
    return [
        TestAnswerHistorySummary(
            id=row.id,
            title=row.title,
            judgement=row.judgement,
            updated_at=row.updated_at.isoformat(),
            preview=(row.feedback or row.correct_answer or "")[:80],
        )
        for row in rows
    ]


@router.get("/history/{history_id}", response_model=TestAnswerHistoryDetail)
def get_test_answer_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(TestAnswerAnalysisHistory)
        .filter(
            TestAnswerAnalysisHistory.id == history_id,
            TestAnswerAnalysisHistory.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="解答分析履歴が見つかりません。")

    return TestAnswerHistoryDetail(
        id=row.id,
        title=row.title,
        question=row.question,
        user_answer=row.user_answer,
        updated_at=row.updated_at.isoformat(),
        history_id=row.id,
        judgement=row.judgement,
        issues=json.loads(row.issues_json or "[]"),
        suggestions=json.loads(row.suggestions_json or "[]"),
        correct_answer=row.correct_answer,
        feedback=row.feedback,
    )


@router.patch("/history/{history_id}")
def rename_test_answer_history(
    history_id: int,
    payload: TestAnswerHistoryRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="履歴名を入力してください。")

    row = (
        db.query(TestAnswerAnalysisHistory)
        .filter(
            TestAnswerAnalysisHistory.id == history_id,
            TestAnswerAnalysisHistory.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="解答分析履歴が見つかりません。")

    row.title = title[:80]
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id, "title": row.title}


@router.delete("/history/{history_id}")
def delete_test_answer_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(TestAnswerAnalysisHistory)
        .filter(
            TestAnswerAnalysisHistory.id == history_id,
            TestAnswerAnalysisHistory.user_id == current_user.id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="解答分析履歴が見つかりません。")

    db.delete(row)
    db.commit()
    return {"ok": True, "id": history_id}
