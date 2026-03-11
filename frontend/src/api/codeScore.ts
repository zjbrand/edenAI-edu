import { API_BASE } from "../lib/api";

export type CodeScoreResponse = {
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
