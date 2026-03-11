# backend/app/api/admin_users.py
# 先生向け：生徒一覧 / 権限変更 / 停止

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.services.avatar_service import ensure_teacher_avatar

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


class UserItem(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None


@router.get("", response_model=List[UserItem])
def list_users(_: dict = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserItem(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            avatar=u.avatar,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else None,
        )
        for u in users
    ]


class RoleUpdate(BaseModel):
    role: str  # "student" or "teacher"（旧: "user" / "admin" 互換）


@router.patch("/{user_id}/role", response_model=UserItem)
def update_role(
    user_id: int,
    payload: RoleUpdate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    role_map = {
        "teacher": "teacher",
        "student": "student",
        "admin": "teacher",
        "user": "student",
    }

    normalized_role = role_map.get(payload.role)
    if not normalized_role:
        raise HTTPException(
            status_code=400,
            detail="role は 'student' または 'teacher'（旧: 'user'/'admin' も可）",
        )

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="生徒が見つかりません。")

    u.role = normalized_role
    db.commit()
    db.refresh(u)

    if normalized_role == "teacher":
        ensure_teacher_avatar(db, u)
        db.refresh(u)

    return UserItem(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        avatar=u.avatar,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at.isoformat() if u.created_at else None,
    )


class ActiveUpdate(BaseModel):
    is_active: bool


@router.patch("/{user_id}/active", response_model=UserItem)
def update_active(
    user_id: int,
    payload: ActiveUpdate,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="生徒が見つかりません。")

    u.is_active = bool(payload.is_active)
    db.commit()
    db.refresh(u)

    return UserItem(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        avatar=u.avatar,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at.isoformat() if u.created_at else None,
    )
