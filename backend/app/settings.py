from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

# backend/.env を優先読み込みし、なければルート .env を利用
backend_env = BACKEND_DIR / ".env"
root_env = REPO_ROOT / ".env"
if backend_env.exists():
    load_dotenv(backend_env)
elif root_env.exists():
    load_dotenv(root_env)


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "EdenAI Teacher API")
    ENV: str = os.getenv("ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # API ドキュメント（本番はデフォルト無効）
    ENABLE_DOCS: bool = _to_bool(
        os.getenv("ENABLE_DOCS"),
        default=(ENV != "production"),
    )

    # CORS 許可オリジン
    CORS_ORIGINS: List[str] = _split_csv(
        os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
    )

    # Host ヘッダー検証（本番は実ドメインのみを推奨）
    TRUSTED_HOSTS: List[str] = _split_csv(
        os.getenv(
            "TRUSTED_HOSTS",
            "localhost,127.0.0.1",
        )
    )

    # 認証
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # セキュリティ切替
    ALLOW_PLAINTEXT_PASSWORD_COMPAT: bool = _to_bool(
        os.getenv("ALLOW_PLAINTEXT_PASSWORD_COMPAT"),
        default=False,
    )

    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ナレッジソース切替
    KNOWLEDGE_ENABLE_DB: bool = _to_bool(
        os.getenv("KNOWLEDGE_ENABLE_DB"),
        default=True,
    )
    # 本番では静的ファイル読込を既定で無効化
    KNOWLEDGE_ENABLE_STATIC: bool = _to_bool(
        os.getenv("KNOWLEDGE_ENABLE_STATIC"),
        default=(ENV != "production"),
    )
    KNOWLEDGE_STATIC_DIR: str = os.getenv(
        "KNOWLEDGE_STATIC_DIR",
        str(BACKEND_DIR / "app" / "data" / "company_docs"),
    )

    def validate(self) -> None:
        errors: list[str] = []

        if self.ENV == "production":
            weak_secrets = {"", "change-me-in-prod", "replace-with-a-strong-random-secret"}
            if self.JWT_SECRET_KEY in weak_secrets or len(self.JWT_SECRET_KEY) < 32:
                errors.append("JWT_SECRET_KEY が弱すぎます（32文字以上のランダム文字列を設定してください）。")

            if self.ALLOW_PLAINTEXT_PASSWORD_COMPAT:
                errors.append("本番環境では ALLOW_PLAINTEXT_PASSWORD_COMPAT=false にしてください。")

            if any("localhost" in o or "127.0.0.1" in o for o in self.CORS_ORIGINS):
                errors.append("本番環境の CORS_ORIGINS に localhost を含めないでください。")

            if not self.TRUSTED_HOSTS or "*" in self.TRUSTED_HOSTS:
                errors.append("本番環境では TRUSTED_HOSTS に実ドメインを明示してください。")

            if not self.DATABASE_URL:
                errors.append("本番環境では DATABASE_URL が必須です。")

        if errors:
            joined = "\n- " + "\n- ".join(errors)
            raise RuntimeError("設定検証エラー:" + joined)


settings = Settings()
