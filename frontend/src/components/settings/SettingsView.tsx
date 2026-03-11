import React, { useState } from "react";
import { apiChangePassword } from "../../lib/api";

type Props = {
  token: string;
  email: string;
  fullName?: string | null;
  role: string;
};

const roleLabel = (role: string) => {
  if (role === "teacher" || role === "admin") return "先生";
  if (role === "student" || role === "user") return "生徒";
  return role;
};

const SettingsView: React.FC<Props> = ({ token, email, fullName, role }) => {
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const onChangePw = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    setErr(null);

    if (!currentPw || !newPw || !newPw2) {
      setErr("入力内容を確認してください。");
      return;
    }
    if (newPw !== newPw2) {
      setErr("新しいパスワードが一致しません。");
      return;
    }
    if (newPw.length < 6) {
      setErr("新しいパスワードは6文字以上にしてください。");
      return;
    }

    try {
      setSaving(true);
      await apiChangePassword(token, currentPw, newPw);
      setMsg("パスワードを変更しました。");
      setCurrentPw("");
      setNewPw("");
      setNewPw2("");
    } catch (e: any) {
      setErr(e.message || "変更に失敗しました");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-view">
      <h2>設定</h2>

      <div className="admin-card" style={{ marginTop: 12 }}>
        <h3>アカウント</h3>
        <p>メール：{email}</p>
        <p>氏名：{fullName || "-"}</p>
        <p>権限：{roleLabel(role)}</p>
      </div>

      <div className="admin-card" style={{ marginTop: 12 }}>
        <h3>パスワード変更</h3>

        <form onSubmit={onChangePw}>
          <div className="form-group">
            <label>現在のパスワード</label>
            <input
              type="password"
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>新しいパスワード</label>
            <input
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>新しいパスワード（確認）</label>
            <input
              type="password"
              value={newPw2}
              onChange={(e) => setNewPw2(e.target.value)}
            />
          </div>

          <button className="primary-btn" type="submit" disabled={saving}>
            {saving ? "変更中..." : "変更する"}
          </button>
        </form>

        {msg && <div style={{ marginTop: 8, fontSize: 12, opacity: 0.85 }}>{msg}</div>}
        {err && <div className="auth-error">{err}</div>}
      </div>
    </div>
  );
};

export default SettingsView;
