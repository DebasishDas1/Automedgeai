"use client";

import { m as motion } from "framer-motion";
import {
  Wind,
  Droplet,
  Bug,
  Home,
  Zap,
  ChevronDown,
  Webhook,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { memo } from "react";

// ─── Config ─────────────────────────
const DEMOS = [
  {
    id: "hvac",
    title: "HVAC",
    description: "Book 30% more furnace repairs automatically.",
    icon: Wind,
    href: "/demo-hvac",
  },
  {
    id: "plumbing",
    title: "Plumbing",
    description: "Instant dispatching for emergency leaks.",
    icon: Droplet,
    href: "/demo-plumbing",
  },
  {
    id: "pest",
    title: "Pest Control",
    description: "Convert seasonal inquiries into bookings.",
    icon: Bug,
    href: "/demo-pest-control",
  },
  {
    id: "roofing",
    title: "Roofing",
    description: "Qualify storm damage leads instantly.",
    icon: Home,
    href: "/demo-roofing",
  },
];

// ─── Premium Card ─────────────────────────
const DemoCard = memo(({ index, demo }: any) => {
  const { title, description, href } = demo;
  const Icon = demo.icon;

  return (
    <Link href={href} scroll={true} className="group block relative h-full">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: index * 0.1, duration: 0.6 }}
        className="relative h-full"
      >
        {/* EXTERNAL CARD GLOW (Outside Card) */}
        <div className="absolute -inset-4 bg-amber-500/5 rounded-[3rem] blur-3xl opacity-0 group-hover:opacity-100 transition-all duration-700 -z-10" />

        <div className="relative h-full p-8 rounded-[2.5rem] border border-slate-200 dark:border-white/5 bg-white dark:bg-slate-950/40 backdrop-blur-3xl transition-all duration-500 shadow-xl group-hover:shadow-[0_20px_60px_-15px_rgba(245,158,11,0.25)] flex flex-col items-center text-center">
          {/* Step Icon HUB (Clean look, no individual outside shadow) */}
          <div className="relative mb-8 w-24 h-24">
            {/* Icon Card */}
            <div className="relative w-24 h-24 rounded-[32px] bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 flex items-center justify-center transition-all duration-500 group-hover:-translate-y-2 group-hover:rotate-3 group-hover:bg-white dark:group-hover:bg-slate-800">
              <Icon
                size={36}
                className="text-amber-500 transition-transform duration-500 group-hover:scale-110"
              />

              {/* Interior gradient shine on hover */}
              <div className="absolute inset-0 bg-linear-to-br from-amber-400 to-yellow-500 opacity-0 group-hover:opacity-8 rounded-[32px] transition-opacity" />
            </div>
          </div>

          <div className="space-y-4 relative z-10">
            <h3 className="text-3xl font-outfit font-black leading-tight tracking-tighter text-slate-800 dark:text-white transition-colors group-hover:text-amber-500">
              {title}
            </h3>
            <p className="text-[17px] text-slate-500 dark:text-slate-400 leading-relaxed font-semibold opacity-80 max-w-[280px]">
              {description}
            </p>
          </div>

          {/* Bottom Call to Action */}
          <div className="mt-8 flex items-center gap-2 text-amber-500 font-black uppercase tracking-[0.2em] text-[10px] transform translate-y-2 opacity-0 group-hover:opacity-100 group-hover:translate-y-0 transition-all">
            Explore {title} Solution
            <ArrowRight className="w-4 h-4" />
          </div>
        </div>
      </motion.div>
    </Link>
  );
});

// ─── Node (minimal) ─────────────────────────
const Node = memo(({ children, label, glow }: any) => (
  <div className="flex flex-col items-center gap-4 text-center group relative">
    <div
      className={`relative ${glow ? "shadow-[0_0_30px_rgba(29,158,117,0.4)]" : ""} transition-all duration-500`}
    >
      {children}
    </div>
    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground group-hover:text-accent transition-colors">
      {label}
    </span>
  </div>
));

// ─── Main Section ─────────────────────────
export function DemoWorkflowSection() {
  return (
    <section
      id="the-engine"
      className="py-32 px-6 max-w-7xl mx-auto overflow-hidden relative"
    >
      {/* Background decoration */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full bg-[radial-gradient(circle_at_center,var(--tw-gradient-stops))] from-amber-500/5 via-transparent to-transparent -z-10" />

      {/* Header */}
      <div className="text-center mb-20">
        <div className="inline-flex items-center gap-2 bg-amber-500/10 px-4 py-2 rounded-full text-amber-500 font-black text-xs uppercase tracking-widest mb-6 border border-amber-500/20">
          <Zap className="w-3.5 h-3.5 fill-current" />
          The Industry Engine
        </div>
        <h2 className="text-5xl md:text-7xl font-outfit font-black mb-6 tracking-tighter leading-none text-slate-900 dark:text-white">
          See the AI in{" "}
          <span className="text-accent underline decoration-accent/20 decoration-8 underline-offset-8">
            Action
          </span>
        </h2>

        <p className="text-xl text-slate-500 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed font-semibold opacity-80">
          Tailored workflows for every home service niche. Capture, qualify, and
          book in 60 seconds.
        </p>
      </div>

      {/* Layout */}
      <div className="flex flex-col items-center gap-8 relative">
        {/* Connection Line */}
        <div className="absolute top-10 bottom-40 w-px bg-linear-to-b from-amber-500/20 via-amber-500/40 to-transparent -z-10" />

        {/* Trigger */}
        <Node label="New Inquiry">
          <div className="w-16 h-16 rounded-[1.25rem] border-2 border-slate-200 dark:border-white/10 bg-white dark:bg-slate-950 shadow-xl flex items-center justify-center hover:scale-110 transition-transform cursor-help">
            <Webhook className="w-7 h-7 text-cta opacity-60" />
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-cta-foreground rounded-full animate-ping" />
            <div className="absolute -top-1 -right-1 w-4 h-4 bg-cta-foreground rounded-full" />
          </div>
        </Node>

        <div className="p-2 bg-white dark:bg-slate-900 rounded-full border border-slate-200 dark:border-white/10 shadow-sm">
          <ChevronDown className="w-5 h-5 text-amber-500 animate-bounce" />
        </div>

        {/* AI */}
        <Node label="AutomEdge AI Core">
          <div className="w-24 h-24 rounded-3xl bg-accent/10 border border-accent/20 flex items-center justify-center relative shadow-2xl shadow-accent/10">
            <Zap className="w-10 h-10 text-accent fill-accent" />
            <div className="absolute -inset-2 bg-accent/10 blur-xl rounded-full -z-10" />
          </div>
        </Node>

        <div className="p-2 bg-white dark:bg-slate-900 rounded-full border border-slate-200 dark:border-white/10 shadow-sm mb-8">
          <ChevronDown className="w-5 h-5 text-amber-500 animate-bounce [animation-delay:200ms]" />
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8 w-full max-w-5xl">
          {DEMOS.map((demo, index) => (
            <DemoCard key={demo.id} demo={demo} index={index} />
          ))}
        </div>
      </div>
    </section>
  );
}
