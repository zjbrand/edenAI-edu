import { API_BASE } from "../lib/api";

export type CodeScoreResponse = {
  history_id?: number | null;
  is_code: boolean;
  message: string;
  correctness: number;
  style: number;
  efficiency: number;
  total_score: number;
  issues: string[];
  improvements: string[];
  llm_feedback?: string | null;
};

export type CodeScoreHistorySummary = {
  id: number;
  title: string;
  total_score: number;
  updated_at: string;
  preview: string;
};

export type CodeScoreHistoryDetail = CodeScoreResponse & {
  id: number;
  title: string;
  code: string;
  updated_at: string;
};

export async function apiScoreCode(token: string, code: string): Promise<CodeScoreResponse> {
  const res = await fetch(`${API_BASE}/api/code-review/score`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ code }),
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function apiListCodeScoreHistory(token: string): Promise<CodeScoreHistorySummary[]> {
  const res = await fetch(`${API_BASE}/api/code-review/history`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function apiGetCodeScoreHistory(token: string, historyId: number): Promise<CodeScoreHistoryDetail> {
  const res = await fetch(`${API_BASE}/api/code-review/history/${historyId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function apiRenameCodeScoreHistory(token: string, historyId: number, title: string) {
  const res = await fetch(`${API_BASE}/api/code-review/history/${historyId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json() as Promise<{ ok: boolean; id: number; title: string }>;
}

export async function apiDeleteCodeScoreHistory(token: string, historyId: number) {
  const res = await fetch(`${API_BASE}/api/code-review/history/${historyId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json() as Promise<{ ok: boolean; id: number }>;
}
