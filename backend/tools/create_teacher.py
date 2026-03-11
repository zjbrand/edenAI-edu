from __future__ import annotations

import argparse

from app.db import SessionLocal
from app.models.user import User
from app.services.auth_service import get_password_hash


def upsert_teacher(email: str, password: str, full_name: str | None):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        hashed_password = get_password_hash(password)

        if user:
            user.hashed_password = hashed_password
            user.full_name = full_name
            user.role = "teacher"
            user.is_active = True
            action = "updated"
        else:
            user = User(
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                role="teacher",
                is_active=True,
            )
            db.add(user)
            action = "created"

        db.commit()
        db.refresh(user)

        print({
            "action": action,
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
        })
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Create/update a teacher user")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default="Teacher")
    args = parser.parse_args()

    upsert_teacher(args.email, args.password, args.full_name)


if __name__ == "__main__":
    main()
