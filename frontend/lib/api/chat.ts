// lib/api/chat.ts
const API = () => process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StartChatResponse {
  session_id: string;
  vertical: string;
  // message: string;
  turn: number;
}

export interface SendMessageResponse {
  session_id: string;
  message: string;
  turn: number;
  is_complete: boolean;
  appt_booked: boolean;
  fields_collected: Record<string, unknown>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const startChatSession = (vertical: string, source = "web_chat") =>
  post<StartChatResponse>(`/api/v1/chat/${vertical}/start`, { source });

export const sendChatMessage = (vertical: string, session_id: string, message: string) =>
  post<SendMessageResponse>(`/api/v1/chat/${vertical}/message`, { session_id, message });