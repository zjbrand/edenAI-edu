export type Role = "user" | "assistant";

export interface Message {
  role: Role;
  content: string;
  responseId?: number;
  rating?: number | null;
  ratingPending?: boolean;
}

export interface AskResponse {
  answer: string;
  response_id: number;
}

export type View = "chat" | "admin" | "knowledge" | "messages" | "settings" | "code_score";
export type Theme = "dark" | "light";
export type AuthMode = "login" | "register";


