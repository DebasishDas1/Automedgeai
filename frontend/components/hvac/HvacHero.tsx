'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export const HvacHero = () => {
    return (
        <section className="relative pt-32 pb-20 px-6 bg-[#EEF2F5] dark:bg-slate-950 overflow-hidden transition-colors duration-500">
            {/* Background Gradients - Simplified for better performance */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#00C2A8]/5 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-[10%] right-[-10%] w-[50%] h-[50%] bg-orange-500/5 dark:bg-orange-950/10 rounded-full blur-[120px]"></div>
            </div>

            <div className="max-w-7xl mx-auto relative z-10 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
                {/* Headline Section */}
                <div className="relative inline-block mb-16 px-4">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-slate-900 shadow-sm border border-slate-200 dark:border-slate-800 mb-8">
                        <span className="flex h-2 w-2 rounded-full bg-[#00C2A8] animate-pulse"></span>
                        <span className="text-[10px] font-black tracking-widest uppercase text-slate-500 dark:text-slate-400">
                            The #1 Automation Tool for HVAC
                        </span>
                    </div>

                    <h1 className="text-[48px] md:text-[80px] lg:text-[110px] font-outfit font-[900] tracking-[-0.05em] leading-[0.85] text-[#1A1A1A] dark:text-white">
                        Every Lead <br className="hidden md:block" />
                        <span className="text-[#00C2A8] relative">
                            Answered
                            <svg className="absolute -bottom-2 lg:-bottom-4 left-0 w-full" height="8" viewBox="0 0 400 8" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M4 4C60 2 120 2 396 4" stroke="#00C2A8" strokeWidth="6" strokeLinecap="round" opacity="0.3" />
                            </svg>
                        </span>
                    </h1>

                    <p className="mt-8 text-lg md:text-2xl text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto leading-relaxed">
                        Stop losing HVAC jobs to slow replies. Automedge follows up with every lead in 60 seconds — while you're still on the job site.
                    </p>
                </div>

                {/* CTA Buttons */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-20">
                    <Link href="#contact" className="w-full sm:w-auto">
                        <button className="w-full h-16 px-10 bg-[#00C2A8] text-white rounded-full font-bold text-xl hover:scale-105 active:scale-95 transition-all shadow-xl shadow-[#00C2A8]/20 flex items-center justify-center gap-3">
                            Claim My 14-Day Trial →
                        </button>
                    </Link>
                    <Link href="#demo" className="w-full sm:w-auto">
                        <button className="w-full h-16 px-10 bg-white dark:bg-slate-900 text-[#1A1A1A] dark:text-white rounded-full font-bold text-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all flex items-center justify-center">
                            Watch Video Demo
                        </button>
                    </Link>
                </div>

                {/* Main Hero Image Container - LCP Optimized */}
                <div className="relative w-full max-w-6xl mx-auto rounded-[32px] overflow-hidden aspect-video shadow-2xl border border-slate-200/50 dark:border-slate-800/50 bg-white dark:bg-slate-900 group">
                    <Image
                        src="/hvac.png"
                        alt="HVAC technician at work"
                        fill
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 90vw, 1200px"
                        className="object-cover group-hover:scale-105 transition-transform duration-1000"
                        priority
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent pointer-events-none"></div>

                    {/* Overlay Badges */}
                    <div className="absolute bottom-8 left-8 p-4 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md rounded-2xl shadow-xl hidden md:block border border-white/20">
                        <div className="flex gap-1 text-orange-400 mb-1 text-xs">★★★★★</div>
                        <div className="text-xl font-black text-slate-900 dark:text-white font-outfit tracking-tight">"Saves me 10+ hours/week."</div>
                        <div className="text-[10px] font-black text-slate-500 uppercase mt-1 tracking-widest">— Mike Johnson, MJ Cooling</div>
                    </div>
                </div>
            </div>
        </section>
    );
};
