import React from "react";
import type { LoginType } from "../../App";

const STUDENT_AVATARS = [
  "🐶", "🐱", "🐰", "🐼", "🐨",
  "🦊", "🐯", "🐸", "🐵", "🐧",
  "🐙", "🦄", "🐻", "🐮", "🐤",
  "🐺", "🐷", "🦁", "🐹", "🐳",
];

interface Props {
  loginType: LoginType;
  setLoginType: (r: LoginType) => void;

  authMode: "login" | "register";
  setAuthMode: (m: "login" | "register") => void;

  authEmail: string;
  setAuthEmail: (v: string) => void;

  authPassword: string;
  setAuthPassword: (v: string) => void;

  authName: string;
  setAuthName: (v: string) => void;

  authAvatar: string;
  setAuthAvatar: (v: string) => void;

  authError: string | null;
  onSubmit: (e: React.FormEvent) => void;
}

const AuthView: React.FC<Props> = ({
  loginType,
  setLoginType,
  authMode,
  setAuthMode,
  authEmail,
  setAuthEmail,
  authPassword,
  setAuthPassword,
  authName,
  setAuthName,
  authAvatar,
  setAuthAvatar,
  authError,
  onSubmit,
}) => {
  const isTeacher = loginType === "teacher";

  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [localError, setLocalError] = React.useState<string | null>(null);

  React.useEffect(() => {
    setLocalError(null);
    if (authMode !== "register") setConfirmPassword("");
  }, [authMode, loginType]);

  const handleRoleChange = (role: LoginType) => {
    setLocalError(null);

    if (role === "teacher") {
      setLoginType("teacher");
      setAuthMode("login");
      setConfirmPassword("");
      return;
    }

    setLoginType("student");
  };

  const handleSubmit = (e: React.FormEvent) => {
    setLocalError(null);

    if (!isTeacher && authMode === "register") {
      if (authPassword !== confirmPassword) {
        e.preventDefault();
        setLocalError("パスワードが一致しません。もう一度確認してください。");
        return;
      }
      if (!authPassword || !confirmPassword) {
        e.preventDefault();
        setLocalError("パスワードを入力してください。");
        return;
      }
      if (!authAvatar) {
        e.preventDefault();
        setLocalError("アバターを選択してください。");
        return;
      }
    }

    onSubmit(e);
  };

  return (
    <div className="auth-view">
      <div className="auth-card">
        <div className="role-card-tabs">
          <button
            type="button"
            className={`role-card ${loginType === "student" ? "active" : ""}`}
            onClick={() => handleRoleChange("student")}
          >
            <div className="role-card-title">生徒</div>
            <div className="role-card-sub">会話機能を利用</div>
          </button>

          <button
            type="button"
            className={`role-card ${loginType === "teacher" ? "active" : ""}`}
            onClick={() => handleRoleChange("teacher")}
          >
            <div className="role-card-title">先生</div>
            <div className="role-card-sub">管理画面を利用</div>
          </button>
        </div>

        <h2 className="auth-title">
          {isTeacher ? "先生ログイン" : authMode === "login" ? "ログイン" : "新規登録"}
        </h2>

        {isTeacher ? (
          <p className="auth-hint">先生アカウントは事前作成済み（登録不可）</p>
        ) : authMode === "login" ? (
          <p className="auth-hint">メールアドレスとパスワードでログインしてください</p>
        ) : (
          <p className="auth-hint">必要事項を入力してアカウントを作成してください</p>
        )}

        <form onSubmit={handleSubmit}>
          {!isTeacher && authMode === "register" && (
            <>
              <div className="form-group">
                <label>氏名</label>
                <input
                  type="text"
                  value={authName}
                  onChange={(e) => setAuthName(e.target.value)}
                  placeholder="例）山田 太郎"
                  autoComplete="name"
                />
              </div>

              <div className="form-group">
                <label>アバター</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {STUDENT_AVATARS.map((a, idx) => (
                    <button
                      key={`${a}-${idx}`}
                      type="button"
                      onClick={() => setAuthAvatar(a)}
                      style={{
                        width: 34,
                        height: 34,
                        borderRadius: 999,
                        border: authAvatar === a ? "2px solid #16c47f" : "1px solid rgba(255,255,255,0.25)",
                        background: "transparent",
                        color: "inherit",
                        cursor: "pointer",
                        fontSize: 18,
                      }}
                    >
                      {a}
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          <div className="form-group">
            <label>メールアドレス</label>
            <input
              type="email"
              value={authEmail}
              onChange={(e) => setAuthEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label>パスワード</label>
            <input
              type="password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              placeholder="********"
              autoComplete={authMode === "register" ? "new-password" : "current-password"}
            />
          </div>

          {!isTeacher && authMode === "register" && (
            <div className="form-group">
              <label>パスワード（確認）</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="********"
                autoComplete="new-password"
              />
            </div>
          )}

          <button type="submit" className="primary-btn full-width">
            {isTeacher ? "先生としてログイン" : authMode === "login" ? "ログイン" : "登録"}
          </button>
        </form>

        {localError && <div className="auth-error">{localError}</div>}
        {authError && <div className="auth-error">{authError}</div>}

        {!isTeacher && (
          <div className="auth-switch">
            {authMode === "login" ? (
              <button
                type="button"
                onClick={() => {
                  setLocalError(null);
                  setAuthMode("register");
                }}
              >
                新規登録
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setLocalError(null);
                  setAuthMode("login");
                }}
              >
                ログインへ戻る
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthView;

