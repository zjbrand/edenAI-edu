// frontend/src/components/layout/Sidebar.tsx
import React from "react";
import logo from "../../assets/logo.png";

import type { Theme, View } from "../../types";

type Props = {
  theme: Theme;
  toggleTheme: () => void;

  activeView: View;
  setActiveView: (v: View) => void;

  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;

  isLoggedIn: boolean;
  onLogout: () => void;

  isTeacher: boolean;
  teacherUnreadCount: number;

  userName?: string;
  userRoleLabel?: string;
  userAvatar?: string;
};

const Sidebar: React.FC<Props> = ({
  theme,
  toggleTheme,
  activeView,
  setActiveView,
  sidebarOpen,
  setSidebarOpen,
  isLoggedIn,
  onLogout,
  isTeacher,
  teacherUnreadCount,
  userName,
  userRoleLabel,
  userAvatar,
}) => {
  return (
    <aside
      className={`sidebar ${sidebarOpen ? "open" : ""}`}
      onClick={() => {
        setActiveView("chat");
        setSidebarOpen(false);
      }}
    >
      <div className="sidebar-inner" onClick={(e) => e.stopPropagation()}>
        <div className="sidebar-header">
          <img src={logo} alt="Eden" className="sidebar-logo" />
          <div className="sidebar-title">
            <div className="sidebar-title-main">Eden AI</div>
            <div className="sidebar-title-sub">プログラミング教師(TEST)</div>
          </div>
        </div>

        {isLoggedIn && (
          <div
            style={{
              marginBottom: 10,
              fontSize: 12,
              opacity: 0.9,
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span>{userAvatar || "🙂"}</span>
            <span>
              {userName || "ユーザー"}（{userRoleLabel || "生徒"}）
            </span>
          </div>
        )}

        <nav className="sidebar-nav">
          <button
            type="button"
            className={`nav-item ${activeView === "chat" ? "active" : ""}`}
            onClick={() => {
              setActiveView("chat");
              setSidebarOpen(false);
            }}
          >
            💬 AI会話
          </button>


          <button
            type="button"
            className={`nav-item ${activeView === "code_score" ? "active" : ""}`}
            onClick={() => {
              setActiveView("code_score");
              setSidebarOpen(false);
            }}
          >
            🧪 コード採点
          </button>

          <button
            type="button"
            className={`nav-item ${activeView === "test_analysis" ? "active" : ""}`}
            onClick={() => {
              setActiveView("test_analysis");
              setSidebarOpen(false);
            }}
          >
            📝 テスト解答分析
          </button>

          {!isTeacher && (
            <button
              type="button"
              className={`nav-item ${activeView === "messages" ? "active" : ""}`}
              onClick={() => {
                setActiveView("messages");
                setSidebarOpen(false);
              }}
            >
              🙋 先生に質問
            </button>
          )}

          {isTeacher && (
            <button
              type="button"
              className={`nav-item ${activeView === "messages" ? "active" : ""}`}
              onClick={() => {
                setActiveView("messages");
                setSidebarOpen(false);
              }}
              style={{ position: "relative" }}
            >
              📨 メッセージ
              {teacherUnreadCount > 0 && <span className="msg-badge nav-badge">{teacherUnreadCount}</span>}
            </button>
          )}

          {isTeacher && (
            <button
              type="button"
              className={`nav-item ${activeView === "knowledge" ? "active" : ""}`}
              onClick={() => {
                setActiveView("knowledge");
                setSidebarOpen(false);
              }}
            >
              📚 AI再学習
            </button>
          )}

          {isTeacher && (
            <button
              type="button"
              className={`nav-item ${activeView === "admin" ? "active" : ""}`}
              onClick={() => {
                setActiveView("admin");
                setSidebarOpen(false);
              }}
            >
              📊 システム管理
            </button>
          )}

          <button
            type="button"
            className={`nav-item ${activeView === "settings" ? "active" : ""}`}
            onClick={() => {
              setActiveView("settings");
              setSidebarOpen(false);
            }}
          >
            ⚙ 設定
          </button>
        </nav>

        <div className="sidebar-footer">
          <button type="button" className="outline-btn" onClick={toggleTheme}>
            {theme === "dark" ? "ライトへ切替" : "ダークへ切替"}
          </button>

          {isLoggedIn && (
            <button
              type="button"
              className="outline-btn danger"
              onClick={() => {
                onLogout();
                setSidebarOpen(false);
              }}
            >
              ログアウト
            </button>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;





