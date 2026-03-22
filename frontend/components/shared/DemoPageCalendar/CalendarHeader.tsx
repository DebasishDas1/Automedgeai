"use client";

import { m as motion } from "framer-motion";
import { Calendar as CalendarIcon } from "lucide-react";

type CalendarHeaderProps = {
  title: string;
  highlight: string;
  description?: string;
};

export const CalendarHeader = ({ title, highlight, description }: CalendarHeaderProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="text-center mb-16 max-w-3xl mx-auto flex flex-col items-center"
    >
      <div className="flex items-center justify-center gap-2 mb-4">
        <CalendarIcon className="w-5 h-5 text-accent" />
        <span className="label text-accent uppercase tracking-widest font-bold text-[10px] sm:text-xs">
          Book a Live Demo
        </span>
      </div>

      <h2 className="text-4xl md:text-5xl font-outfit tracking-tight leading-tight mb-4 text-foreground">
        {title} <span className="text-accent">{highlight}</span>
      </h2>

      {description && (
        <p className="text-lg text-muted-foreground opacity-90 max-w-2xl mx-auto leading-relaxed">
          {description}
        </p>
      )}
    </motion.div>
  );
};
