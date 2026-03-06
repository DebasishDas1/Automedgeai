import React from 'react';
import Link from 'next/link';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen bg-slate-950 text-slate-50">
            {/* Sidebar */}
            <aside className="w-64 border-r border-slate-800 p-6 flex flex-col gap-8">
                <div className="text-2xl font-bold font-syne text-emerald-400">
                    Automedge
                </div>
                <nav className="flex flex-col gap-2">
                    <Link href="/dashboard" className="p-3 rounded-lg bg-slate-800 text-emerald-400 font-medium">
                        Pipeline
                    </Link>
                    <Link href="/dashboard/leads" className="p-3 rounded-lg hover:bg-slate-900 text-slate-400 hover:text-white transition-colors">
                        Leads
                    </Link>
                    <Link href="/dashboard/settings" className="p-3 rounded-lg hover:bg-slate-900 text-slate-400 hover:text-white transition-colors">
                        Settings
                    </Link>
                </nav>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/50 backdrop-blur-md">
                    <h2 className="text-xl font-semibold">Lead Pipeline</h2>
                    <div className="flex items-center gap-4">
                        <div className="text-sm text-slate-400">Mike's HVAC Services</div>
                        <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center font-bold text-slate-900">
                            M
                        </div>
                    </div>
                </header>
                <div className="flex-1 overflow-auto p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
