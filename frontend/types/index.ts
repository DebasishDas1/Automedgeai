export type VerticalType = 'hvac' | 'roofing' | 'plumbing' | 'pest_control';

export interface Lead {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  source: string;
  vertical: VerticalType;
  stage: 'new' | 'contacted' | 'quoted' | 'booked' | 'done';
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface Job {
  id: string;
  lead_id: string;
  tech_name?: string;
  scheduled?: string;
  status: string;
  notes?: string;
}

export interface Booking {
  id: string;
  name: string;
  email: string;
  vertical: VerticalType;
  created_at: string;
}

export interface Vertical {
  slug: VerticalType;
  label: string;
  pain: string;
  fix: string;
  demoLead: {
    name: string;
    issue: string;
    city: string;
    source: string;
  };
}

export interface WorkflowEvent {
  step: number;
  label: string;
  status: 'active' | 'completed' | 'pending';
  ts: string;
}

export interface FirebaseUser {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
}
