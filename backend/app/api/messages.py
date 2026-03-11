from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models.message import DirectMessage
from app.models.user import User

router = APIRouter(prefix="/messages", tags=["messages"])


def _is_teacher(role: str) -> bool:
    return role in ("teacher", "admin")


def _is_student(role: str) -> bool:
    return role in ("student", "user")


class TeacherItem(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    avatar: str | None = None


class SendMessageRequest(BaseModel):
    to_user_id: int
    content: str


class MessageItem(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    content: str
    is_read: bool
    created_at: str


class ConversationItem(BaseModel):
    user_id: int
    email: str
    full_name: str | None = None
    avatar: str | None = None
    role: str
    last_message: str
    last_at: str
    unread_count: int


@router.get("/teachers", response_model=List[TeacherItem])
def list_teachers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not _is_student(current_user.role):
        raise HTTPException(status_code=403, detail="生徒のみ利用できます。")

    teachers = (
        db.query(User)
        .filter(User.is_active == True)  # noqa: E712
        .filter(User.role.in_(["teacher", "admin"]))
        .order_by(User.created_at.desc())
        .all()
    )

    return [
        TeacherItem(id=t.id, email=t.email, full_name=t.full_name, avatar=t.avatar)
        for t in teachers
    ]


@router.post("/send", response_model=MessageItem)
def send_message(
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    text = payload.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="内容を入力してください。")

    recipient = db.query(User).filter(User.id == payload.to_user_id).first()
    if not recipient or not recipient.is_active:
        raise HTTPException(status_code=404, detail="送信先が見つかりません。")

    sender_is_teacher = _is_teacher(current_user.role)
    recipient_is_teacher = _is_teacher(recipient.role)

    if sender_is_teacher and recipient_is_teacher:
        raise HTTPException(status_code=400, detail="先生同士には送信できません。")
    if (not sender_is_teacher) and (not recipient_is_teacher):
        raise HTTPException(status_code=400, detail="生徒同士には送信できません。")

    msg = DirectMessage(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        content=text,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return MessageItem(
        id=msg.id,
        sender_id=msg.sender_id,
        recipient_id=msg.recipient_id,
        content=msg.content,
        is_read=msg.is_read,
        created_at=msg.created_at.isoformat(),
    )


@router.get("/conversations", response_model=List[ConversationItem])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DirectMessage)
        .filter(
            or_(
                DirectMessage.sender_id == current_user.id,
                DirectMessage.recipient_id == current_user.id,
            )
        )
        .order_by(DirectMessage.created_at.desc())
        .all()
    )

    if not rows:
        return []

    partner_ids: set[int] = set()
    for r in rows:
        partner_ids.add(r.recipient_id if r.sender_id == current_user.id else r.sender_id)

    users = db.query(User).filter(User.id.in_(partner_ids)).all()
    user_map = {u.id: u for u in users}

    # 新しい順に、各相手の先頭1件を最終メッセージとして採用
    conv_map: dict[int, ConversationItem] = {}
    for r in rows:
        partner_id = r.recipient_id if r.sender_id == current_user.id else r.sender_id
        if partner_id in conv_map:
            continue
        u = user_map.get(partner_id)
        if not u:
            continue

        unread_count = (
            db.query(DirectMessage)
            .filter(
                and_(
                    DirectMessage.sender_id == partner_id,
                    DirectMessage.recipient_id == current_user.id,
                    DirectMessage.is_read == False,  # noqa: E712
                )
            )
            .count()
        )

        conv_map[partner_id] = ConversationItem(
            user_id=u.id,
            email=u.email,
            full_name=u.full_name,
            avatar=u.avatar,
            role=u.role,
            last_message=r.content,
            last_at=r.created_at.isoformat(),
            unread_count=unread_count,
        )

    return list(conv_map.values())


@router.get("/conversations/{partner_id}", response_model=List[MessageItem])
def get_conversation(
    partner_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    partner = db.query(User).filter(User.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="相手ユーザーが見つかりません。")

    rows = (
        db.query(DirectMessage)
        .filter(
            or_(
                and_(
                    DirectMessage.sender_id == current_user.id,
                    DirectMessage.recipient_id == partner_id,
                ),
                and_(
                    DirectMessage.sender_id == partner_id,
                    DirectMessage.recipient_id == current_user.id,
                ),
            )
        )
        .order_by(DirectMessage.created_at.asc())
        .all()
    )

    return [
        MessageItem(
            id=r.id,
            sender_id=r.sender_id,
            recipient_id=r.recipient_id,
            content=r.content,
            is_read=r.is_read,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("/conversations/{partner_id}/read")
def mark_conversation_read(
    partner_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DirectMessage)
        .filter(
            and_(
                DirectMessage.sender_id == partner_id,
                DirectMessage.recipient_id == current_user.id,
                DirectMessage.is_read == False,  # noqa: E712
            )
        )
        .all()
    )

    for r in rows:
        r.is_read = True

    db.commit()
    return {"ok": True, "updated": len(rows)}


@router.get("/unread-count")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cnt = (
        db.query(DirectMessage)
        .filter(
            and_(
                DirectMessage.recipient_id == current_user.id,
                DirectMessage.is_read == False,  # noqa: E712
            )
        )
        .count()
    )
    return {"count": cnt}
