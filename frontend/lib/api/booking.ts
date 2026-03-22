// lib/api/booking.ts
// Handles direct booking requests from the Calendar component.

const baseUrl = () =>
  process.env.NEXT_PUBLIC_API_URL ?? "https://automedge-backend.onrender.com";

export interface BookingRequest {
  name:         string;
  email:        string;
  business:     string;  // Maps to "Company Website" or similar
  vertical:     string;  // "hvac", etc.
  scheduled_at: string;  // ISO string
  team_size?:   string;
}

export interface BookingResponse {
  id:           string;
  name:         string;
  email:        string;
  business:     string;
  vertical:     string;
  scheduled_at: string;
  created_at:   string;
}

export async function createBooking(data: BookingRequest): Promise<BookingResponse> {
  const res = await fetch(`${baseUrl()}/api/v1/bookings/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || "Failed to submit booking");
  }

  return res.json();
}
