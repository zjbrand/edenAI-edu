export type Role = "user" | "assistant";

export interface Message {
  role: Role;
  content: string;
  responseId?: number;
  rating?: number | null;
  ratingPending?: boolean;
  createdAt?: string;
}

export interface AskResponse {
  answer: string;
  response_id: number | null;
  conversation_id: number;
}

export interface ChatSessionSummary {
  id: number;
  title: string;
  subject: string;
  last_message: string;
  updated_at: string;
}

export interface ChatSessionDetail {
  id: number;
  title: string;
  subject: string;
  updated_at: string;
  messages: Array<{
    id: number;
    role: Role;
    content: string;
    response_id?: number | null;
    rating?: number | null;
    created_at: string;
  }>;
}

export type View = "chat" | "admin" | "knowledge" | "messages" | "settings" | "code_score";
export type Theme = "dark" | "light";
export type AuthMode = "login" | "register";


