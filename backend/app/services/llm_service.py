from __future__ import annotations

import logging
from typing import Dict, List, Optional

import httpx

from app.settings import settings
from .knowledge_service import get_relevant_context

logger = logging.getLogger("edenai.llm")

GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_BASE_URL = settings.GROQ_BASE_URL
GROQ_MODEL = settings.GROQ_MODEL
LLM_REQUEST_TIMEOUT_SECONDS = 300.0


class LLMServiceError(Exception):
    """AI 応答に失敗したときの共通例外"""


class LLMServiceTimeoutError(LLMServiceError):
    """5分以内に応答が返らなかったときの例外"""


SYSTEM_PROMPT = """
あなたは丁寧で説明が分かりやすい日本語のプログラミング講師です。
同時に、社内業務や社内ルールも理解しているアシスタントとして振る舞ってください。

システムから「会社ナレッジ」が与えられた場合は、必ず次の方針に従ってください。
1. まず会社ナレッジを優先して参照する。
2. 回答の中に、参照した社内情報の要点を自然に反映する。
3. 会社ナレッジに十分な情報がない場合のみ、一般知識で補足する。
4. 社内情報と一般知識を混ぜる場合は、その区別が分かるように説明する。

回答は必ず日本語で、次の流れで行ってください。
- まず【結論】を簡潔に示す。
- 次に【詳細説明】で理由や手順を丁寧に説明する。
- 必要であれば、コード例や注意点を追加する。
""".strip()


def build_messages(
    question: str,
    subject: Optional[str],
    history: List[Dict[str, str]],
    context: Optional[str] = None,
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        kb_block = "以下は会社ナレッジです。必要に応じて優先参照して回答してください。\n" + context
        messages.append({"role": "system", "content": kb_block})

    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = question
    if subject:
        user_content = f"[回答言語: 日本語]\n[科目: {subject}]\n{question}"
    else:
        user_content = f"[回答言語: 日本語]\n{question}"
    messages.append({"role": "user", "content": user_content})

    return messages


def ask_llm(
    question: str,
    subject: Optional[str] = None,
    history: List[Dict[str, str]] | None = None,
) -> str:
    history = history or []

    if not GROQ_API_KEY:
        raise LLMServiceError("Groq API の設定が未完了です。")

    context = get_relevant_context(question, top_k=30)
    if context:
        logger.debug("knowledge hit lines=%s", len(context.splitlines()))
    else:
        logger.debug("knowledge hit empty")

    messages = build_messages(question, subject, history, context=context)

    url = GROQ_BASE_URL.rstrip("/") + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.4,
    }

    try:
        with httpx.Client(timeout=LLM_REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException as e:
        logger.warning("groq call timeout after %s seconds", LLM_REQUEST_TIMEOUT_SECONDS)
        raise LLMServiceTimeoutError("AIが5分以内に応答しませんでした。") from e
    except httpx.HTTPStatusError as e:
        logger.warning("groq http error status=%s", e.response.status_code)
        raise LLMServiceError(
            f"Groq API の呼び出しに失敗しました。HTTP {e.response.status_code}"
        ) from e
    except Exception as e:
        logger.exception("groq call failed: %s", e)
        raise LLMServiceError("Groq API への接続中にエラーが発生しました。") from e

    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception("groq response parse failed: %s", e)
        raise LLMServiceError("Groq API の応答解析に失敗しました。") from e

    logger.info("llm provider=groq model=%s", GROQ_MODEL)
    return content
