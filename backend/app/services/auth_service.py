# backend/app/services/auth_service.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

from app.models.user import User
from app.settings import settings
from app.services.avatar_service import choose_student_avatar

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordTooLongError(ValueError):
    """パスワードが bcrypt の 72 バイト制限を超えたときのエラー"""


class InactiveUserError(ValueError):
    """停止中ユーザーがログインしようとしたときのエラー"""


def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except ValueError as e:
        if "password cannot be longer than 72 bytes" in str(e):
            raise PasswordTooLongError("パスワードは72バイト以内で入力してください。") from e
        raise


def _allow_plaintext_fallback() -> bool:
    return settings.ALLOW_PLAINTEXT_PASSWORD_COMPAT or settings.ENV != "production"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if _allow_plaintext_fallback() and not hashed_password.startswith("$2"):
        return plain_password == hashed_password

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        if _allow_plaintext_fallback():
            return plain_password == hashed_password
        return False
    except ValueError as e:
        if "password cannot be longer than 72 bytes" in str(e):
            raise PasswordTooLongError("パスワードは72バイト以内で入力してください。") from e
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str | None = None,
    avatar: str | None = None,
) -> User:
    existing = get_user_by_email(db, email=email)
    if existing:
        raise ValueError("このメールアドレスは既に登録されています。")

    hashed_pw = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_pw,
        full_name=full_name,
        avatar=choose_student_avatar(avatar),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None

    if not user.is_active:
        raise InactiveUserError("権限を失ったため、ログインできません。")

    if not verify_password(password, user.hashed_password):
        return None

    return user


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
