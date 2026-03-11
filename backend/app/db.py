# backend/app/db.py
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 環境変数 DATABASE_URL があればそれを優先
# 例: postgres://USER:PASSWORD@HOST:PORT/DBNAME
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./eden_teacher.db")

# Postgres URL を SQLAlchemy 形式へ変換
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

is_sqlite = DATABASE_URL.startswith("sqlite")

# SQLite のときだけ check_same_thread が必要
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=not is_sqlite,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
