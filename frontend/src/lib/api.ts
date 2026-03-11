// src/lib/api.ts
const API_BASE_FROM_ENV = import.meta.env.VITE_API_BASE as string | undefined;

function resolveApiBase(): string {
  if (API_BASE_FROM_ENV && API_BASE_FROM_ENV.trim().length > 0) {
    return API_BASE_FROM_ENV.trim();
  }

  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://127.0.0.1:8000";
    }
    return window.location.origin;
  }

  return "http://127.0.0.1:8000";
}

async function readApiError(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string" && data.detail.trim()) {
      return data.detail;
    }
  } catch {
    // JSON でないエラー本文は次で吸収する
  }

  try {
    const text = await res.text();
    if (text.trim()) return text;
  } catch {
    // 本文が取れない場合は fallback を返す
  }

  return fallback;
}

export const API_BASE = resolveApiBase();

export async function apiRegister(
  email: string,
  password: string,
  fullName?: string | null,
  avatar?: string | null,
) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      full_name: fullName ?? null,
      avatar: avatar ?? null,
    }),
  });
  if (!res.ok) {
    const msg = await readApiError(res, "登録に失敗しました。");
    throw new Error(`登録失敗: ${msg}`);
  }
}

export async function apiLogin(email: string, password: string): Promise<string> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });

  if (!res.ok) {
    const msg = await readApiError(res, "ログインに失敗しました。");
    throw new Error(`ログイン失敗: ${msg}`);
  }

  const data = await res.json();
  if (!data?.access_token) throw new Error("access_token が返ってきませんでした");
  return data.access_token as string;
}

export async function apiAsk(params: {
  token: string;
  question: string;
  subject: string;
  history: { role: string; content: string }[];
}) {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${params.token}`,
    },
    body: JSON.stringify({
      question: params.question,
      subject: params.subject,
      history: params.history,
    }),
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return (await res.json()) as { answer: string };
}

export type MeResponse = {
  id: number;
  email: string;
  full_name: string | null;
  avatar: string | null;
  role: "student" | "teacher" | "user" | "admin" | string;
};

export async function apiMe(token: string): Promise<MeResponse> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiChangePassword(
  token: string,
  currentPassword: string,
  newPassword: string
): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/auth/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
