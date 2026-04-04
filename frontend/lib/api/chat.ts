// lib/api/chat.ts
/**
 * Frontend API client for Automedge Unified Chat.
 * Optimized for consolidated backend endpoints (/api/v1/chat/*).
 */

const baseUrl = () =>
  process.env.NEXT_PUBLIC_API_URL ?? "https://automedge-backend.onrender.com";

export interface StartChatResponse {
  session_id: string;
  vertical:   string;
  turn:       number;
}

export interface SendMessageResponse {
  session_id:       string;
  message:          string;
  turn:             number;
  is_complete:      boolean;
  appt_booked:      boolean;
  fields_collected: Record<string, unknown>;
}

export interface MessageMetadata {
  is_complete:      boolean;
  turn:             number;
  appt_booked:      boolean;
  fields_collected: Record<string, unknown>;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(`${status}: ${detail}`);
    this.name = "ApiError";
  }
}

// ── Core fetch wrapper ────────────────────────────────────────────────────────

async function post<T>(
  path: string,
  body: unknown,
  timeoutMs = 15_000,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${baseUrl()}${path}`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
      signal:  controller.signal,
    });

    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new ApiError(res.status, detail);
    }

    return res.json() as Promise<T>;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(408, "Request timed out. The server may be waking up — try again.");
    }
    throw new ApiError(0, err instanceof Error ? err.message : "Network error");
  } finally {
    clearTimeout(timer);
  }
}

// ── API calls ─────────────────────────────────────────────────────────────────

/**
 * Starts a new chat session. The vertical (hvac, plumbing, etc.) is now 
 * sent in the request body to facilitate a universal /start endpoint.
 */
export const startChatSession = (
  vertical: string,
  userInfo?: { name: string; email: string; phone: string },
  source = "web_chat",
) => {
  // Normalize vertical names (e.g. general -> hvac)
  const backendVertical = vertical === "general" ? "hvac" : vertical;
  
  return post<StartChatResponse>(
    "/api/v1/chat/start",
    { vertical: backendVertical, source, ...userInfo },
    20_000,
  );
};

/**
 * SSE streaming wrapper for chat messages.
 * Unified endpoint: session_id automatically determines the vertical context.
 */
export async function streamChatMessage(
  session_id: string,
  message:    string,
  onChunk:    (chunk: string) => void,
  onMetadata: (meta: MessageMetadata) => void,
) {
  const res = await fetch(`${baseUrl()}/api/v1/chat/message/stream`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ session_id, message }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, detail);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("Stream reader not available");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    
    // SSE emits chunks separated by double newline
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() || ""; // last piece might be partial

    for (const chunk of chunks) {
      const line = chunk.trim();
      if (!line.startsWith("data: ")) continue;
      
      const raw = line.slice(6).trim();
      if (raw === "[DONE]") return;

      try {
        const payload = JSON.parse(raw);
        if (payload.chunk) {
          onChunk(payload.chunk);
        } else if (payload.metadata) {
          onMetadata(payload.metadata);
        } else if (payload.error) {
          throw new Error(payload.error);
        }
      } catch (e) {
        console.warn("Failed to parse SSE payload", e);
      }
    }
  }
}