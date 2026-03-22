"use client";

import { m as motion } from "framer-motion";
import {
  Timer,
  ArrowUpCircle,
  XCircle,
  Users2,
  Clock3,
  TrendingUp,
} from "lucide-react";

const IMPACTS = [
  {
    icon: <Timer className="w-8 h-8 text-accent" />,
    stat: "2–3x",
    label: "Faster Response Time",
  },
  {
    icon: <ArrowUpCircle className="w-8 h-8 text-accent" />,
    stat: "30–50%",
    label: "More Booked Appointments",
  },
  {
    icon: <XCircle className="w-8 h-8 text-accent" />,
    stat: "0",
    label: "Zero Missed Leads",
  },
  {
    icon: <Users2 className="w-8 h-8 text-accent" />,
    stat: "40%",
    label: "Reduced Staff Load",
  },
  {
    icon: <Clock3 className="w-8 h-8 text-accent" />,
    stat: "24/7",
    label: "Availability",
  },
  {
    icon: <TrendingUp className="w-8 h-8 text-accent" />,
    stat: "85%",
    label: "Higher Conversion Rate",
  },
];

export function ImpactSection() {
  return (
    <section
      id="impact"
      className="py-24 px-6 border-y border-border/10 scroll-mt-24"
    >
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-5xl md:text-7xl font-outfit font-extrabold tracking-tighter"
          >
            What This Means For Your Business
          </motion.h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-y-16 gap-x-8">
          {IMPACTS.map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="text-center group flex flex-col items-center"
            >
              <div className="flex justify-center mb-8">
                <div className="p-6 rounded-full border-2 border-accent/20 group-hover:bg-accent/5 transition-all duration-300 group-hover:scale-110 shadow-lg [&_svg]:w-10 [&_svg]:h-10">
                  {item.icon}
                </div>
              </div>
              <div className="text-6xl md:text-8xl font-outfit font-black mb-4 tracking-tighter">
                {item.stat}
              </div>
              <div className="text-muted-foreground font-sans font-bold uppercase tracking-[0.2em] text-sm md:text-base">
                {item.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
