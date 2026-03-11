# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_access_token,
    verify_password,
    get_password_hash,
    PasswordTooLongError,
    InactiveUserError,
)
from app.services.avatar_service import ensure_teacher_avatar

from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    avatar: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    role: str
    avatar: str | None = None


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        create_user(
            db=db,
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
            avatar=payload.avatar,
        )
    except PasswordTooLongError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return {"msg": "ユーザーを作成しました。"}


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form_data.username
    password = form_data.password

    try:
        user = authenticate_user(db, email=email, password=password)
    except PasswordTooLongError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except InactiveUserError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="メールアドレスまたはパスワードが正しくありません。",
        )

    # 先生は未設定時にアバターを自動割当（重複回避）
    ensure_teacher_avatar(db, user)

    token = create_access_token({"sub": user.email, "email": user.email})

    return TokenResponse(access_token=token, token_type="bearer")


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        avatar=current_user.avatar,
    )


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="現在のパスワードが正しくありません")

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(current_user)
    db.commit()

    return {"ok": True}
