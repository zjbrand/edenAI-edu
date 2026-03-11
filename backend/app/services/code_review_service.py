from __future__ import annotations

import ast
import json
import re
from typing import Any

import httpx

from app.services.llm_service import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL

NON_CODE_MESSAGE = "この入力欄には採点対象のコードを入力してください。"


def _clamp(score: float) -> int:
    return max(0, min(100, int(round(score))))


def _weighted_total(correctness: int, style: int, efficiency: int) -> int:
    # 総合点 = 正確性*0.6 + スタイル*0.2 + 有効性*0.2
    return _clamp(correctness * 0.6 + style * 0.2 + efficiency * 0.2)


def _score_from_value(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        return _clamp(float(value))
    if isinstance(value, str):
        m = re.search(r"(\d{1,3})(?:\.\d+)?", value)
        if m:
            return _clamp(float(m.group(1)))
    return None


def _pick_score(obj: dict[str, Any], raw_text: str, *keys: str) -> int:
    for key in keys:
        if key in obj:
            parsed = _score_from_value(obj.get(key))
            if parsed is not None:
                return parsed

    for key in keys:
        m = re.search(rf"{re.escape(key)}\s*[:：=]?\s*(\d{{1,3}})", raw_text, re.IGNORECASE)
        if m:
            return _clamp(float(m.group(1)))

    return 0


def _compose_feedback(
    correctness: int,
    style: int,
    efficiency: int,
    issues: list[str],
    improvements: list[str],
    analysis: str | None = None,
) -> str:
    if analysis and analysis.strip():
        return analysis.strip()

    lines = [
        "**AI講評（要約）**",
        f"- 正確性: {correctness}点",
        f"- スタイル: {style}点",
        f"- 有効性: {efficiency}点",
        "",
        "**主な問題点**",
    ]
    for item in issues[:6]:
        lines.append(f"- {item}")

    lines.append("")
    lines.append("**改善ポイント**")
    for item in improvements[:6]:
        lines.append(f"- {item}")

    return "\n".join(lines)


def looks_like_code(text: str) -> bool:
    if not text or len(text.strip()) < 12:
        return False

    sample = text.strip()
    lines = [ln for ln in sample.splitlines() if ln.strip()]
    if len(lines) < 2:
        return False

    patterns = [
        r"\bdef\b", r"\bclass\b", r"\bfunction\b", r"=>", r"\breturn\b",
        r"\bif\b", r"\bfor\b", r"\bwhile\b", r"\bimport\b", r"#include",
        r"\{", r"\}", r";", r"\(", r"\)",
    ]
    hits = sum(1 for p in patterns if re.search(p, sample))

    non_alnum = sum(1 for ch in sample if not ch.isalnum() and not ch.isspace())
    symbol_ratio = non_alnum / max(1, len(sample))

    return hits >= 3 or (hits >= 2 and symbol_ratio > 0.06) or (len(sample) >= 20 and symbol_ratio > 0.12)


def _balanced_pairs(code: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in code:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()
    return not stack


def _maybe_python(code: str) -> bool:
    py_markers = ["def ", "import ", "print(", "elif ", "except", "None", "True", "False"]
    return any(m in code for m in py_markers)


def _detect_spelling_and_symbol_errors(code: str) -> tuple[list[str], list[str], float, float]:
    issues: list[str] = []
    improvements: list[str] = []
    correctness_penalty = 0.0
    style_penalty = 0.0

    typo_map = {
        "pritn(": "print(",
        "funtion": "function",
        "retrun": "return",
        "improt ": "import ",
        "cosnt ": "const ",
        "lenght": "length",
    }
    for wrong, right in typo_map.items():
        if wrong in code:
            issues.append(f"スペルミスの可能性: '{wrong}'（候補: '{right}'）")
            improvements.append(f"'{wrong}' を '{right}' に修正してください。")
            correctness_penalty += 8

    full_width_symbols = re.findall(r"[，。；：！？（）｛｝［］＝＋＜＞]", code)
    if full_width_symbols:
        issues.append("全角記号が含まれています。コードでは半角記号を使用してください。")
        improvements.append("全角の記号を半角に置き換えてください。")
        correctness_penalty += 10
        style_penalty += 4

    if code.count('"') % 2 == 1 or code.count("'") % 2 == 1:
        issues.append("クォートの対応が崩れている可能性があります。")
        improvements.append("文字列の開始/終了クォートを確認してください。")
        correctness_penalty += 10

    op_end_lines = [ln.strip() for ln in code.splitlines() if re.search(r"[+\-*/=,.:]$", ln.strip())]
    if op_end_lines:
        issues.append("行末の記号位置に不整合の可能性があります。")
        improvements.append("演算子や区切り記号の位置を見直してください。")
        correctness_penalty += 8

    return issues, improvements, correctness_penalty, style_penalty


def _heuristic_review(code: str) -> dict[str, Any]:
    correctness = 82.0
    style = 78.0
    efficiency = 76.0
    issues: list[str] = []
    improvements: list[str] = []

    lines = code.splitlines()
    line_count = max(1, len(lines))

    spelling_issues, spelling_improvements, c_penalty, s_penalty = _detect_spelling_and_symbol_errors(code)
    if spelling_issues:
        issues.extend(spelling_issues)
        improvements.extend(spelling_improvements)
        correctness -= c_penalty
        style -= s_penalty

    if not _balanced_pairs(code):
        correctness -= 22
        issues.append("括弧または波括弧の対応が崩れている可能性があります。")
        improvements.append("()、[]、{} の開閉を対応させてください。")

    if _maybe_python(code):
        try:
            ast.parse(code)
        except SyntaxError as e:
            correctness -= 26
            issues.append(f"Python 構文エラーの可能性: {e.msg}（{e.lineno} 行目）")
            improvements.append("まず構文エラーを解消してからロジック検証を行ってください。")

    long_lines = sum(1 for ln in lines if len(ln) > 120)
    if long_lines > 0:
        style -= min(16, long_lines * 2)
        issues.append("長すぎる行があり、可読性が低下しています。")
        improvements.append("長い式は改行し、中間変数に分割してください。")

    if "\t" in code:
        style -= 8
        issues.append("インデントにタブとスペースが混在しています。")
        improvements.append("インデントをスペースに統一してください。")

    comment_lines = sum(1 for ln in lines if ln.strip().startswith(("#", "//", "/*", "*")))
    if line_count >= 12 and comment_lines == 0:
        style -= 8
        improvements.append("重要処理には短いコメントを追加すると保守しやすくなります。")

    nested_loop_hit = bool(
        re.search(r"for\s+.*:\n(?:\s{2,}|\t)+for\s+", code)
        or re.search(r"for\s*\(.*\)\s*\{[\s\S]{0,220}for\s*\(", code)
    )
    if nested_loop_hit:
        efficiency -= 14
        issues.append("入れ子ループがあり、データ量増加時に性能低下の恐れがあります。")
        improvements.append("辞書化・索引化などで計算量を下げることを検討してください。")

    if re.search(r"\+\=\s*['\"]", code) and re.search(r"for\s|while\s", code):
        efficiency -= 8
        improvements.append("ループ内の文字列結合は join などへ置き換えると効率的です。")

    correctness_i = _clamp(correctness)
    style_i = _clamp(style)
    efficiency_i = _clamp(efficiency)

    if not issues:
        issues.append("重大なエラーは検出されませんでした。")
    if not improvements:
        improvements.append("境界値テストを追加すると品質がさらに向上します。")

    return {
        "correctness": correctness_i,
        "style": style_i,
        "efficiency": efficiency_i,
        "total_score": _weighted_total(correctness_i, style_i, efficiency_i),
        "issues": issues[:6],
        "improvements": improvements[:6],
        "llm_feedback": _compose_feedback(correctness_i, style_i, efficiency_i, issues, improvements),
    }


def _extract_json_object(raw_text: str) -> dict[str, Any] | None:
    raw_text = raw_text.strip()
    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start >= 0 and end > start:
        block = raw_text[start:end + 1]
        try:
            parsed = json.loads(block)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


def _llm_review(code: str) -> dict[str, Any] | None:
    if not GROQ_API_KEY:
        return None

    prompt = (
        "あなたは厳密なコードレビュアーです。JSONのみを返してください。"
        "JSONキーは correctness(0-100), style(0-100), efficiency(0-100),"
        "issues(文字列配列), improvements(文字列配列), analysis(文字列) を必須とします。"
        "issues はスペルミス・記号ミスを優先して指摘してください。"
        "言語は日本語、各配列は最大6件。"
    )

    url = GROQ_BASE_URL.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": code},
        ],
    }

    try:
        with httpx.Client(timeout=40.0) as client:
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

        content = data["choices"][0]["message"]["content"]
        obj = _extract_json_object(content) or {}

        c = _pick_score(obj, content, "correctness", "accuracy", "正確性", "正确性")
        s = _pick_score(obj, content, "style", "readability", "スタイル", "风格")
        e = _pick_score(obj, content, "efficiency", "performance", "有効性", "有效性")

        issues = [str(x) for x in (obj.get("issues") or obj.get("errors") or [])][:6]
        improvements = [str(x) for x in (obj.get("improvements") or obj.get("suggestions") or [])][:6]

        analysis = str(
            obj.get("analysis")
            or obj.get("summary")
            or obj.get("review")
            or ""
        ).strip()

        if c == 0 and s == 0 and e == 0:
            return None

        if not issues:
            issues = ["重大なエラーは検出されませんでした。"]
        if not improvements:
            improvements = ["テストと例外処理を補強すると安定性が向上します。"]

        return {
            "correctness": c,
            "style": s,
            "efficiency": e,
            "total_score": _weighted_total(c, s, e),
            "issues": issues,
            "improvements": improvements,
            "llm_feedback": _compose_feedback(c, s, e, issues, improvements, analysis or content),
        }
    except Exception:
        return None


def review_code_submission(code: str) -> dict[str, Any]:
    code_text = (code or "").strip()
    if not looks_like_code(code_text):
        return {
            "is_code": False,
            "message": NON_CODE_MESSAGE,
            "correctness": 0,
            "style": 0,
            "efficiency": 0,
            "total_score": 0,
            "issues": [],
            "improvements": [],
            "llm_feedback": None,
        }

    result = _llm_review(code_text) or _heuristic_review(code_text)
    return {
        "is_code": True,
        "message": "採点が完了しました。",
        **result,
    }
