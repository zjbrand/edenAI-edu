export type Role = "user" | "assistant";

export interface Message {
  role: Role;
  content: string;
}

export interface AskResponse {
  answer: string;
}

export type View = "chat" | "admin" | "messages" | "settings" | "code_score";
export type Theme = "dark" | "light";
export type AuthMode = "login" | "register";


