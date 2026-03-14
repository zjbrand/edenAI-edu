from app.db import SessionLocal
from app.models import User
from app.core.security import get_password_hash

db = SessionLocal()

user = User(
    email="admin@example.com",
    full_name="Admin",
    hashed_password=get_password_hash("123456789"),
    role="teacher",
    is_active=True
)

db.add(user)
db.commit()
db.close()
