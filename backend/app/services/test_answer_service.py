from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.services.llm_service import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    raw_text = _strip_code_fence(raw_text)
    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start >= 0 and end > start:
        block = raw_text[start : end + 1]
        try:
            parsed = json.loads(block)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


def _normalize_judgement(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "不完全"
    if "正" in text and "不" not in text and "誤" not in text:
        return "正しい"
    if "誤" in text or "違" in text:
        return "誤り"
    return "不完全"


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip(" -\u3000") for item in value if str(item).strip()]
    if isinstance(value, str):
        lines = []
        for line in value.splitlines():
            cleaned = line.strip(" -\u3000")
            if cleaned:
                lines.append(cleaned)
        if lines:
            return lines
    return []


def _call_groq(messages: list[dict[str, str]], temperature: float = 0.2) -> str:
    url = GROQ_BASE_URL.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": GROQ_MODEL,
        "temperature": temperature,
        "messages": messages,
    }

    with httpx.Client(timeout=90.0) as client:
        resp = client.post(
            url,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
    return str(data["choices"][0]["message"]["content"]).strip()


def _parse_sectioned_response(raw_text: str) -> dict[str, Any]:
    text = _strip_code_fence(raw_text)
    pattern = re.compile(
        r"\[判定\]\s*(?P<judgement>.*?)\s*"
        r"\[誤っている点・補足できる点\]\s*(?P<issues>.*?)\s*"
        r"\[改善提案\]\s*(?P<suggestions>.*?)\s*"
        r"\[正しい解答\]\s*(?P<correct_answer>.*?)\s*"
        r"\[AIフィードバック\]\s*(?P<feedback>.*)",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return {}

    return {
        "judgement": match.group("judgement").strip(),
        "issues": _normalize_list(match.group("issues")),
        "suggestions": _normalize_list(match.group("suggestions")),
        "correct_answer": match.group("correct_answer").strip(),
        "feedback": match.group("feedback").strip(),
    }


def _is_rich_enough(
    judgement: str,
    issues: list[str],
    suggestions: list[str],
    correct_answer: str,
    feedback: str,
) -> bool:
    return (
        len(judgement.strip()) > 0
        and len(issues) >= 2
        and len(suggestions) >= 2
        and len(correct_answer.strip()) >= 60
        and len(feedback.strip()) >= 60
    )


def _fallback_analysis(question: str, user_answer: str) -> dict[str, Any]:
    question_lines = [line.strip() for line in question.splitlines() if line.strip()]
    answer_lines = [line.strip() for line in user_answer.splitlines() if line.strip()]
    question_head = question_lines[0] if question_lines else "問題文"
    answer_head = answer_lines[0] if answer_lines else "答案が未入力です。"

    if not user_answer.strip():
        return {
            "judgement": "誤り",
            "issues": [
                "答案が入力されていないため、問題の理解度と解答方針を確認できません。",
                f"問題文の冒頭は「{question_head}」ですが、それに対する結論や説明がありません。",
            ],
            "suggestions": [
                "まず結論を1文で書き、その後に理由や根拠を2〜3文で補足してください。",
                "問題文の条件・キーワードを抜き出し、それぞれに対応する説明を入れてください。",
            ],
            "correct_answer": (
                "模範解答を正確に生成するには、問題の条件に対するあなたの考え方が必要です。\n"
                "まずは仮の解答でもよいので、結論・理由・補足の3要素で答案を書いてください。"
            ),
            "feedback": (
                "今回は答案が未入力のため、内容面の評価はできませんでした。"
                "ただし、問題に対して『何を問われているか』『どう答えるか』を分けて書けば、"
                "次回はより具体的な添削結果を返せます。"
            ),
        }

    return {
        "judgement": "不完全",
        "issues": [
            f"答案の冒頭は「{answer_head}」ですが、問題文「{question_head}」に対する根拠や条件整理が不足している可能性があります。",
            "AI接続または応答形式の問題により詳細分析ができなかったため、誤答箇所の洗い出しが十分ではありません。",
        ],
        "suggestions": [
            "結論、理由、具体例の順で書き直すと、答案の完成度をより正確に評価できます。",
            "問題文に含まれる条件や用語をそのまま使って説明すると、論点のずれを防ぎやすくなります。",
        ],
        "correct_answer": (
            f"問題文の中心テーマは「{question_head}」です。\n"
            "再分析時には、このテーマに対して条件整理、要点説明、結論の3段構成で模範解答を生成します。"
        ),
        "feedback": (
            "今回はAIの詳細解析結果を取得できなかったため、部分的な添削結果を表示しています。"
            "ただし、あなたの答案と問題文の対応関係をもう少し明示すれば、次回はより具体的な誤り分析と模範解答が返せます。"
        ),
    }


def analyze_test_answer(question: str, user_answer: str) -> dict[str, Any]:
    if not question.strip():
        raise ValueError("問題を入力してください。")
    if not user_answer.strip():
        raise ValueError("あなたの答案を入力してください。")
    if not GROQ_API_KEY:
        return _fallback_analysis(question, user_answer)

    user_content = f"【問題】\n{question.strip()}\n\n【あなたの答案】\n{user_answer.strip()}"

    json_prompt = (
        "あなたは日本語で答案添削を行う、丁寧で具体的な講師です。"
        "返答は必ずJSONのみで、以下のキーを含めてください。"
        'judgement: "正しい" または "不完全" または "誤り"、'
        "issues: 文字列配列、suggestions: 文字列配列、correct_answer: 文字列、feedback: 文字列。"
        "重要: 内容を一般論にせず、必ず問題文と答案の内容に触れて具体的に書いてください。"
        "issues は最低3件、各項目は1〜2文で、"
        "『どこが不足・誤りか』『どの条件が抜けているか』を具体的に指摘してください。"
        "suggestions は最低3件、各項目は1〜2文で、"
        "『どう直せばよいか』『どの観点を追加すべきか』を具体的に書いてください。"
        "correct_answer は問題に対する模範解答として、"
        "結論、理由、必要なら具体例を含めた十分に詳しい日本語で書いてください。"
        "feedback は判定理由、よかった点、弱い点、次に何を直すべきかを含む80文字以上の文章で書いてください。"
    )

    try:
        content = _call_groq(
            [
                {"role": "system", "content": json_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.15,
        )
        obj = _extract_json_object(content) or {}
        judgement = _normalize_judgement(obj.get("judgement"))
        issues = _normalize_list(obj.get("issues"))[:6]
        suggestions = _normalize_list(obj.get("suggestions"))[:6]
        correct_answer = str(obj.get("correct_answer") or "").strip()
        feedback = str(obj.get("feedback") or obj.get("analysis") or "").strip()

        if _is_rich_enough(judgement, issues, suggestions, correct_answer, feedback):
            return {
                "judgement": judgement,
                "issues": issues,
                "suggestions": suggestions,
                "correct_answer": correct_answer,
                "feedback": feedback,
            }
    except Exception:
        pass

    section_prompt = (
        "あなたは日本語で答案添削を行う講師です。"
        "以下の見出しをそのまま使い、具体的で内容豊富に回答してください。"
        "各項目は必ず問題文と答案の具体的な内容に触れてください。\n\n"
        "[判定]\n"
        "正しい / 不完全 / 誤り のいずれか1つ\n\n"
        "[誤っている点・補足できる点]\n"
        "- 具体的な指摘を最低3件\n\n"
        "[改善提案]\n"
        "- 具体的な改善案を最低3件\n\n"
        "[正しい解答]\n"
        "模範解答を十分に詳しく\n\n"
        "[AIフィードバック]\n"
        "判定理由、良い点、弱い点、次の改善行動を80文字以上でまとめる"
    )

    try:
        content = _call_groq(
            [
                {"role": "system", "content": section_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        parsed = _parse_sectioned_response(content)
        judgement = _normalize_judgement(parsed.get("judgement"))
        issues = _normalize_list(parsed.get("issues"))[:6]
        suggestions = _normalize_list(parsed.get("suggestions"))[:6]
        correct_answer = str(parsed.get("correct_answer") or "").strip()
        feedback = str(parsed.get("feedback") or "").strip()

        if _is_rich_enough(judgement, issues, suggestions, correct_answer, feedback):
            return {
                "judgement": judgement,
                "issues": issues,
                "suggestions": suggestions,
                "correct_answer": correct_answer,
                "feedback": feedback,
            }
    except Exception:
        pass

    return _fallback_analysis(question, user_answer)
