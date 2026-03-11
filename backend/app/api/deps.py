from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db import get_db
from app.models.user import User
from app.services.auth_service import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    从 JWT 中解析当前用户（sub = email）
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效或已过期",
        )

    email: str | None = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少 sub",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)):
    """
    先生（teacher）権限校验
    兼容旧数据中的 admin 角色
    """
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="先生権限が必要です",
        )

    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }
