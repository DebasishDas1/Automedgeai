import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Lead, VerticalType, FirebaseUser } from '../../types';

interface AutomedgeStore {
    // Auth
    user: FirebaseUser | null;
    setUser: (user: FirebaseUser | null) => void;

    // Current vertical context
    vertical: VerticalType | null;
    setVertical: (v: VerticalType | null) => void;

    // Leads (dashboard)
    leads: Lead[];
    setLeads: (leads: Lead[]) => void;
    updateLeadStage: (id: string, stage: Lead['stage']) => void;

    // Demo state
    demoStep: number;
    demoRunning: boolean;
    startDemo: () => void;
    resetDemo: () => void;
    setDemoStep: (step: number) => void;
}

export const useStore = create<AutomedgeStore>()(
    persist(
        (set) => ({
            user: null,
            setUser: (user: FirebaseUser | null) => set({ user }),

            vertical: null,
            setVertical: (vertical: VerticalType | null) => set({ vertical }),

            leads: [],
            setLeads: (leads: Lead[]) => set({ leads }),
            updateLeadStage: (id: string, stage: Lead['stage']) =>
                set((state: AutomedgeStore) => ({
                    leads: state.leads.map((l) => (l.id === id ? { ...l, stage } : l)),
                })),

            demoStep: 0,
            demoRunning: false,
            startDemo: () => set({ demoRunning: true, demoStep: 1 }),
            resetDemo: () => set({ demoRunning: false, demoStep: 0 }),
            setDemoStep: (demoStep: number) => set({ demoStep }),
        }),
        {
            name: 'automedge-storage',
            partialize: (state: AutomedgeStore) => ({ vertical: state.vertical }),
        }
    )
);
