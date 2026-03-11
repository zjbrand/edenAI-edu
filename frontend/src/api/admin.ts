// frontend/src/api/admin.ts
import { API_BASE } from "../lib/api";

function getToken(): string | null {
  return localStorage.getItem("eden_token");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    ...(init?.headers as Record<string, string>),
  };

  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  if (!isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }

  const ct = res.headers.get("content-type") || "";
  if (!ct.includes("application/json")) {
    return (undefined as unknown) as T;
  }
  return (await res.json()) as T;
}

export type SystemStatus = {
  ok: boolean;
  services: Record<string, string>;
  stats?: {
    users?: number;
    student_count?: number;
    teacher_count?: number;
    inactive_student_count?: number;
    inactive_teacher_count?: number;
    knowledge_docs?: number;
  };
};

export type AdminUser = {
  id: number;
  email: string;
  full_name?: string | null;
  avatar?: string | null;
  role: "student" | "teacher" | "user" | "admin";
  is_active: boolean;
  created_at?: string | null;
};

export function fetchSystemStatus() {
  return request<SystemStatus>("/admin/system/status");
}

export function fetchUsers() {
  return request<AdminUser[]>("/admin/users");
}

export function setUserRole(userId: number, role: "student" | "teacher") {
  return request<AdminUser>(`/admin/users/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export function setUserActive(userId: number, is_active: boolean) {
  return request<AdminUser>(`/admin/users/${userId}/active`, {
    method: "PATCH",
    body: JSON.stringify({ is_active }),
  });
}


