import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.code_review_history import CodeReviewHistory
from app.models.user import User
from app.services.code_review_service import review_code_submission

router = APIRouter(prefix="/api/code-review", tags=["code-review"])


class CodeReviewRequest(BaseModel):
    code: str


class CodeReviewResponse(BaseModel):
    history_id: int | None = None
    is_code: bool
    message: str
    correctness: int
    style: int
    efficiency: int
    total_score: int
    issues: list[str]
    improvements: list[str]
    llm_feedback: str | None = None


class CodeReviewHistorySummary(BaseModel):
    id: int
    title: str
    total_score: int
    updated_at: str
    preview: str


class CodeReviewHistoryDetail(CodeReviewResponse):
    id: int
    title: str
    code: str
    updated_at: str


class CodeReviewHistoryRenameRequest(BaseModel):
    title: str


def _build_history_title(code: str) -> str:
    first = next((line.strip() for line in code.splitlines() if line.strip()), "")
    if len(first) <= 28:
        return first or "新しい採点"
    return first[:28] + "..."


@router.post("/score", response_model=CodeReviewResponse)
def score_code(
    payload: CodeReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = review_code_submission(payload.code)
    history = CodeReviewHistory(
        user_id=current_user.id,
        title=_build_history_title(payload.code),
        code=payload.code,
        is_code=result["is_code"],
        message=result["message"],
        correctness=result["correctness"],
        style=result["style"],
        efficiency=result["efficiency"],
        total_score=result["total_score"],
        issues_json=json.dumps(result["issues"], ensure_ascii=False),
        improvements_json=json.dumps(result["improvements"], ensure_ascii=False),
        llm_feedback=result.get("llm_feedback"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return CodeReviewResponse(history_id=history.id, **result)


@router.get("/history", response_model=list[CodeReviewHistorySummary])
def list_code_review_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(CodeReviewHistory)
        .filter(CodeReviewHistory.user_id == current_user.id)
        .order_by(CodeReviewHistory.updated_at.desc())
        .all()
    )
    return [
        CodeReviewHistorySummary(
            id=row.id,
            title=row.title,
            total_score=row.total_score,
            updated_at=row.updated_at.isoformat(),
            preview=(row.llm_feedback or row.message or "")[:80],
        )
        for row in rows
    ]


@router.get("/history/{history_id}", response_model=CodeReviewHistoryDetail)
def get_code_review_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(CodeReviewHistory)
        .filter(CodeReviewHistory.id == history_id, CodeReviewHistory.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="採点履歴が見つかりません。")

    return CodeReviewHistoryDetail(
        id=row.id,
        title=row.title,
        code=row.code,
        updated_at=row.updated_at.isoformat(),
        history_id=row.id,
        is_code=row.is_code,
        message=row.message,
        correctness=row.correctness,
        style=row.style,
        efficiency=row.efficiency,
        total_score=row.total_score,
        issues=json.loads(row.issues_json or "[]"),
        improvements=json.loads(row.improvements_json or "[]"),
        llm_feedback=row.llm_feedback,
    )


@router.patch("/history/{history_id}")
def rename_code_review_history(
    history_id: int,
    payload: CodeReviewHistoryRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="履歴名を入力してください。")

    row = (
        db.query(CodeReviewHistory)
        .filter(CodeReviewHistory.id == history_id, CodeReviewHistory.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="採点履歴が見つかりません。")

    row.title = title[:80]
    row.updated_at = datetime.utcnow()
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id, "title": row.title}


@router.delete("/history/{history_id}")
def delete_code_review_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(CodeReviewHistory)
        .filter(CodeReviewHistory.id == history_id, CodeReviewHistory.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="採点履歴が見つかりません。")

    db.delete(row)
    db.commit()
    return {"ok": True, "id": history_id}
