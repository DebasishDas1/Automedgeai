export interface Message {
  id: string;
  text: string;
  sender: "bot" | "user";
  quickReplies?: { id: string; text: string }[];
}

export type Vertical = "hvac" | "roofing" | "plumbing" | "pest_control" | "general";

export interface ChatbotProps {
  vertical?: Vertical;
}

export interface UserInfo {
  name: string;
  email: string;
  phone: string;
}
