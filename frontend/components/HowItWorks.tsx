"use client";

import { m as motion } from "framer-motion";
import {
  Zap,
  Bot,
  CalendarCheck2,
  ArrowRight,
  ArrowDown,
  MousePointerClick,
  Clock,
  Star,
} from "lucide-react";

const steps = [
  {
    icon: MousePointerClick,
    title: "Lead Capture",
    description:
      "Multi-source lead ingestion from web forms, ads, and voice calls.",
    color: "from-blue-400 to-indigo-500",
    shadow: "shadow-blue-400/20",
    iconColor: "text-blue-500",
    bgColor: "bg-blue-400/5",
    dropShadow: "drop-shadow-[0_2px_4px_rgba(96,165,250,0.3)]",
  },
  {
    icon: Bot,
    title: "AI Analysis",
    description:
      "Instant qualification and triage based on urgency and issue type.",
    color: "from-purple-400 to-violet-500",
    shadow: "shadow-purple-400/20",
    iconColor: "text-purple-500",
    bgColor: "bg-purple-400/5",
    dropShadow: "drop-shadow-[0_2px_4px_rgba(167,139,250,0.3)]",
  },
  {
    icon: CalendarCheck2,
    title: "Smart Booking",
    description:
      "Deep CRM integration for real-time calendar availability and booking.",
    color: "from-emerald-400 to-teal-500",
    shadow: "shadow-emerald-400/20",
    iconColor: "text-emerald-500",
    bgColor: "bg-emerald-400/5",
    dropShadow: "drop-shadow-[0_2px_4px_rgba(52,211,153,0.3)]",
  },
  {
    icon: Clock,
    title: "Auto Follow-up",
    description:
      "Multi-touch nurturing for leads who aren't ready to book immediately.",
    color: "from-rose-400 to-pink-500",
    shadow: "shadow-rose-400/20",
    iconColor: "text-rose-500",
    bgColor: "bg-rose-400/5",
    dropShadow: "drop-shadow-[0_2px_4px_rgba(251,113,133,0.3)]",
  },
  {
    icon: Star,
    title: "Review Gen",
    description:
      "Post-job satisfaction checks and automated Google review requests.",
    color: "from-amber-400 to-yellow-500",
    shadow: "shadow-amber-400/20",
    iconColor: "text-amber-500",
    bgColor: "bg-amber-400/5",
    dropShadow: "drop-shadow-[0_2px_4px_rgba(251,191,36,0.3)]",
  },
];

export const HowItWorks = () => {
  return (
    <section className="relative py-32 px-6 overflow-hidden" id="how-it-works">
      {/* Background Decorators */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full pointer-events-none -z-10">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-emerald-500/5 rounded-full blur-[100px] animate-pulse delay-700" />
      </div>

      <div className="max-w-[1400px] mx-auto">
        <div className="text-center mb-24">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent/10 border border-accent/20 mb-8"
          >
            <Zap size={14} className="text-accent fill-accent" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-accent">
              Our Process
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-5xl md:text-7xl font-outfit font-black leading-[1.1] mb-8 tracking-tighter text-slate-900 dark:text-white"
          >
            The lead lifecycle, <br />
            <span className="text-transparent bg-clip-text bg-linear-to-r from-accent to-emerald-500">
              completely automated.
            </span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg md:text-xl text-slate-500 dark:text-slate-400 max-w-2xl mx-auto font-medium"
          >
            Stop losing jobs to slow replies. Our AI handles every stage from
            capture to follow-up and reviews.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-y-16 lg:gap-8 relative items-start">
          {/* Connecting Line removed as requested */}

          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1, duration: 0.6 }}
              className="group relative"
            >
              <div className="flex flex-col items-center">
                {/* Step Icon & Number Hub */}
                <div className="relative mb-10 w-24 h-24">
                  {/* Outer Glow */}
                  <div
                    className={`absolute -inset-2 bg-linear-to-br ${step.color} rounded-[32px] blur-xl opacity-0 group-hover:opacity-25 transition-all duration-500`}
                  />

                  {/* Icon Card */}
                  <div
                    className={`relative w-24 h-24 rounded-[32px] bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 ${step.shadow} flex items-center justify-center transition-all duration-500 group-hover:-translate-y-2 group-hover:rotate-3 group-hover:bg-white dark:group-hover:bg-slate-800 shadow-xl`}
                  >
                    <step.icon
                      size={32}
                      className={`${step.iconColor} transition-transform duration-500 group-hover:scale-110`}
                    />

                    {/* Interior gradient shine on hover */}
                    <div
                      className={`absolute inset-0 bg-linear-to-br ${step.color} opacity-0 group-hover:opacity-5 rounded-[32px] transition-opacity`}
                    />
                  </div>
                </div>

                <div className="text-center px-4 space-y-4">
                  <h3 className="text-xl font-outfit font-black text-slate-900 dark:text-white tracking-tight leading-tight">
                    {step.title}
                  </h3>
                  <p className="text-[14px] text-slate-500 dark:text-slate-400 leading-relaxed font-semibold opacity-80">
                    {step.description}
                  </p>
                </div>

                {/* ARROW DECORATORS (Adaptive) */}
                {i < steps.length - 1 && (
                  <div className="relative lg:absolute lg:-right-8 lg:top-[100px] mt-8 lg:mt-0 z-20 flex items-center justify-center">
                    {/* Desktop Arrow */}
                    <div
                      className={`hidden lg:block text-amber-400 transition-colors`}
                    >
                      <ArrowRight
                        size={32}
                        strokeWidth={3}
                        className="drop-shadow-[0_2px_4px_rgba(251,191,36,0.3)]"
                      />
                    </div>
                    {/* Mobile Arrow */}
                    <div className="lg:hidden text-amber-400 flex flex-col items-center gap-2">
                      <div className="w-[2px] h-8 bg-linear-to-b from-transparent via-amber-400/50 to-amber-400 rounded-full" />
                      <ArrowDown
                        size={28}
                        strokeWidth={3}
                        className="drop-shadow-[0_2px_4px_rgba(251,191,36,0.3)]"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Hover Glow Plate */}
              <div
                className={`absolute inset-0 ${step.bgColor} rounded-[40px] opacity-0 group-hover:opacity-100 transition-all duration-500 -z-10 blur-xl scale-95 group-hover:scale-105`}
              />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
