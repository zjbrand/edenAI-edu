import React, { useEffect, useState } from "react";
import {
  apiAnalyzeTestAnswer,
  apiDeleteTestAnswerHistory,
  apiGetTestAnswerHistory,
  apiListTestAnswerHistory,
  apiRenameTestAnswerHistory,
  type TestAnswerAnalysisResponse,
  type TestAnswerHistoryDetail,
  type TestAnswerHistorySummary,
} from "../../api/testAnswerAnalysis";

type Props = {
  token: string;
};

const TestAnswerAnalysisView: React.FC<Props> = ({ token }) => {
  const [question, setQuestion] = useState("");
  const [userAnswer, setUserAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TestAnswerAnalysisResponse | null>(null);
  const [historyItems, setHistoryItems] = useState<TestAnswerHistorySummary[]>([]);
  const [activeHistoryId, setActiveHistoryId] = useState<number | null>(null);

  const loadHistory = async () => {
    const list = await apiListTestAnswerHistory(token);
    setHistoryItems(list);
  };

  useEffect(() => {
    (async () => {
      try {
        await loadHistory();
      } catch {
        // 初回履歴取得失敗でも分析機能自体は使えるようにする
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const onSubmit = async () => {
    if (!question.trim()) {
      setError("問題を入力してください。");
      return;
    }
    if (!userAnswer.trim()) {
      setError("あなたの答案を入力してください。");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await apiAnalyzeTestAnswer(token, question, userAnswer);
      setResult(data);
      setActiveHistoryId(data.history_id ?? null);
      await loadHistory();
    } catch (e: any) {
      setError(e.message || "解答分析に失敗しました。");
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const onSelectHistory = async (historyId: number) => {
    try {
      setHistoryLoading(true);
      setError(null);
      const detail: TestAnswerHistoryDetail = await apiGetTestAnswerHistory(token, historyId);
      setActiveHistoryId(detail.id);
      setQuestion(detail.question);
      setUserAnswer(detail.user_answer);
      setResult(detail);
    } catch (e: any) {
      setError(e.message || "履歴の読み込みに失敗しました。");
    } finally {
      setHistoryLoading(false);
    }
  };

  const onNewAnalysis = () => {
    setActiveHistoryId(null);
    setQuestion("");
    setUserAnswer("");
    setResult(null);
    setError(null);
  };

  const onRenameHistory = async (item: TestAnswerHistorySummary) => {
    const title = window.prompt("新しい履歴名を入力してください。", item.title);
    if (title === null) return;

    try {
      await apiRenameTestAnswerHistory(token, item.id, title);
      await loadHistory();
    } catch (e: any) {
      setError(e.message || "履歴名の変更に失敗しました。");
    }
  };

  const onDeleteHistory = async (item: TestAnswerHistorySummary) => {
    const ok = window.confirm(`「${item.title}」を削除しますか？`);
    if (!ok) return;

    try {
      await apiDeleteTestAnswerHistory(token, item.id);
      await loadHistory();
      if (activeHistoryId === item.id) {
        onNewAnalysis();
      }
    } catch (e: any) {
      setError(e.message || "履歴の削除に失敗しました。");
    }
  };

  return (
    <div className="test-analysis-view">
      <div className="code-score-header">
        <h2>テスト解答分析</h2>
        <p>問題とあなたの答案を入力すると、AIが誤りや補足点を分析し、改善提案と模範解答を返します。</p>
      </div>

      <div className="code-score-workspace">
        <aside className="chat-history-panel code-score-history-panel">
          <div className="chat-history-header">
            <div className="chat-history-title">履歴</div>
            <button type="button" className="primary-btn" onClick={onNewAnalysis}>
              新しい分析
            </button>
          </div>

          {historyLoading && <div style={{ opacity: 0.7 }}>履歴を読み込み中...</div>}
          {!historyLoading && historyItems.length === 0 && (
            <div style={{ opacity: 0.7 }}>まだ保存された解答分析履歴がありません。</div>
          )}

          <div className="chat-history-list">
            {historyItems.map((item) => (
              <button
                key={item.id}
                type="button"
                className={`chat-history-item ${activeHistoryId === item.id ? "active" : ""}`}
                onClick={() => onSelectHistory(item.id)}
              >
                <div className="chat-history-item-top">
                  <div className="chat-history-item-title">{item.title}</div>
                  <div className="chat-history-item-actions" onClick={(e) => e.stopPropagation()}>
                    <button type="button" className="link-btn" onClick={() => onRenameHistory(item)}>
                      名前変更
                    </button>
                    <button type="button" className="link-btn danger" onClick={() => onDeleteHistory(item)}>
                      削除
                    </button>
                  </div>
                </div>
                <div className="chat-history-item-meta">判定: {item.judgement}</div>
                <div className="chat-history-item-preview">{item.preview || "分析結果を確認する"}</div>
              </button>
            ))}
          </div>
        </aside>

        <div className="code-score-main">
          <div className="code-score-card test-analysis-input-card">
            <label htmlFor="test-question-input">問題</label>
            <textarea
              id="test-question-input"
              className="test-analysis-question-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="問題文を入力してください..."
            />

            <label htmlFor="test-answer-input">あなたの答案</label>
            <textarea
              id="test-answer-input"
              className="test-analysis-answer-input"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="自分の解答を入力してください..."
            />

            <button type="button" className="primary-btn code-score-submit" onClick={onSubmit} disabled={loading}>
              {loading ? "分析中..." : "分析する"}
            </button>

            {error && <div className="auth-error">{error}</div>}
          </div>

          {result && (
            <div className="code-score-result">
              <div className="code-score-card">
                <h3>判定</h3>
                <div className={`test-analysis-judgement ${result.judgement === "正しい" ? "ok" : result.judgement === "不完全" ? "partial" : "ng"}`}>
                  {result.judgement}
                </div>
              </div>

              <div className="code-score-card">
                <h3>誤っている点・補足できる点</h3>
                <ul>
                  {result.issues.map((item, idx) => (
                    <li key={`issue-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="code-score-card">
                <h3>改善提案</h3>
                <ul>
                  {result.suggestions.map((item, idx) => (
                    <li key={`suggestion-${idx}`}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="code-score-card">
                <h3>正しい解答</h3>
                <div className="code-score-feedback">{result.correct_answer}</div>
              </div>

              <div className="code-score-card">
                <h3>AIフィードバック</h3>
                <div className="code-score-feedback">{result.feedback}</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestAnswerAnalysisView;
