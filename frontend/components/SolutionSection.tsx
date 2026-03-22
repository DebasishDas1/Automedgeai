"use client";

import { m as motion } from "framer-motion";
import {
  Sparkles,
  Target,
  Zap,
  Repeat,
  CalendarCheck,
  BarChart3,
} from "lucide-react";

const SOLUTIONS = [
  {
    icon: <Sparkles className="w-6 h-6" />,
    title: "AI Lead Capture",
    description: "Instantly grab leads from every channel, 24/7.",
  },
  {
    icon: <Target className="w-6 h-6" />,
    title: "AI Qualification",
    description: "Automated triage to identify high-intent prospects.",
  },
  {
    icon: <Repeat className="w-6 h-6" />,
    title: "AI Nurturing",
    description: "Keep leads warm with intelligent, multi-step conversation.",
  },
  {
    icon: <Zap className="w-6 h-6" />,
    title: "AI Follow-up",
    description: "Reach back out to cold leads without lifting a finger.",
  },
  {
    icon: <CalendarCheck className="w-6 h-6" />,
    title: "AI Booking",
    description:
      "Seamlessly integrate with your calendar to book appointments.",
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: "AI Analytics",
    description: "Deep insights into your pipeline and conversion rates.",
  },
];

export function SolutionSection() {
  return (
    <section id="solution" className="py-24 px-6 bg-muted/30 scroll-mt-24">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-6 py-2 rounded-full border border-primary/20 bg-primary/5 text-primary font-black text-xs uppercase tracking-[0.2em]"
          >
            The Solution
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="text-5xl md:text-7xl font-outfit font-extrabold leading-tight mb-6 tracking-tighter mt-6"
          >
            Automedge AI: Your 24/7 <br className="hidden md:block" />
            <span className="text-accent underline decoration-accent/20 decoration-8 underline-offset-8">
              AI Sales System
            </span>
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-2xl md:text-3xl text-muted-foreground font-bold tracking-tight"
          >
            Your Complete AI Sales Engine — Built For You
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12 relative">
          <div className="absolute inset-0 -z-10 opacity-[0.08] pointer-events-none">
            <Sparkles className="absolute top-0 right-0 w-48 h-48 animate-pulse" />
            <Zap className="absolute bottom-0 left-0 w-32 h-32 rotate-45" />
          </div>
          {SOLUTIONS.map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1, duration: 0.6 }}
              whileHover={{ scale: 1.05, y: -5 }}
              className="relative group p-10 rounded-[2.5rem] border-border/50 bg-card/40 backdrop-blur-xl hover:border-accent/40 transition-all duration-500 shadow-sm hover:shadow-2xl flex flex-col items-center text-center"
            >
              <div className="mb-8 w-20 h-20 rounded-2xl bg-accent/10 flex items-center justify-center text-accent group-hover:bg-accent group-hover:text-accent-foreground transition-all shadow-inner [&_svg]:w-10 [&_svg]:h-10">
                {item.icon}
              </div>
              <div className="space-y-4">
                <h3 className="text-3xl font-outfit font-black leading-tight tracking-tight">
                  {item.title}
                </h3>
                <p className="text-muted-foreground leading-relaxed font-medium opacity-80 group-hover:opacity-100 transition-opacity">
                  {item.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
