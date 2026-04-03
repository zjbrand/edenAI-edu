from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.ai_feedback import AIResponseFeedback
from app.models.ai_unanswered import AIUnansweredMessage
from app.models.schemas import (
    AIResponseRatingRequest,
    AIResponseRatingResponse,
    AskRequest,
    AskResponse,
)
from app.models.user import User
from app.services.llm_service import LLMServiceError, LLMServiceTimeoutError, ask_llm
from app.api.messages import _list_teacher_ids, _push_refresh_event


router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = [msg.dict() for msg in request.history]

    try:
        answer = ask_llm(
            question=request.question,
            subject=request.subject,
            history=history,
        )
    except (LLMServiceTimeoutError, LLMServiceError) as e:
        unanswered = AIUnansweredMessage(
            user_id=current_user.id,
            subject=request.subject,
            question=request.question,
            failure_reason=str(e),
        )
        db.add(unanswered)
        db.commit()
        _push_refresh_event(db, _list_teacher_ids(db), "unanswered_created")
        return AskResponse(
            answer="AIから5分以内に回答を取得できませんでした。先生へ未回答メッセージとして共有しました。メッセージ画面で先生からの返信をお待ちください。",
            response_id=None,
        )

    if not answer.strip():
        unanswered = AIUnansweredMessage(
            user_id=current_user.id,
            subject=request.subject,
            question=request.question,
            failure_reason="AI回答が空文字でした。",
        )
        db.add(unanswered)
        db.commit()
        _push_refresh_event(db, _list_teacher_ids(db), "unanswered_created")
        return AskResponse(
            answer="AIの回答が取得できなかったため、先生へ未回答メッセージとして共有しました。メッセージ画面で返信をお待ちください。",
            response_id=None,
        )

    feedback = AIResponseFeedback(
        user_id=current_user.id,
        subject=request.subject,
        question=request.question,
        answer=answer,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return AskResponse(answer=answer, response_id=feedback.id)


@router.post("/ask-feedback", response_model=AIResponseRatingResponse)
def rate_ai_response(
    payload: AIResponseRatingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="評価は1〜5の範囲で入力してください。")

    feedback = (
        db.query(AIResponseFeedback)
        .filter(
            AIResponseFeedback.id == payload.response_id,
            AIResponseFeedback.user_id == current_user.id,
        )
        .first()
    )
    if not feedback:
        raise HTTPException(status_code=404, detail="対象のAI回答が見つかりません。")

    feedback.rating = payload.rating
    feedback.rated_at = datetime.utcnow()
    db.add(feedback)
    db.commit()

    return AIResponseRatingResponse(
        ok=True,
        response_id=feedback.id,
        rating=payload.rating,
    )
