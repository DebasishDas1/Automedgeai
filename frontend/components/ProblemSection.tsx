"use client";

import { m as motion } from "framer-motion";
import {
  Clock,
  MessageSquareOff,
  EyeOff,
  UserX,
  Users,
  TrendingDown,
} from "lucide-react";

const PROBLEMS = [
  {
    icon: <Clock className="w-8 h-8" />,
    text: "Slow follow-ups costing you deals",
    desc: "78% of customers buy from the first business that responds.",
  },
  {
    icon: <MessageSquareOff className="w-8 h-8" />,
    text: "Missed WhatsApp inquiries",
    desc: "Every unseen text is a customer calling your competitor instead.",
  },
  {
    icon: <EyeOff className="w-8 h-8" />,
    text: "Zero pipeline visibility",
    desc: "If you don't know your lead source, you're lighting money on fire.",
  },
  {
    icon: <UserX className="w-8 h-8" />,
    text: "Receptionists miss callbacks",
    desc: "Busy teams forget to call back. AI never takes a lunch break.",
  },
  {
    icon: <Users className="w-8 h-8" />,
    text: "Losing to local competitors",
    desc: "Speed to lead is the only competitive advantage that still works.",
  },
  {
    icon: <TrendingDown className="w-8 h-8" />,
    text: "No structured nurturing",
    desc: "Most leads need 5+ touches. Most businesses only give one.",
  },
];

export function ProblemSection() {
  return (
    <section id="problem" className="py-32 px-6 max-w-7xl mx-auto scroll-mt-24">
      <div className="text-center mb-24 space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="inline-flex items-center gap-2 px-6 py-2 rounded-full border border-destructive/20 bg-destructive/5 text-destructive font-black text-xs uppercase tracking-[0.2em]"
        >
          The Problem
        </motion.div>

        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-5xl md:text-8xl font-outfit font-black tracking-tighter leading-[0.9] max-w-5xl mx-auto"
        >
          Leads go cold in
          <span className="text-accent underline decoration-accent/20 decoration-8 underline-offset-8">
            5 minutes.
          </span>
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="text-xl md:text-3xl text-muted-foreground font-bold tracking-tight max-w-2xl mx-auto leading-tight"
        >
          Most service businesses lose{" "}
          <span className="text-foreground underline decoration-destructive/30 decoration-4 underline-offset-4">
            30–60%
          </span>{" "}
          of their leads to friction and slow responses.
        </motion.p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative">
        {PROBLEMS.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -8 }}
            className="relative group p-10 rounded-[2.5rem] border-border/50 bg-card/40 backdrop-blur-xl hover:border-accent/40 transition-all duration-500 shadow-sm hover:shadow-2xl flex flex-col items-center text-center"
          >
            <div className="mb-8 w-20 h-20 rounded-2xl flex items-center justify-center bg-primary/10 transition-all shadow-inner [&_svg]:w-10 [&_svg]:h-10">
              {item.icon}
            </div>

            <div className="space-y-4">
              <h3 className="text-2xl font-outfit font-black leading-tight tracking-tight">
                {item.text}
              </h3>
              <p className="text-muted-foreground leading-relaxed font-medium opacity-80 group-hover:opacity-100 transition-opacity">
                {item.desc}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
