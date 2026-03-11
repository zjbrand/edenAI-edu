import React, { useState } from "react";
import { apiScoreCode, type CodeScoreResponse } from "../../api/codeScore";

type Props = {
  token: string;
};

const CodeScoreView: React.FC<Props> = ({ token }) => {
  const calcTotal = (correctness: number, style: number, efficiency: number) =>
    Math.round(correctness * 0.6 + style * 0.2 + efficiency * 0.2);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CodeScoreResponse | null>(null);

  const onSubmit = async () => {
    if (!code.trim()) {
      setError("この入力欄には採点対象のコードを入力してください。");
      setResult(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await apiScoreCode(token, code);
      setResult(data);
      if (!data.is_code) {
        setError(data.message);
      }
    } catch (e: any) {
      setError(e.message || "採点に失敗しました。");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="code-score-view">
      <div className="code-score-header">
        <h2>コード採点</h2>
        <p>
          コードを入力して採点を押すと、
          <span className="code-score-rule-item code-score-inline-metric" tabIndex={0}>
            正確性 60%
            <span className="code-score-rule-tooltip">
              コードが問題の要求どおりに正しく動作するかを評価する。
              <br />
              文法エラー、ロジックエラー、計算ミスなどがないかを確認する。
            </span>
          </span>
          、
          <span className="code-score-rule-item code-score-inline-metric" tabIndex={0}>
            スタイル 20%
            <span className="code-score-rule-tooltip">
              コードの可読性や書き方の良さを評価する。
              <br />
              変数名の分かりやすさ、インデント、命名規則、
              <br />
              コメントの有無などを確認する。
            </span>
          </span>
          、
          <span className="code-score-rule-item code-score-inline-metric" tabIndex={0}>
            有効性 20%
            <span className="code-score-rule-tooltip">
              アルゴリズムや処理方法が効率的であるかを評価する。
              <br />
              不要なループや計算がないか、より良い方法がないかを確認する。
            </span>
          </span>
          で評価します。
        </p>
      </div>

      <div className="code-score-card">
        <label htmlFor="code-input">コード入力</label>
        <textarea
          id="code-input"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="採点対象のコードをここに入力してください..."
        />

        <button type="button" className="primary-btn code-score-submit" onClick={onSubmit} disabled={loading}>
          {loading ? "採点中..." : "採点"}
        </button>

        {error && <div className="auth-error">{error}</div>}
      </div>

      {result?.is_code && (
        <div className="code-score-result">
          <div className="code-score-card" style={{ marginBottom: 8 }}>
            総合点 = 正確性 × 0.6 + スタイル × 0.2 + 有効性 × 0.2
          </div>

          <div className="code-score-grid">
            <div className="status-card">
              <div className="status-title">総合点</div>
              <div className="status-value">{calcTotal(result.correctness, result.style, result.efficiency)}</div>
            </div>
            <div className="status-card">
              <div className="status-title">正確性（60%）</div>
              <div className="status-value">{result.correctness}</div>
            </div>
            <div className="status-card">
              <div className="status-title">スタイル（20%）</div>
              <div className="status-value">{result.style}</div>
            </div>
            <div className="status-card">
              <div className="status-title">有効性（20%）</div>
              <div className="status-value">{result.efficiency}</div>
            </div>
          </div>
          {result.llm_feedback && (
            <div className="code-score-card">
              <h3>AI講評（モデル出力）</h3>
              <div className="code-score-feedback">{result.llm_feedback}</div>
            </div>
          )}

          <div className="code-score-card">
            <h3>主な問題点</h3>
            <ul>
              {result.issues.map((item, idx) => (
                <li key={`issue-${idx}`}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="code-score-card">
            <h3>改善ポイント</h3>
            <ul>
              {result.improvements.map((item, idx) => (
                <li key={`improve-${idx}`}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default CodeScoreView;


