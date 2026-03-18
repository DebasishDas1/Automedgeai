"use client";

import { motion } from "framer-motion";
import {
  Wind,
  Droplet,
  Bug,
  Home,
  Zap,
  ChevronDown,
  Webhook,
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
    color: "from-blue-500 to-cyan-400",
    href: "/demo-hvac",
  },
  {
    id: "plumbing",
    title: "Plumbing",
    description: "Instant dispatching for emergency leaks.",
    icon: Droplet,
    color: "from-cyan-500 to-sky-400",
    href: "/demo-plumbing",
  },
  {
    id: "pest",
    title: "Pest Control",
    description: "Convert seasonal inquiries into bookings.",
    icon: Bug,
    color: "from-emerald-500 to-green-400",
    href: "/demo-pest-control",
  },
  {
    id: "roofing",
    title: "Roofing",
    description: "Qualify storm damage leads instantly.",
    icon: Home,
    color: "from-amber-500 to-orange-400",
    href: "/demo-roofing",
  },
];

// ─── Premium Card ─────────────────────────
const DemoCard = memo(({ demo }: any) => {
  const Icon = demo.icon;

  return (
    <Link href={demo.href} className="group block">
      <motion.div
        whileHover={{ y: -6, scale: 1.04 }}
        transition={{ type: "spring", stiffness: 240, damping: 18 }}
        className="relative rounded-3xl"
      >
        {/* Neon ambient glow */}
        <div
          className={`absolute -inset-3 rounded-[28px] bg-linear-to-br ${demo.color} opacity-25 blur-3xl group-hover:opacity-50 transition duration-500`}
        />

        {/* Transparent Glass Card */}
        <div className="relative h-full rounded-3xl backdrop-blur-2xl bg-white/5 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.4)] p-6 text-center">
          {/* Icon */}
          <div className="flex justify-center mb-4">
            <div
              className={`p-4 rounded-2xl bg-linear-to-br ${demo.color} text-white shadow-lg group-hover:scale-110 transition-transform duration-300`}
            >
              <Icon className="w-7 h-7" />
            </div>
          </div>

          {/* Title */}
          <h4 className="text-lg font-semibold tracking-tight text-white mb-2">
            {demo.title}
          </h4>

          {/* Description */}
          <p className="text-sm text-white/70 leading-relaxed max-w-[220px] mx-auto">
            {demo.description}
          </p>

          {/* Subtle hover overlay */}
          <div className="pointer-events-none absolute inset-0 rounded-3xl bg-white/10 opacity-0 group-hover:opacity-100 transition duration-300" />
        </div>
      </motion.div>
    </Link>
  );
});

// ─── Node (minimal) ─────────────────────────
const Node = memo(({ children, label }: any) => (
  <div className="flex flex-col items-center gap-2 text-center">
    {children}
    <span className="text-xs text-muted-foreground">{label}</span>
  </div>
));

// ─── Main Section ─────────────────────────
export function DemoWorkflowSection() {
  return (
    <section className="py-24 px-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-14">
        <h2 className="text-5xl md:text-6xl font-bold mb-4">
          See the AI in <span className="text-accent">Action</span>
        </h2>

        <p className="text-muted-foreground max-w-xl mx-auto">
          Watch how AI captures and books leads automatically.
        </p>
      </div>

      {/* Layout */}
      <div className="flex flex-col items-center gap-4">
        {/* Trigger */}
        <Node label="New Lead">
          <div className="w-14 h-14 rounded-xl border flex items-center justify-center">
            <Webhook className="w-6 h-6 text-muted-foreground" />
          </div>
        </Node>

        <ChevronDown className="hidden md:block mx-auto opacity-30" />

        {/* AI */}
        <Node label="AI Agent">
          <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center">
            <Zap className="w-7 h-7 text-accent" />
          </div>
        </Node>

        <ChevronDown className="hidden md:block mx-auto opacity-30" />

        {/* Cards */}
        <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {DEMOS.map((demo) => (
            <DemoCard key={demo.id} demo={demo} />
          ))}
        </div>
      </div>
    </section>
  );
}
