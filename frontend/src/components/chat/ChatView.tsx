import React from "react";
import type { ChatSessionSummary, Message, Theme } from "../../types";

type Props = {
  theme: Theme;
  toggleTheme: () => void;

  subject: string;
  setSubject: (v: string) => void;

  messages: Message[];
  sessions: ChatSessionSummary[];
  activeConversationId: number | null;
  question: string;
  setQuestion: (v: string) => void;

  loading: boolean;
  historyLoading: boolean;
  error: string | null;

  onSend: () => void;
  onNewConversation: () => void;
  onSelectConversation: (sessionId: number) => void;
  onRenameConversation: (session: ChatSessionSummary) => void;
  onDeleteConversation: (session: ChatSessionSummary) => void;
  onRateResponse: (responseId: number, rating: number) => void;
  onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement>;
};

const ChatView: React.FC<Props> = ({
  theme,
  toggleTheme,
  subject,
  setSubject,
  messages,
  sessions,
  activeConversationId,
  question,
  setQuestion,
  loading,
  historyLoading,
  error,
  onSend,
  onNewConversation,
  onSelectConversation,
  onRenameConversation,
  onDeleteConversation,
  onRateResponse,
  onKeyDown,
}) => {
  return (
    <div className="chat-view">
      <div className="top-bar">
        <div className="top-bar-left">
          <div className="app-title-block">
            <div className="app-title-main">Eden AI プログラミング教師</div>
            <div className="app-title-sub">自然言語でプログラミングを学ぶ · 複数ターン対話対応</div>
          </div>
        </div>

        <div className="top-bar-right">
          <div className="subject-select">
            <span>科目：</span>
            <select value={subject} onChange={(e) => setSubject(e.target.value)}>
              <option value="编程">汎用プログラミング</option>
              <option value="Python">Python</option>
              <option value="Java">Java</option>
              <option value="前端">フロントエンド開発</option>
              <option value="算法">アルゴリズム / データ構造</option>
            </select>
          </div>

          <button className="theme-toggle" onClick={toggleTheme}>
            {theme === "dark" ? "🌙ダーク" : "☀ ライト"}
          </button>
        </div>
      </div>

      <div className="chat-workspace">
        <aside className="chat-history-panel">
          <div className="chat-history-header">
            <div className="chat-history-title">履歴</div>
            <button type="button" className="primary-btn" onClick={onNewConversation}>
              新しい話題
            </button>
          </div>

          {historyLoading && <div style={{ opacity: 0.7 }}>履歴を読み込み中...</div>}
          {!historyLoading && sessions.length === 0 && (
            <div style={{ opacity: 0.7 }}>まだ保存された会話がありません。</div>
          )}

          <div className="chat-history-list">
            {sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                className={`chat-history-item ${activeConversationId === session.id ? "active" : ""}`}
                onClick={() => onSelectConversation(session.id)}
              >
                <div className="chat-history-item-top">
                  <div className="chat-history-item-title">{session.title}</div>
                  <div className="chat-history-item-actions" onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      className="link-btn"
                      onClick={() => onRenameConversation(session)}
                    >
                      名前変更
                    </button>
                    <button
                      type="button"
                      className="link-btn danger"
                      onClick={() => onDeleteConversation(session)}
                    >
                      削除
                    </button>
                  </div>
                </div>
                <div className="chat-history-item-meta">{session.subject}</div>
                <div className="chat-history-item-preview">{session.last_message || "会話を続ける"}</div>
              </button>
            ))}
          </div>
        </aside>

        <div className="chat-body">
          {messages.length === 0 && (
            <div className="chat-empty-hint">
              👉 試しに質問してみてください：
              <br />
              「変数とは何か、日常の例えで説明して？」
              <br />
              「ある数が素数かどうか判定するPython関数を書いて？」
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`chat-message-row ${msg.role === "user" ? "align-right" : "align-left"}`}
            >
              <div className="chat-message-stack">
                <div
                  className={`chat-message-bubble ${msg.role === "user" ? "user-bubble" : "assistant-bubble"}`}
                >
                  {msg.content}
                </div>

                {msg.role === "assistant" && msg.responseId && (
                  <div className="chat-rating-box">
                    <div className="chat-rating-label">この回答を評価</div>
                    <div className="chat-rating-stars" aria-label="AI回答評価">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          className={`chat-star-btn ${(msg.rating || 0) >= star ? "active" : ""}`}
                          onClick={() => onRateResponse(msg.responseId!, star)}
                          disabled={msg.ratingPending}
                          aria-label={`${star}つ星で評価`}
                          title={`${star}つ星で評価`}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                    <div className="chat-rating-caption">
                      {msg.ratingPending
                        ? "送信中..."
                        : msg.rating
                          ? `${msg.rating}つ星で評価済み`
                          : "未評価"}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && <div className="error-bar">{error}</div>}

      <div className="input-bar">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="あなたのプログラミングに関する質問を入力してください。Shift+Enterで改行、Enterで送信"
        />
        <button onClick={onSend} disabled={loading || !question.trim()}>
          {loading ? "考え中…" : "送信"}
        </button>
      </div>

      <div className="copyright">
        本ソフトウェアの著作権はエデン株式会社に帰属します。
      </div>
    </div>
  );
};

export default ChatView;
