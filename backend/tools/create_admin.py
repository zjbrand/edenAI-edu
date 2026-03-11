# Deprecated compatibility script.
# Use: python -m app.tools.create_teacher --email ... --password ...

from app.db import SessionLocal
from app.models.user import User
from app.services.auth_service import get_password_hash

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "123456789"
ADMIN_NAME = "Admin"


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        hashed = get_password_hash(ADMIN_PASSWORD)

        if user:
            user.hashed_password = hashed
            user.full_name = ADMIN_NAME
            user.role = "teacher"
            user.is_active = True
            action = "updated"
        else:
            user = User(
                email=ADMIN_EMAIL,
                hashed_password=hashed,
                full_name=ADMIN_NAME,
                role="teacher",
                is_active=True,
            )
            db.add(user)
            action = "created"

        db.commit()
        print(f"Teacher account {action}: {ADMIN_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
