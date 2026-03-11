# backend/app/services/knowledge_service.py
# ナレッジ読み込み＆簡易検索（DB + 静的ファイル）

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDoc
from app.settings import settings

logger = logging.getLogger("edenai.knowledge")

# メモリ上のシンプルなキャッシュ（行単位）
_KNOWLEDGE_LINES: List[str] = []

DATA_DIR = Path(settings.KNOWLEDGE_STATIC_DIR)
SUPPORTED = {".txt", ".md", ".markdown"}


def _read_text_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return p.read_text(encoding="utf-8", errors="ignore")


def load_all_knowledge(db: Optional[Session] = None) -> List[str]:
    """
    Load knowledge from enabled sources:
    1) static files
    2) database knowledge_docs(status='active')
    """
    texts: List[str] = []

    if settings.KNOWLEDGE_ENABLE_STATIC and DATA_DIR.exists():
        for p in sorted(DATA_DIR.glob("*")):
            if p.is_file() and p.suffix.lower() in SUPPORTED:
                texts.append(_read_text_file(p))

    if settings.KNOWLEDGE_ENABLE_DB and db is not None:
        docs = db.query(KnowledgeDoc).filter(KnowledgeDoc.status == "active").all()
        for d in docs:
            if d.content:
                texts.append(d.content)

    return texts


def reload_knowledge_cache(db: Optional[Session] = None) -> None:
    global _KNOWLEDGE_LINES

    texts = load_all_knowledge(db=db)

    lines: List[str] = []
    for t in texts:
        for line in t.splitlines():
            s = line.strip()
            if s:
                lines.append(s)

    _KNOWLEDGE_LINES = lines
    logger.info(
        "knowledge source config=%s",
        {
            "db": settings.KNOWLEDGE_ENABLE_DB,
            "static": settings.KNOWLEDGE_ENABLE_STATIC,
            "static_dir": str(DATA_DIR),
        },
    )
    logger.debug("knowledge sample lines=%s", _KNOWLEDGE_LINES[:20])
    logger.info("knowledge loaded lines=%s", len(_KNOWLEDGE_LINES))


def _normalize_query(query: str) -> str:
    q = query.strip()
    q = re.sub(r"[？\?！!。、．\.,\s・]", "", q)
    return q


def get_relevant_context(query: str, top_k: int = 10) -> str:
    if not _KNOWLEDGE_LINES:
        return ""

    q_norm = _normalize_query(query)
    if not q_norm:
        return "\n".join(_KNOWLEDGE_LINES[:top_k])

    chars = list(dict.fromkeys(q_norm))

    scored_indices: List[tuple[float, int]] = []

    for idx, line in enumerate(_KNOWLEDGE_LINES):
        line_norm = _normalize_query(line)
        if not line_norm:
            continue

        raw_score = sum(1 for c in chars if c in line_norm)
        if raw_score == 0:
            continue

        length = max(5, len(line_norm))
        score = raw_score / (length ** 0.5)

        scored_indices.append((score, idx))

    if not scored_indices:
        return "\n".join(_KNOWLEDGE_LINES[:top_k])

    scored_indices.sort(key=lambda x: x[0], reverse=True)

    picked_lines: List[str] = []
    used_idx: set[int] = set()

    for score, idx in scored_indices:
        if len(picked_lines) >= top_k:
            break

        for j in (idx - 1, idx, idx + 1):
            if 0 <= j < len(_KNOWLEDGE_LINES) and j not in used_idx:
                picked_lines.append(_KNOWLEDGE_LINES[j])
                used_idx.add(j)
                if len(picked_lines) >= top_k:
                    break

    return "\n".join(picked_lines)
