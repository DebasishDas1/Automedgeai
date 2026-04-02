// lib/api/retell.ts
// Handles web call session creation for Retell AI.

const baseUrl = () =>
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface WebCallSession {
  access_token: string;
  call_id:      string;
}

export async function createWebCall(type?: string): Promise<WebCallSession> {
  const res = await fetch(`${baseUrl()}/api/v1/retell/create-web-call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type: type || null }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || "Failed to create web call session");
  }

  return res.json();
}
