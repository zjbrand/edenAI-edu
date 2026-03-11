from __future__ import annotations

import random
from sqlalchemy.orm import Session

from app.models.user import User

# 生徒向け（登録時に選択可能）
STUDENT_AVATARS = [
    "🐶", "🐱", "🐰", "🐼", "🐨",
    "🦊", "🐯", "🐸", "🐵", "🐧",
    "🐙", "🦄", "🐻", "🐮", "🐤",
    "🐺", "🐷", "🦁", "🐹", "🐳",
]

# 先生向け（重複しないように割当）
TEACHER_AVATARS = [
    "👨‍🏫", "👩‍🏫", "🧓", "👴", "👵",
    "👨", "👩", "🧔", "👨‍💼", "👩‍💼",
]


def is_teacher_role(role: str) -> bool:
    return role in ("teacher", "admin")


def choose_student_avatar(requested: str | None = None) -> str:
    if requested and requested in STUDENT_AVATARS:
        return requested
    return random.choice(STUDENT_AVATARS)


def choose_teacher_avatar(db: Session, exclude_user_id: int | None = None) -> str:
    query = db.query(User).filter(User.role.in_(["teacher", "admin"]))
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)

    used = {u.avatar for u in query.all() if u.avatar}
    candidates = [a for a in TEACHER_AVATARS if a not in used]
    if candidates:
        return random.choice(candidates)
    return random.choice(TEACHER_AVATARS)


def ensure_teacher_avatar(db: Session, user: User) -> bool:
    if not is_teacher_role(user.role):
        return False

    avatar_occupied = False
    if user.avatar:
        avatar_occupied = (
            db.query(User)
            .filter(User.id != user.id)
            .filter(User.role.in_(["teacher", "admin"]))
            .filter(User.avatar == user.avatar)
            .first()
            is not None
        )

    if user.avatar and user.avatar in TEACHER_AVATARS and not avatar_occupied:
        return False

    user.avatar = choose_teacher_avatar(db, exclude_user_id=user.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return True
