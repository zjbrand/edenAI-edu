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

export type UnansweredMessageItem = {
  id: number;
  student_id: number;
  student_email: string;
  student_name?: string | null;
  student_avatar?: string | null;
  subject: string;
  question: string;
  created_at: string;
};

export type MessagesSocketEvent = {
  type: "connected" | "messages_updated";
  reason?: string;
  unread_count?: number;
  unanswered_count?: number;
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

export async function apiSendDirectMessage(
  token: string,
  toUserId: number,
  content: string,
  linkedUnansweredId?: number | null,
): Promise<DirectMessageItem> {
  const res = await fetch(`${API_BASE}/messages/send`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...auth(token),
    },
    body: JSON.stringify({
      to_user_id: toUserId,
      content,
      linked_unanswered_id: linkedUnansweredId ?? null,
    }),
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

export async function apiListUnansweredMessages(token: string): Promise<UnansweredMessageItem[]> {
  const res = await fetch(`${API_BASE}/messages/unanswered`, {
    headers: { ...auth(token) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function resolveMessagesSocketUrl(token: string): string {
  const base = API_BASE.replace(/^http/i, "ws");
  return `${base}/messages/ws?token=${encodeURIComponent(token)}`;
}

export function createMessagesSocket(token: string): WebSocket {
  return new WebSocket(resolveMessagesSocketUrl(token));
}
