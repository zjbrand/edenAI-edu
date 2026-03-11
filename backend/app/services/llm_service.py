import logging
import os
from typing import Dict, List, Optional

import httpx

from .knowledge_service import get_relevant_context

logger = logging.getLogger("edenai.llm")

# Groq 設定
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """
你是一位耐心、讲解清楚的编程老师，同时非常了解我们公司的内部情况。

如果系统提供了“公司知识库内容”，你必须：
1. 优先参考知识库中的信息；
2. 在回答中体现公司知识库的要点；
3. 如果知识库里没有相关内容，才使用通用知识，但要注明。

回答结构：
- 先给出【简洁的结论】。
- 再给出【详细解释】。
- 若属于公司业务，请引用知识库内容。
"""


def build_messages(
    question: str,
    subject: Optional[str],
    history: List[Dict[str, str]],
    context: Optional[str] = None,
):
    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    if context:
        kb_block = "下面是与公司业务相关的知识库内容，请结合参考回答：\n" + context
        messages.append({"role": "system", "content": kb_block})

    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    user_content = question
    if subject:
        user_content = f"[科目: {subject}]\n{question}"
    messages.append({"role": "user", "content": user_content})

    return messages


def ask_llm(
    question: str,
    subject: Optional[str] = None,
    history: List[Dict[str, str]] = None,
) -> str:
    history = history or []

    if not GROQ_API_KEY:
        return "后端配置错误：请先在 .env 中设置 GROQ_API_KEY。"

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
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        logger.warning("Groq HTTP error status=%s", e.response.status_code)
        return f"调用 Groq 接口失败：HTTP {e.response.status_code}，详情：{e.response.text[:200]}"
    except Exception as e:
        logger.exception("Groq call failed: %s", e)
        return f"调用 Groq 接口时发生错误：{e}"

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.exception("Groq response parse failed: %s", e)
        return f"解析 Groq 返回内容时出错：{e}；原始响应：{data}"
