// frontend/src/api.ts

import { API_BASE } from "./lib/api";

// ====== 型定義 ======
export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface AskResponse {
  answer: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

// ====== トークン操作 ======
const TOKEN_KEY = "eden_ai_token";

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function loadToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

// ====== リクエスト共通処理 ======
function buildHeaders(token?: string): HeadersInit {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

// 1) ログイン
export async function apiLogin(
  email: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `ログインに失敗しました。HTTP ${res.status}`);
  }

  const data = (await res.json()) as LoginResponse;
  return data;
}

// 2) 登録
export async function apiRegister(
  email: string,
  password: string,
  fullName?: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({
      email,
      password,
      full_name: fullName ?? null,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `登録に失敗しました。HTTP ${res.status}`);
  }
}

// 3) 質問送信（履歴と任意トークン付き）
export async function apiAsk(
  question: string,
  subject: string,
  history: ChatMessage[],
  token?: string
): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: buildHeaders(token),
    body: JSON.stringify({
      question,
      subject,
      history,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `質問送信に失敗しました。HTTP ${res.status}`);
  }

  const data = (await res.json()) as AskResponse;
  return data;
}
