import { API_BASE } from "../lib/api";

export type TestAnswerAnalysisResponse = {
  history_id?: number | null;
  judgement: string;
  issues: string[];
  suggestions: string[];
  correct_answer: string;
  feedback: string;
};

export type TestAnswerHistorySummary = {
  id: number;
  title: string;
  judgement: string;
  updated_at: string;
  preview: string;
};

export type TestAnswerHistoryDetail = TestAnswerAnalysisResponse & {
  id: number;
  title: string;
  question: string;
  user_answer: string;
  updated_at: string;
};

export async function apiAnalyzeTestAnswer(
  token: string,
  question: string,
  userAnswer: string
): Promise<TestAnswerAnalysisResponse> {
  const res = await fetch(`${API_BASE}/api/test-answer-analysis/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question, user_answer: userAnswer }),
  });

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function apiListTestAnswerHistory(token: string): Promise<TestAnswerHistorySummary[]> {
  const res = await fetch(`${API_BASE}/api/test-answer-analysis/history`, {
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

export async function apiGetTestAnswerHistory(token: string, historyId: number): Promise<TestAnswerHistoryDetail> {
  const res = await fetch(`${API_BASE}/api/test-answer-analysis/history/${historyId}`, {
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

export async function apiRenameTestAnswerHistory(token: string, historyId: number, title: string) {
  const res = await fetch(`${API_BASE}/api/test-answer-analysis/history/${historyId}`, {
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

export async function apiDeleteTestAnswerHistory(token: string, historyId: number) {
  const res = await fetch(`${API_BASE}/api/test-answer-analysis/history/${historyId}`, {
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
