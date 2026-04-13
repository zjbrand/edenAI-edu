from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.ai_feedback import AIResponseFeedback
from app.models.ai_unanswered import AIUnansweredMessage
from app.models.chat_history import AIChatMessage, AIChatSession
from app.models.schemas import (
    AIResponseRatingRequest,
    AIResponseRatingResponse,
    AskRequest,
    AskResponse,
    ChatSessionDetail,
    ChatSessionMessage,
    ChatSessionRenameRequest,
    ChatSessionSummary,
)
from app.models.user import User
from app.services.llm_service import LLMServiceError, LLMServiceTimeoutError, ask_llm
from app.api.messages import _list_teacher_ids, _push_refresh_event


router = APIRouter(prefix="/api", tags=["ask"])


def _build_session_title(question: str) -> str:
    trimmed = " ".join(question.strip().split())
    if len(trimmed) <= 28:
        return trimmed or "新しい会話"
    return trimmed[:28] + "..."


def _get_session_or_404(db: Session, session_id: int, user_id: int) -> AIChatSession:
    session = (
        db.query(AIChatSession)
        .filter(AIChatSession.id == session_id, AIChatSession.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="会話履歴が見つかりません。")
    return session


def _save_chat_pair(
    db: Session,
    session: AIChatSession,
    question: str,
    answer: str,
    response_feedback_id: int | None = None,
) -> None:
    now = datetime.utcnow()
    db.add(
        AIChatMessage(
            session_id=session.id,
            role="user",
            content=question,
            created_at=now,
        )
    )
    db.add(
        AIChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            response_feedback_id=response_feedback_id,
            created_at=now,
        )
    )
    session.updated_at = now
    db.add(session)


@router.get("/chat-sessions", response_model=list[ChatSessionSummary])
def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(AIChatSession)
        .filter(AIChatSession.user_id == current_user.id)
        .order_by(AIChatSession.updated_at.desc())
        .all()
    )

    items: list[ChatSessionSummary] = []
    for session in sessions:
        last_message = (
            db.query(AIChatMessage)
            .filter(AIChatMessage.session_id == session.id)
            .order_by(AIChatMessage.created_at.desc())
            .first()
        )
        items.append(
            ChatSessionSummary(
                id=session.id,
                title=session.title,
                subject=session.subject,
                last_message=last_message.content if last_message else "",
                updated_at=session.updated_at.isoformat(),
            )
        )
    return items


@router.get("/chat-sessions/{session_id}", response_model=ChatSessionDetail)
def get_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session_or_404(db, session_id, current_user.id)

    rows = (
        db.query(AIChatMessage)
        .filter(AIChatMessage.session_id == session.id)
        .order_by(AIChatMessage.created_at.asc(), AIChatMessage.id.asc())
        .all()
    )

    messages: list[ChatSessionMessage] = []
    for row in rows:
        rating = None
        if row.response_feedback_id:
            feedback = db.query(AIResponseFeedback).filter(AIResponseFeedback.id == row.response_feedback_id).first()
            rating = feedback.rating if feedback else None
        messages.append(
            ChatSessionMessage(
                id=row.id,
                role=row.role,
                content=row.content,
                response_id=row.response_feedback_id,
                rating=rating,
                created_at=row.created_at.isoformat(),
            )
        )

    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        subject=session.subject,
        updated_at=session.updated_at.isoformat(),
        messages=messages,
    )


@router.patch("/chat-sessions/{session_id}")
def rename_chat_session(
    session_id: int,
    payload: ChatSessionRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="履歴名を入力してください。")

    session = _get_session_or_404(db, session_id, current_user.id)
    session.title = title[:80]
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()

    return {
        "ok": True,
        "id": session.id,
        "title": session.title,
    }


@router.delete("/chat-sessions/{session_id}")
def delete_chat_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session_or_404(db, session_id, current_user.id)

    feedback_ids = [
        row.response_feedback_id
        for row in db.query(AIChatMessage.response_feedback_id)
        .filter(AIChatMessage.session_id == session.id)
        .all()
        if row.response_feedback_id
    ]

    db.query(AIChatMessage).filter(AIChatMessage.session_id == session.id).delete()
    if feedback_ids:
        db.query(AIResponseFeedback).filter(AIResponseFeedback.id.in_(feedback_ids)).delete(synchronize_session=False)
    db.delete(session)
    db.commit()

    return {"ok": True, "id": session_id}


@router.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = [msg.dict() for msg in request.history]
    session = (
        _get_session_or_404(db, request.conversation_id, current_user.id)
        if request.conversation_id
        else AIChatSession(
            user_id=current_user.id,
            title=_build_session_title(request.question),
            subject=request.subject,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    )
    if not request.conversation_id:
        db.add(session)
        db.commit()
        db.refresh(session)
    else:
        session.subject = request.subject
        db.add(session)
        db.commit()

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
        _save_chat_pair(
            db,
            session,
            request.question,
            "AIから5分以内に回答を取得できませんでした。先生へ未回答メッセージとして共有しました。メッセージ画面で先生からの返信をお待ちください。",
        )
        db.commit()
        _push_refresh_event(db, _list_teacher_ids(db), "unanswered_created")
        return AskResponse(
            answer="AIから5分以内に回答を取得できませんでした。先生へ未回答メッセージとして共有しました。メッセージ画面で先生からの返信をお待ちください。",
            response_id=None,
            conversation_id=session.id,
        )

    if not answer.strip():
        unanswered = AIUnansweredMessage(
            user_id=current_user.id,
            subject=request.subject,
            question=request.question,
            failure_reason="AI回答が空文字でした。",
        )
        db.add(unanswered)
        _save_chat_pair(
            db,
            session,
            request.question,
            "AIの回答が取得できなかったため、先生へ未回答メッセージとして共有しました。メッセージ画面で返信をお待ちください。",
        )
        db.commit()
        _push_refresh_event(db, _list_teacher_ids(db), "unanswered_created")
        return AskResponse(
            answer="AIの回答が取得できなかったため、先生へ未回答メッセージとして共有しました。メッセージ画面で返信をお待ちください。",
            response_id=None,
            conversation_id=session.id,
        )

    feedback = AIResponseFeedback(
        user_id=current_user.id,
        subject=request.subject,
        question=request.question,
        answer=answer,
    )
    db.add(feedback)
    db.flush()
    _save_chat_pair(db, session, request.question, answer, response_feedback_id=feedback.id)
    db.commit()
    db.refresh(feedback)

    return AskResponse(answer=answer, response_id=feedback.id, conversation_id=session.id)


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
