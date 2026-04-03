import React, { useEffect, useState } from "react";
import "./App.css";

import Sidebar from "./components/layout/Sidebar";
import ChatView from "./components/chat/ChatView";
import AuthView from "./components/auth/AuthView";
import AdminView, { type AdminTab } from "./components/admin/AdminView";
import SettingsView from "./components/settings/SettingsView";
import MessagesView from "./components/messages/MessagesView";
import CodeScoreView from "./components/code-score/CodeScoreView";

import type { Message, View, Theme, AuthMode } from "./types";
import { apiAsk, apiLogin, apiRegister, apiMe, apiRateAiResponse } from "./lib/api";
import { apiUnreadCount, createMessagesSocket, type MessagesSocketEvent } from "./api/messages";
import type { MeResponse } from "./lib/api";

export type LoginType = "student" | "teacher";

const roleLabel = (role: string | undefined) => {
  if (role === "teacher" || role === "admin") return "先生";
  return "生徒";
};

const App: React.FC = () => {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [subject, setSubject] = useState("プログラミング");
  const [error, setError] = useState<string | null>(null);

  const [activeView, setActiveView] = useState<View>("chat");
  const [theme, setTheme] = useState<Theme>("light");
  const [adminTab, setAdminTab] = useState<AdminTab>("system");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [token, setToken] = useState<string | null>(() =>
    typeof window !== "undefined" ? localStorage.getItem("eden_token") : null
  );
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(() =>
    typeof window !== "undefined" ? !!localStorage.getItem("eden_token") : false
  );

  const [loginType, setLoginType] = useState<LoginType>("student");

  const [authMode, setAuthMode] = useState<AuthMode>("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authAvatar, setAuthAvatar] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);

  const [me, setMe] = useState<MeResponse | null>(null);
  const [teacherUnreadCount, setTeacherUnreadCount] = useState(0);
  const [messageEventVersion, setMessageEventVersion] = useState(0);

  const isTeacher = me?.role === "teacher" || me?.role === "admin";

  const toggleTheme = () => setTheme((p) => (p === "dark" ? "light" : "dark"));

  useEffect(() => {
    if (!token) {
      setMe(null);
      setTeacherUnreadCount(0);
      return;
    }

    (async () => {
      try {
        const meData = await apiMe(token);
        setMe(meData);
      } catch {
        setMe(null);
        setIsLoggedIn(false);
        setToken(null);
        localStorage.removeItem("eden_token");
      }
    })();
  }, [token]);

  useEffect(() => {
    if (!token || !isTeacher) {
      setTeacherUnreadCount(0);
      return;
    }

    (async () => {
      try {
        const count = await apiUnreadCount(token);
        setTeacherUnreadCount(count);
      } catch {
        // 初回取得失敗時は WebSocket 再通知を待つ
      }
    })();
  }, [token, isTeacher]);

  useEffect(() => {
    if (!token || !isLoggedIn) return;

    let ws: WebSocket | null = null;
    let closedByEffect = false;
    let reconnectTimer: number | null = null;

    const connect = () => {
      ws = createMessagesSocket(token);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as MessagesSocketEvent;
          if (typeof data.unread_count === "number" && isTeacher) {
            setTeacherUnreadCount(data.unread_count);
          }
          if (data.type === "messages_updated") {
            setMessageEventVersion((prev) => prev + 1);
          }
        } catch {
          // 不正なイベントは無視
        }
      };

      ws.onclose = () => {
        if (closedByEffect) return;
        reconnectTimer = window.setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      closedByEffect = true;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      ws?.close();
    };
  }, [token, isLoggedIn, isTeacher]);

  const handleSend = async () => {
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    if (!token) {
      alert("ログインしてください。");
      return;
    }

    setError(null);
    const newMessages: Message[] = [...messages, { role: "user", content: trimmed }];
    setMessages(newMessages);
    setQuestion("");
    setLoading(true);

    try {
      const historyPayload = newMessages.map((m) => ({ role: m.role, content: m.content }));
      const data = await apiAsk({
        token,
        question: trimmed,
        subject,
        history: historyPayload,
      });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          responseId: data.response_id ?? undefined,
          rating: null,
        },
      ]);
    } catch (e: any) {
      setError(e.message || "リクエスト失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleRateResponse = async (responseId: number, rating: number) => {
    if (!token) {
      alert("ログインしてください。");
      return;
    }

    setMessages((prev) =>
      prev.map((msg) =>
        msg.responseId === responseId ? { ...msg, ratingPending: true } : msg
      )
    );

    try {
      await apiRateAiResponse({ token, responseId, rating });
      setMessages((prev) =>
        prev.map((msg) =>
          msg.responseId === responseId ? { ...msg, rating, ratingPending: false } : msg
        )
      );
    } catch (e: any) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.responseId === responseId ? { ...msg, ratingPending: false } : msg
        )
      );
      alert(e.message || "評価の送信に失敗しました。");
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);

    if (loginType === "teacher" && authMode === "register") {
      setAuthError("先生アカウントは登録できません。");
      return;
    }

    try {
      if (loginType === "student" && authMode === "register") {
        await apiRegister(authEmail, authPassword, authName || null, authAvatar || null);
      }

      const accessToken = await apiLogin(authEmail, authPassword);
      setToken(accessToken);
      setIsLoggedIn(true);
      localStorage.setItem("eden_token", accessToken);

      const meData = await apiMe(accessToken);
      setMe(meData);

      if (loginType === "teacher") {
        if (meData.role !== "teacher" && meData.role !== "admin") {
          setAuthError("先生権限がありません。");
          localStorage.removeItem("eden_token");
          setIsLoggedIn(false);
          setToken(null);
          setMe(null);
          return;
        }
        setActiveView("admin");
        setAdminTab("system");
      } else {
        setActiveView("chat");
      }

      setSidebarOpen(false);
    } catch (err: any) {
      setAuthError(err.message || "認証失敗");
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setToken(null);
    setMe(null);
    setTeacherUnreadCount(0);
    localStorage.removeItem("eden_token");

    setAuthMode("login");
    setLoginType("student");
    setAuthAvatar("");
    setActiveView("chat");
    setSidebarOpen(false);
    setMessages([]);
  };

  const renderMainContent = () => {
    if (!isLoggedIn) {
      return (
        <AuthView
          loginType={loginType}
          setLoginType={setLoginType}
          authMode={authMode}
          setAuthMode={setAuthMode}
          authEmail={authEmail}
          setAuthEmail={setAuthEmail}
          authPassword={authPassword}
          setAuthPassword={setAuthPassword}
          authName={authName}
          setAuthName={setAuthName}
          authAvatar={authAvatar}
          setAuthAvatar={setAuthAvatar}
          authError={authError}
          onSubmit={handleAuthSubmit}
        />
      );
    }

    if (activeView === "admin") {
      return <AdminView token={token!} adminTab={adminTab} setAdminTab={setAdminTab} />;
    }

    if (activeView === "knowledge") {
      return <AdminView token={token!} adminTab="knowledge" setAdminTab={setAdminTab} />;
    }

    if (activeView === "messages") {
      return (
        <MessagesView
          token={token ?? ""}
          myUserId={me?.id ?? 0}
          isTeacher={!!isTeacher}
          onUnreadChanged={setTeacherUnreadCount}
          messageEventVersion={messageEventVersion}
        />
      );
    }

    if (activeView === "code_score") {
      return <CodeScoreView token={token ?? ""} />;
    }

    if (activeView === "settings") {
      const email = me?.email ?? "";
      const fullName = me?.full_name ?? null;
      const role = me?.role ?? "student";

      return <SettingsView token={token ?? ""} email={email} fullName={fullName} role={role} />;
    }

    return (
      <ChatView
        theme={theme}
        toggleTheme={toggleTheme}
        subject={subject}
        setSubject={setSubject}
        messages={messages}
        question={question}
        setQuestion={setQuestion}
        loading={loading}
        error={error}
        onSend={handleSend}
        onRateResponse={handleRateResponse}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />
    );
  };

  return (
    <div className={`app-root ${theme}`}>
      <div className="app-layout">
        <Sidebar
          theme={theme}
          toggleTheme={toggleTheme}
          activeView={activeView}
          setActiveView={(v) => {
            if ((v === "admin" || v === "knowledge") && !isTeacher) return;
            setActiveView(v);
          }}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          isLoggedIn={isLoggedIn}
          onLogout={handleLogout}
          isTeacher={!!isTeacher}
          teacherUnreadCount={teacherUnreadCount}
          userName={me?.full_name || me?.email}
          userRoleLabel={roleLabel(me?.role)}
          userAvatar={me?.avatar || ""}
        />

        <main className="main-panel">
          <div className="mobile-top-bar">
            <button className="menu-btn" onClick={() => setSidebarOpen((v) => !v)}>
              ☰
            </button>
            <div className="mobile-top-title">Eden AI</div>
            <div style={{ width: 24 }} />
          </div>

          {renderMainContent()}

          {sidebarOpen && (
            <div
              onClick={() => setSidebarOpen(false)}
              style={{
                position: "fixed",
                inset: 0,
                background: "rgba(0,0,0,0.35)",
                zIndex: 20,
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;





