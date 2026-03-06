'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useStore } from '@/lib/zustand/store';
import { Button } from '@/components/ui/button';
import { WorkflowEvent } from '@/types';

export const DemoWorkflow = ({ vertical }: { vertical: string }) => {
    const { demoStep, demoRunning, startDemo, resetDemo, setDemoStep } = useStore();
    const [events, setEvents] = useState<WorkflowEvent[]>([]);

    const streamDemo = async () => {
        startDemo();
        setEvents([]);

        try {
            const res = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/workflow/stream?vertical=${vertical}`,
                { headers: { Accept: 'text/event-stream' } }
            );

            if (!res.body) return;

            const reader = res.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value);
                const lines = text.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim();
                        if (dataStr === '[DONE]') {
                            break;
                        }
                        try {
                            const data = JSON.parse(dataStr);
                            setDemoStep(data.step);
                            setEvents(prev => [...prev, data]);
                        } catch (e) {
                            console.error('Error parsing SSE data', e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('SSE Stream Error:', error);
        } finally {
            // Keep demo running state for a bit to show completion
            setTimeout(() => resetDemo(), 3000);
        }
    };

    const steps = [
        { id: 1, label: 'Lead Captured' },
        { id: 2, label: 'AI Qualification' },
        { id: 3, label: 'SMS Sent' },
        { id: 4, label: 'Call Booked' }
    ];

    return (
        <section className="py-20 px-6 bg-slate-950">
            <div className="max-w-4xl mx-auto border border-slate-800 rounded-3xl p-8 bg-slate-900/50 backdrop-blur-sm">
                <div className="flex justify-between items-center mb-12">
                    <h3 className="text-2xl font-bold font-syne">Live Automation Demo</h3>
                    {!demoRunning ? (
                        <Button onClick={streamDemo} className="bg-emerald-500 hover:bg-emerald-600">
                            Run Demo
                        </Button>
                    ) : (
                        <div className="flex items-center gap-2 text-emerald-400">
                            <span className="relative flex h-3 w-3">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                            </span>
                            Workflow Active
                        </div>
                    )}
                </div>

                <div className="space-y-6 relative">
                    {steps.map((step, index) => (
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{
                                opacity: demoStep >= step.id ? 1 : 0.3,
                                x: 0,
                                scale: demoStep === step.id ? 1.02 : 1
                            }}
                            className={`flex items-center gap-4 p-4 rounded-xl border ${demoStep === step.id
                                    ? 'border-emerald-500 bg-emerald-500/10'
                                    : 'border-slate-800 bg-slate-800/20'
                                }`}
                        >
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${demoStep >= step.id ? 'bg-emerald-500 text-slate-900' : 'bg-slate-700 text-slate-400'
                                }`}>
                                {step.id}
                            </div>
                            <div className="flex-1">
                                <p className="font-semibold">{step.label}</p>
                                {demoStep === step.id && (
                                    <motion.p
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        className="text-sm text-emerald-400"
                                    >
                                        Processing...
                                    </motion.p>
                                )}
                            </div>
                            {demoStep > step.id && (
                                <div className="text-emerald-500 text-sm">Completed</div>
                            )}
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};
