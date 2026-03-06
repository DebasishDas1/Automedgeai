'use client';

import React from 'react';
import { useStore } from '@/lib/zustand/store';

const stages = ['new', 'contacted', 'quoted', 'booked', 'done'] as const;

export default function DashboardPage() {
    const { leads } = useStore();

    return (
        <div className="grid grid-cols-5 gap-6 h-full">
            {stages.map((stage) => (
                <div key={stage} className="flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                        <h3 className="font-bold uppercase text-xs tracking-widest text-slate-500">
                            {stage}
                        </h3>
                        <span className="bg-slate-800 text-slate-400 px-2 py-0.5 rounded text-[10px] font-bold">
                            {leads.filter(l => l.stage === stage).length}
                        </span>
                    </div>
                    <div className="flex-1 bg-slate-900/50 border border-slate-800/50 rounded-xl p-4 space-y-4 min-h-[500px]">
                        {leads
                            .filter((l) => l.stage === stage)
                            .map((lead) => (
                                <div
                                    key={lead.id}
                                    className="bg-slate-800 border border-slate-700 p-4 rounded-lg shadow-sm hover:border-emerald-500/50 transition-colors cursor-pointer group"
                                >
                                    <p className="font-semibold group-hover:text-emerald-400">{lead.name}</p>
                                    <p className="text-xs text-slate-400 mt-1">{lead.source} · {lead.vertical}</p>
                                </div>
                            ))}
                        {leads.filter(l => l.stage === stage).length === 0 && (
                            <div className="h-24 border border-dashed border-slate-800 rounded-lg flex items-center justify-center text-slate-600 text-xs text-center px-4">
                                No leads in this stage
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}
