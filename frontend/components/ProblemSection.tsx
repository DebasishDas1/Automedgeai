"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
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
    icon: <Clock className="w-6 h-6" />,
    text: "Slow follow-ups costing you deals",
  },
  {
    icon: <MessageSquareOff className="w-6 h-6" />,
    text: "Missed WhatsApp and website inquiries",
  },
  {
    icon: <EyeOff className="w-6 h-6" />,
    text: "No lead tracking or pipeline visibility",
  },
  {
    icon: <UserX className="w-6 h-6" />,
    text: "Receptionists forgetting callbacks",
  },
  {
    icon: <Users className="w-6 h-6" />,
    text: "Leads contacting competitors first",
  },
  {
    icon: <TrendingDown className="w-6 h-6" />,
    text: "No structured nurturing system",
  },
];

export function ProblemSection() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <section id="problem" className="py-24 px-6 max-w-7xl mx-auto scroll-mt-24">
      <div className="text-center mb-20">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-7xl font-outfit font-[800] leading-tight mb-6 tracking-tighter"
        >
          Leads go cold when you don't respond
          <br className="hidden md:block" />
          within 5 minutes.
        </motion.h2>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-2xl md:text-3xl text-accent font-extrabold tracking-tight"
        >
          Most Service Businesses Lose 30–60% of Leads.
        </motion.p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 relative">
        {PROBLEMS.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -10, scale: 1.02 }}
            className="p-10 rounded-[2.5rem] border-2 border-border/50 bg-card hover:border-accent/60 transition-all group shadow-sm hover:shadow-2xl hover:shadow-accent/10 flex flex-col items-center text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-8 text-foreground group-hover:bg-accent group-hover:text-accent-foreground transition-all duration-300 group-hover:rotate-6 shadow-lg [&_svg]:w-8 [&_svg]:h-8">
              {item.icon}
            </div>

            <p className="text-xl font-bold leading-tight tracking-tight max-w-[250px]">
              {item.text}
            </p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
