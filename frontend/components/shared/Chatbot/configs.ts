import { Vertical } from "./types";

export const CONFIGS: Record<
  Vertical,
  {
    title: string;
    initialMessage: string;
    quickReplies: { id: string; text: string }[];
  }
> = {
  hvac: {
    title: "HVAC Elite Assistant",
    initialMessage: "Welcome. How can we optimize your comfort today?",
    quickReplies: [
      { id: "ac", text: "AC Performance" },
      { id: "heat", text: "Heating Optimization" },
      { id: "maint", text: "Elite Maintenance" },
    ],
  },
  roofing: {
    title: "Roofing Specialist",
    initialMessage: "Greetings. Are you seeking an inspection or reporting damage?",
    quickReplies: [
      { id: "leak", text: "Leak Detection" },
      { id: "storm", text: "Storm Assessment" },
      { id: "inspect", text: "Premium Inspection" },
    ],
  },
  plumbing: {
    title: "Plumbing Concierge",
    initialMessage: "Hello. Is this a priority request or routine maintenance?",
    quickReplies: [
      { id: "emergency", text: "Priority Service" },
      { id: "drain", text: "System Clearing" },
      { id: "leak", text: "Pipe Optimization" },
    ],
  },
  pest_control: {
    title: "Shield Pest Control",
    initialMessage: "Active defense enabled. What pest challenge are you facing?",
    quickReplies: [
      { id: "rodents", text: "Rodent Control" },
      { id: "insects", text: "Insect Shield" },
      { id: "termites", text: "Termite Defense" },
    ],
  },
  general: {
    title: "Automedge Platinum",
    initialMessage: "Welcome to the future of home services. How may we assist?",
    quickReplies: [
      { id: "demo", text: "Schedule Concierge" },
      { id: "price", text: "Investment Plans" },
      { id: "how", text: "Our Philosophy" },
    ],
  },
};

export const uid = () => 
  typeof crypto !== 'undefined' && crypto.randomUUID 
    ? crypto.randomUUID() 
    : Math.random().toString(36).substring(2, 11);
