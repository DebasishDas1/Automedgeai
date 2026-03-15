"use client";

import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";

const steps = [
  {
    number: "1",
    title: "Lead comes in",
    description: "Web form, phone call, or ad click — any source",
  },
  {
    number: "2",
    title: "AI responds in 60s",
    description: "Texts them, qualifies issue, checks urgency",
  },
  {
    number: "3",
    title: "Job booked",
    description: "Appointment in your calendar. Done.",
  },
];

export const HowItWorks = () => {
  return (
    <section className="px-6" id="how-it-works">
      <div className="text-center mb-20">
        <motion.h2
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-5xl md:text-7xl font-outfit font-[800] leading-tight mb-6 tracking-tighter"
        >
          From lead to booked job — automatically.
        </motion.h2>
      </div>

      <Card className="relative max-w-5xl mx-auto shadow-lg p-12 rounded-3xl border-none">
        <CardContent className="relative">
          {/* connecting line */}
          <div className="hidden md:block absolute top-8 left-16 right-16 h-[2px] bg-border z-0" />

          <div className="grid md:grid-cols-3 gap-10 relative z-10">
            {steps.map((step) => (
              <div
                key={step.number}
                className="flex flex-col items-center text-center"
              >
                {/* number circle */}
                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-accent text-accent-foreground font-bold text-xl mb-4">
                  {step.number}
                </div>

                <h3 className="font-semibold text-lg mb-2">{step.title}</h3>

                <p className="text-muted-foreground text-sm">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </section>
  );
};
