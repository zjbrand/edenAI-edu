import React, { useEffect, useMemo, useState } from "react";
import {
  apiGetConversation,
  apiListConversations,
  apiListTeachers,
  apiListUnansweredMessages,
  apiMarkConversationRead,
  apiSendDirectMessage,
  type ConversationItem,
  type DirectMessageItem,
  type TeacherItem,
  type UnansweredMessageItem,
} from "../../api/messages";

type Props = {
  token: string;
  myUserId: number;
  isTeacher: boolean;
  onUnreadChanged?: (count: number) => void;
  messageEventVersion?: number;
};

const displayName = (u: { full_name?: string | null; email: string }) => u.full_name || u.email;
const isTeacherRole = (role: string) => role === "teacher" || role === "admin";
const roleLabel = (role: string) => (isTeacherRole(role) ? "先生" : "生徒");
const unansweredStudentName = (item: UnansweredMessageItem) => item.student_name || item.student_email;

const MessagesView: React.FC<Props> = ({
  token,
  myUserId,
  isTeacher,
  onUnreadChanged,
  messageEventVersion = 0,
}) => {
  const [teachers, setTeachers] = useState<TeacherItem[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [unansweredItems, setUnansweredItems] = useState<UnansweredMessageItem[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUnansweredId, setSelectedUnansweredId] = useState<number | null>(null);
  const [activePanel, setActivePanel] = useState<"conversation" | "unanswered">(
    isTeacher ? "unanswered" : "conversation",
  );
  const [thread, setThread] = useState<DirectMessageItem[]>([]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = async () => {
    const list = await apiListConversations(token);
    setConversations(list);
    const totalUnread = list.reduce((sum, c) => sum + (c.unread_count || 0), 0);
    onUnreadChanged?.(totalUnread);
  };

  const loadTeachers = async () => {
    if (!isTeacher) {
      const list = await apiListTeachers(token);
      setTeachers(list);
    }
  };

  const loadUnanswered = async () => {
    if (!isTeacher) return;
    const list = await apiListUnansweredMessages(token);
    setUnansweredItems(list);
  };

  const loadThread = async (partnerId: number) => {
    const rows = await apiGetConversation(token, partnerId);
    setThread(rows);
    await apiMarkConversationRead(token, partnerId);
    await loadConversations();
  };

  useEffect(() => {
    (async () => {
      try {
        setError(null);
        setLoading(true);
        await Promise.all([loadConversations(), loadTeachers(), loadUnanswered()]);
      } catch (e: any) {
        setError(e.message || "読み込み失敗");
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (messageEventVersion === 0) return;

    (async () => {
      try {
        await loadConversations();
        await loadUnanswered();
        if (selectedUserId) {
          const rows = await apiGetConversation(token, selectedUserId);
          setThread(rows);
        }
      } catch {
        // WebSocket再取得時エラーは画面に出さない
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messageEventVersion]);

  const mergedContacts = useMemo(() => {
    const map = new Map<
      number,
      {
        user_id: number;
        email: string;
        full_name?: string | null;
        avatar?: string | null;
        role: string;
        is_active?: boolean;
        unread_count: number;
      }
    >();

    for (const c of conversations) {
      map.set(c.user_id, {
        user_id: c.user_id,
        email: c.email,
        full_name: c.full_name,
        avatar: c.avatar,
        role: c.role,
        is_active: c.is_active,
        unread_count: c.unread_count,
      });
    }

    if (!isTeacher) {
      for (const t of teachers) {
        if (!map.has(t.id)) {
          map.set(t.id, {
            user_id: t.id,
            email: t.email,
            full_name: t.full_name,
            avatar: t.avatar,
            role: "teacher",
            is_active: true,
            unread_count: 0,
          });
        }
      }
    }

    const contacts = Array.from(map.values());
    return contacts.filter((c) => {
      if (c.user_id === myUserId) return false;
      if (c.is_active === false) return false;
      if (isTeacher) return !isTeacherRole(c.role);
      return isTeacherRole(c.role);
    });
  }, [conversations, teachers, isTeacher, myUserId]);

  const selectedContact = mergedContacts.find((x) => x.user_id === selectedUserId) || null;
  const selectedUnansweredItem =
    unansweredItems.find((item) => item.id === selectedUnansweredId) || null;

  useEffect(() => {
    if (selectedUserId && !mergedContacts.some((x) => x.user_id === selectedUserId)) {
      setSelectedUserId(null);
      setThread([]);
    }
  }, [mergedContacts, selectedUserId]);

  const onSelectContact = async (partnerId: number) => {
    setActivePanel("conversation");
    setSelectedUserId(partnerId);
    setSelectedUnansweredId(null);
    try {
      setError(null);
      await loadThread(partnerId);
    } catch (e: any) {
      setError(e.message || "会話の取得に失敗しました");
    }
  };

  const onSend = async () => {
    if (!selectedUserId || !text.trim()) return;
    try {
      setError(null);
      await apiSendDirectMessage(token, selectedUserId, text.trim(), selectedUnansweredId);
      setText("");
      setSelectedUnansweredId(null);
      await loadThread(selectedUserId);
      await loadUnanswered();
    } catch (e: any) {
      setError(e.message || "送信失敗");
    }
  };

  const openStudentConversationFromUnanswered = async (item: UnansweredMessageItem) => {
    setSelectedUserId(item.student_id);
    setSelectedUnansweredId(item.id);
    setActivePanel("conversation");
    try {
      setError(null);
      await loadThread(item.student_id);
      setText(`AI会話で未回答となっていた件について回答します。\n\n【未回答の内容】\n${item.question}\n`);
    } catch (e: any) {
      setError(e.message || "会話の取得に失敗しました");
    }
  };

  return (
    <div className="messages-view">
      <div className="messages-header">
        <h2>{isTeacher ? "メッセージ（生徒対応）" : "先生に質問"}</h2>
        {isTeacher && (
          <p style={{ marginTop: 6, fontSize: 12, opacity: 0.85 }}>
            AI会話で生徒の要望を満たせない場合は、回答をコピーしてTXT形式で会社ナレッジにアップロードしてください。
          </p>
        )}
      </div>

      {loading && <div style={{ opacity: 0.7 }}>読み込み中...</div>}
      {error && <div className="auth-error">{error}</div>}

      <div className="messages-layout">
        <aside className="messages-contacts">
          {isTeacher && (
            <button
              type="button"
              className={`messages-contact-item messages-unanswered-trigger ${activePanel === "unanswered" ? "active" : ""}`}
              onClick={() => {
                setActivePanel("unanswered");
                setSelectedUserId(null);
                setSelectedUnansweredId(null);
                setThread([]);
              }}
            >
              <div className="messages-contact-main">
                <div className="messages-contact-name">🕒 AI会話未回答</div>
                <div className="messages-contact-role">5分以上未回答の内容を確認</div>
              </div>
              {unansweredItems.length > 0 && <span className="msg-badge">{unansweredItems.length}</span>}
            </button>
          )}

          {mergedContacts.length === 0 && <div style={{ opacity: 0.7 }}>連絡先がありません。</div>}
          {mergedContacts.map((c) => (
            <button
              key={c.user_id}
              type="button"
              className={`messages-contact-item ${activePanel === "conversation" && selectedUserId === c.user_id ? "active" : ""}`}
              onClick={() => onSelectContact(c.user_id)}
            >
              <div className="messages-contact-main">
                <div className="messages-contact-name">
                  {(c.avatar || "🙂") + " "}
                  {displayName(c)}
                </div>
                <div className="messages-contact-role">{roleLabel(c.role)}</div>
              </div>
              {c.unread_count > 0 && <span className="msg-badge">{c.unread_count}</span>}
            </button>
          ))}
        </aside>

        <section className="messages-thread">
          {activePanel === "unanswered" && isTeacher && (
            <>
              <div className="messages-thread-title">
                <span className="messages-thread-name">AI会話未回答メッセージ</span>
                <span className="messages-thread-role">（{unansweredItems.length}件）</span>
              </div>

              <div className="messages-thread-body">
                {unansweredItems.length === 0 && <div style={{ opacity: 0.7 }}>未回答メッセージはありません。</div>}

                {unansweredItems.map((item) => (
                  <div key={item.id} className="messages-unanswered-card">
                    <div className="messages-unanswered-head">
                      <div className="messages-unanswered-student">
                        {(item.student_avatar || "🙂") + " "}
                        {unansweredStudentName(item)}
                        <span className="messages-thread-role">（生徒）</span>
                      </div>
                      <div className="messages-unanswered-time">
                        {item.created_at.replace("T", " ").slice(0, 16)}
                      </div>
                    </div>
                    <div className="messages-unanswered-subject">科目: {item.subject}</div>
                    <div className="messages-unanswered-question">{item.question}</div>
                    <div className="messages-unanswered-actions">
                      <button className="primary-btn" onClick={() => openStudentConversationFromUnanswered(item)}>
                        この生徒と対話
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {activePanel === "conversation" && !selectedContact && (
            <div style={{ opacity: 0.7 }}>左側から相手を選択してください。</div>
          )}

          {activePanel === "conversation" && selectedContact && (
            <>
              <div className="messages-thread-title">
                <span className="messages-thread-name">
                  {(selectedContact.avatar || "🙂") + " "}
                  {displayName(selectedContact)}
                </span>
                <span className="messages-thread-role">（{roleLabel(selectedContact.role)}）</span>
                <span>との対話</span>
              </div>

              {selectedUnansweredItem && isTeacher && (
                <div className="messages-linked-unanswered">
                  <div className="messages-linked-unanswered-title">対応中の未回答内容</div>
                  <div className="messages-linked-unanswered-body">{selectedUnansweredItem.question}</div>
                </div>
              )}

              <div className="messages-thread-body">
                {thread.map((m) => {
                  const mine = m.sender_id === myUserId;
                  const senderIsTeacher = mine ? isTeacher : isTeacherRole(selectedContact.role);
                  return (
                    <div key={m.id} className={`chat-message-row ${mine ? "align-right" : "align-left"}`}>
                      <div className={senderIsTeacher ? "teacher-plain-text" : "chat-message-bubble user-bubble"}>
                        {m.content}
                      </div>
                    </div>
                  );
                })}
                {thread.length === 0 && <div style={{ opacity: 0.6 }}>まだメッセージがありません。</div>}
              </div>

              <div className="messages-thread-input">
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={isTeacher ? "生徒へ返信する内容を入力" : "先生への質問を入力"}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      onSend();
                    }
                  }}
                />
                <button className="primary-btn" onClick={onSend} disabled={!text.trim()}>
                  送信
                </button>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
};

export default MessagesView;
