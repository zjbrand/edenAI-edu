import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

from app.api.admin import router as admin_router
from app.api.admin_knowledge import router as admin_knowledge_router
from app.api.admin_system import router as admin_system_router
from app.api.admin_users import router as admin_users_router
from app.api.ask import router as ask_router
from app.api.auth import router as auth_router
from app.api.code_review import router as code_review_router
from app.api.messages import router as messages_router
from app.db import Base, engine, get_db
from app.models.knowledge import KnowledgeDoc  # noqa: F401
from app.models.message import DirectMessage  # noqa: F401
from app.models.ai_feedback import AIResponseFeedback  # noqa: F401
from app.models.chat_history import AIChatMessage, AIChatSession  # noqa: F401
from app.models.code_review_history import CodeReviewHistory  # noqa: F401
from app.models.ai_unanswered import AIUnansweredMessage  # noqa: F401
from app.models.user import User  # noqa: F401
from app.services.knowledge_service import reload_knowledge_cache
from app.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("edenai")

app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.TRUSTED_HOSTS or ["localhost", "127.0.0.1"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(ask_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_knowledge_router)
app.include_router(admin_users_router)
app.include_router(admin_system_router)
app.include_router(messages_router)
app.include_router(code_review_router)


def _ensure_avatar_column() -> None:
    with engine.begin() as conn:
        dialect = engine.dialect.name
        if dialect == "sqlite":
            cols = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            names = {row[1] for row in cols}
            if "avatar" not in names:
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR"))
        elif dialect.startswith("postgresql"):
            row = conn.execute(
                text(
                    """
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users' AND column_name='avatar'
                    """
                )
            ).first()
            if not row:
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR"))


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready")
def readiness_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.exception("readiness check failed: %s", e)
        return {"status": "ng", "db": "down"}
    return {"status": "ok", "db": "up"}


@app.on_event("startup")
def on_startup():
    settings.validate()
    Base.metadata.create_all(bind=engine)
    _ensure_avatar_column()
    with next(get_db()) as db:
        reload_knowledge_cache(db=db)
    logger.info("startup completed (env=%s)", settings.ENV)
