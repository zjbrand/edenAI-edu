import { API_BASE } from "../lib/api";

export type TeacherItem = {
  id: number;
  email: string;
  full_name?: string | null;
  avatar?: string | null;
};

export type ConversationItem = {
  user_id: number;
  email: string;
  full_name?: string | null;
  avatar?: string | null;
  role: string;
  is_active?: boolean;
  last_message: string;
  last_at: string;
  unread_count: number;
};

export type DirectMessageItem = {
  id: number;
  sender_id: number;
  recipient_id: number;
  content: string;
  is_read: boolean;
  created_at: string;
};

function auth(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export async function apiListTeachers(token: string): Promise<TeacherItem[]> {
  const res = await fetch(`${API_BASE}/messages/teachers`, {
    headers: { ...auth(token) },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiListConversations(token: string): Promise<ConversationItem[]> {
  const res = await fetch(`${API_BASE}/messages/conversations`, {
    headers: { ...auth(token) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiGetConversation(token: string, partnerId: number): Promise<DirectMessageItem[]> {
  const res = await fetch(`${API_BASE}/messages/conversations/${partnerId}`, {
    headers: { ...auth(token) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiSendDirectMessage(token: string, toUserId: number, content: string): Promise<DirectMessageItem> {
  const res = await fetch(`${API_BASE}/messages/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...auth(token),
    },
    body: JSON.stringify({ to_user_id: toUserId, content }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiMarkConversationRead(token: string, partnerId: number): Promise<{ ok: boolean; updated: number }> {
  const res = await fetch(`${API_BASE}/messages/conversations/${partnerId}/read`, {
    method: "POST",
    headers: { ...auth(token) },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiUnreadCount(token: string): Promise<number> {
  const res = await fetch(`${API_BASE}/messages/unread-count`, {
    headers: { ...auth(token) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return Number(data?.count ?? 0);
}
