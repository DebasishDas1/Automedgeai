"use client";

import { m as motion } from "framer-motion";
import {
  Zap,
  Wind,
  Droplet,
  Bug,
  Home,
  Sparkles,
  MousePointer2,
  Database,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import { memo } from "react";

// ─────────────────────────────────────────
// n8n Style Graph CONFIG
// ─────────────────────────────────────────
const DEMOS = [
  {
    id: "hvac",
    title: "HVAC",
    description: "Book furnace repairs & installs in under 60 seconds.",
    icon: Wind,
    href: "/demo-hvac",
    theme: "amber",
  },
  {
    id: "plumbing",
    title: "Plumbing",
    description: "Instant qualification for emergency leaks.",
    icon: Droplet,
    href: "/demo-plumbing",
    theme: "blue",
  },
  {
    id: "pest",
    title: "Pest Control",
    description: "Scale seasonal lead capture automatically.",
    icon: Bug,
    href: "/demo-pest-control",
    theme: "emerald",
  },
  {
    id: "roofing",
    title: "Roofing",
    description: "The storm-damage engine for high-volume leads.",
    icon: Home,
    href: "/demo-roofing",
    theme: "purple",
  },
];

// ─────────────────────────────────────────
// Premium Curved Edge with Data Pulse
// ─────────────────────────────────────────
const BezierEdge = ({
  d,
  delay = 0,
  duration = 3,
}: {
  d: string;
  delay?: number;
  duration?: number;
}) => (
  <>
    <motion.path
      d={d}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      className="text-accent/10 dark:text-accent/15"
      initial={{ pathLength: 0, opacity: 0 }}
      whileInView={{ pathLength: 1, opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 1.2, delay, ease: "easeInOut" }}
    />
    <motion.path
      d={d}
      fill="none"
      stroke="url(#pulse-gradient)"
      strokeWidth="2.5"
      strokeLinecap="round"
      initial={{ pathOffset: 0, pathLength: 0.1, opacity: 0 }}
      animate={{ pathOffset: [-1.1, 1.1], opacity: [0, 1, 0] }}
      transition={{
        duration: duration,
        repeat: Infinity,
        delay: delay + 0.5,
        ease: "linear",
      }}
    />
  </>
);

// ─────────────────────────────────────────
// Hyper-Premium Graph Node (DemoCard)
// ─────────────────────────────────────────
const DemoCard = memo(({ index, demo }: any) => {
  const { title, description, href, theme } = demo;
  const Icon = demo.icon;

  const themeStyles: Record<string, string> = {
    amber:
      "text-amber-500 bg-amber-500/5 group-hover:bg-amber-500/10 border-amber-500/20",
    blue: "text-blue-500 bg-blue-500/5 group-hover:bg-blue-500/10 border-blue-500/20",
    emerald:
      "text-emerald-500 bg-emerald-500/5 group-hover:bg-emerald-500/10 border-emerald-500/20",
    purple:
      "text-purple-500 bg-purple-500/5 group-hover:bg-purple-500/10 border-purple-500/20",
  };

  return (
    <Link
      href={href}
      scroll
      className="group block relative z-10 w-full lg:max-w-[340px]"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.98, y: 20 }}
        whileInView={{ opacity: 1, scale: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{
          delay: index * 0.1,
          duration: 0.6,
          ease: [0.16, 1, 0.3, 1],
        }}
        className="h-full relative"
      >
        <div className="absolute -inset-1 bg-accent/5 rounded-4xl blur-xl opacity-0 group-hover:opacity-100 transition-all duration-700 -z-10" />

        <div
          className="
          relative h-full p-6 md:p-8 rounded-4xl
          bg-slate-900/5 dark:bg-slate-900/40 border border-white/10
          backdrop-blur-2xl transition-all duration-500
          hover:border-accent/30 hover:bg-white/5 dark:hover:bg-slate-900/40
          flex flex-col items-center text-center gap-5 shadow-2xl
        "
        >
          <div className="absolute left-1/2 -top-1.5 -translate-x-1/2 w-4 h-4 rounded-full bg-background border-2 border-border/80 group-hover:bg-accent group-hover:border-accent/40 shadow-sm transition-all z-20" />

          <div
            className={`shrink-0 w-16 h-16 rounded-2xl flex items-center justify-center border ${themeStyles[theme]}`}
          >
            <Icon size={32} strokeWidth={2} />
          </div>

          <div className="flex-1 min-w-0 space-y-2">
            <h3 className="text-2xl font-outfit font-black tracking-tight text-foreground truncate">
              {title}
            </h3>
            <p className="text-sm md:text-base text-muted-foreground line-clamp-2 opacity-70 leading-relaxed font-medium max-w-[240px]">
              {description}
            </p>
          </div>

          <div className="flex items-center justify-center w-full pt-4 group-hover:text-accent transition-colors">
            <span className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground group-hover:text-accent">
              Live Demo
            </span>
            <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" />
          </div>
        </div>
      </motion.div>
    </Link>
  );
});

// ─────────────────────────────────────────
// Hyper-Premium Section Layout
// ─────────────────────────────────────────
export function DemoWorkflowSection() {
  return (
    <section
      id="the-engine"
      className="py-32 md:py-48 px-6 max-w-7xl mx-auto relative overflow-hidden"
    >
      {/* Background: Digital Canvas */}
      <div
        className="absolute inset-0 pointer-events-none -z-20 opacity-[0.03] dark:opacity-[0.10] text-foreground/30"
        style={{
          backgroundImage:
            "radial-gradient(circle, currentColor 1.5px, transparent 1.5px)",
          backgroundSize: "48px 48px",
        }}
      />

      {/* Header */}
      <div className="text-center mb-32 relative">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="inline-flex items-center gap-3 px-6 py-2 rounded-full bg-white/5 border border-white/10 text-accent font-black text-[11px] uppercase tracking-[0.3em] mb-10 shadow-2xl backdrop-blur-xl"
        >
          <Sparkles className="w-4 h-4 fill-accent" />
          The Industry Engine
        </motion.div>

        <h2 className="hero-headline opacity-90 mb-8">
          Neural <span className="text-accent italic">Execution</span> Stack.
        </h2>

        <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto leading-relaxed font-medium opacity-80 px-4">
          Visual orchestration of your business logic. Automated nodes connected
          in a high-performance neural canvas.
        </p>
      </div>

      {/* Graph Area */}
      <div className="relative flex flex-col items-center gap-32 md:gap-40 max-w-6xl mx-auto w-full">
        {/* Trigger Node */}
        <div className="relative z-10">
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="px-8 py-5 rounded-4xl 
               bg-background/60 backdrop-blur-md 
               text-foreground 
               flex items-center gap-5 
               shadow-3xl group cursor-pointer 
               border border-border/40
               shadow-2xl
               "
          >
            {/* Icon Bubble */}
            <div
              className="w-12 h-12 rounded-2xl 
                 flex items-center justify-center
                 bg-amber-500/15 dark:bg-amber-400/15
                 border border-amber-500/30 dark:border-amber-400/30"
            >
              <MousePointer2 className="w-6 h-6 text-amber-600 dark:text-amber-400" />
            </div>

            {/* Text */}
            <div className="text-left">
              <p
                className="text-[10px] font-black uppercase tracking-widest leading-none mb-1 
                     text-amber-600/60 dark:text-amber-400/60"
              >
                Inbound Hook
              </p>
              <p className="text-lg font-bold leading-none text-foreground">
                New Lead Inquiry
              </p>
            </div>

            {/* Pulsing Status Dot */}
            <div
              className="w-3 h-3 rounded-full ml-6
                 animate-pulse
                 bg-amber-500 dark:bg-amber-400
                 shadow-[0_0_15px_rgba(245,158,11,0.6)] 
                 dark:shadow-[0_0_15px_rgba(251,191,36,0.6)]"
            />
          </motion.div>

          {/* Pointer bubble */}
          <div
            className="absolute left-1/2 -bottom-2.5 -translate-x-1/2 
               w-5 h-5 rounded-full 
               bg-background border-4 border-border
               shadow-xl"
          />
        </div>

        {/* Central Core */}
        <div className="relative z-10 w-full flex justify-center items-center mx-auto">
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            className="
              w-36 h-36 md:w-52 md:h-52 
              rounded-[3.5rem] 
              flex items-center justify-center 
              bg-accent 
              border-4 border-accent/20 
              overflow-hidden relative
              shadow-[0_0_80px_rgba(29,158,117,0.25)]
              dark:shadow-[0_0_90px_rgba(29,158,117,0.4)]
            "
          >
            <Image
              src="/short-logo.png"
              alt="AutomEdge Logo"
              fill
              sizes="150px"
              className="
                object-contain 
                pointer-events-none 
                select-none
                p-3 md:p-4
              "
            />
          </motion.div>
          {/* Corrected SVG ViewBox and Paths */}
          <svg
            className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[800px] pointer-events-none -z-10"
            viewBox="0 0 100 800"
            preserveAspectRatio="xMidYMid slice"
          >
            <defs>
              <linearGradient
                id="pulse-gradient"
                x1="0%"
                y1="0%"
                x2="0%"
                y2="100%"
              >
                <stop offset="0%" stopColor="transparent" />
                <stop offset="50%" stopColor="#1D9E75" />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
            </defs>

            {/* Trigger to Hub */}
            <BezierEdge d="M 50 -160 L 50 40" />

            {/* Hub to Grid (Branching) */}
            <BezierEdge d="M 50 160 Q 50 250, 25 320" delay={0.2} />
            <BezierEdge d="M 50 160 Q 50 250, 75 320" delay={0.3} />
          </svg>
        </div>
        {/* Industry Matrix */}
        <div className="w-full relative -mt-20 flex justify-center px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 md:gap-x-24 gap-y-16 md:gap-y-24 max-w-6xl mx-auto">
            {DEMOS.map((demo, index) => (
              <DemoCard key={demo.id} demo={demo} index={index} />
            ))}
          </div>
        </div>
        {/* Final Out */}
        <div className="mt-16 relative z-10 flex justify-center w-full">
          <div className="absolute left-1/2 -top-20 -translate-x-1/2 w-1 h-20 bg-linear-to-b from-accent/10 to-accent/40 -z-10" />
          <div className="px-12 py-6 rounded-4xl border border-white/10 shadow-2xl backdrop-blur-2xl flex items-center gap-6 group hover:border-accent/40 transition-all shadow-3xl">
            <Database className="w-6 h-6 text-accent animate-pulse" />
            <div className="flex flex-col gap-1 text-left">
              <span className="text-[11px] font-black uppercase tracking-[0.3em] text-accent/60 group-hover:text-accent transition-colors">
                Distributed Intelligence
              </span>
              <span className="text-lg font-bold text-foreground font-outfit">
                CRM / ERP Integration Layer
              </span>
            </div>
            <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-accent ml-4" />
          </div>
        </div>
      </div>
    </section>
  );
}
