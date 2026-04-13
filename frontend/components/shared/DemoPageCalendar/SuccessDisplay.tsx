"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Video } from "lucide-react";
import { format } from "date-fns";
import { Button } from "@/components/ui/button";

type SuccessDisplayProps = {
  formData: { name: string; email: string; website: string; teamSize: string };
  selectedSlot: Date | null;
  onReschedule: () => void;
};

export const SuccessDisplay = ({
  formData,
  selectedSlot,
  onReschedule,
}: SuccessDisplayProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="py-24 px-10 flex flex-col items-center justify-center text-center bg-accent/5"
    >
      <div className="w-28 h-28 rounded-full bg-green-500/10 flex items-center justify-center mb-10 shadow-inner ring-4 ring-green-500/5">
        <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center animate-pulse">
          <CheckCircle2 className="w-10 h-10 text-green-500" />
        </div>
      </div>
      <h3 className="text-4xl md:text-5xl font-outfit font-black text-foreground mb-6 tracking-tight">
        You&apos;re all set!
      </h3>
      <p className="text-xl md:text-2xl text-muted-foreground max-w-lg mb-12 leading-relaxed font-medium">
        Thanks,{" "}
        <span className="text-foreground font-black">{formData.name}</span>!{" "}
        <br className="hidden sm:block" />
        We&apos;ve sent a calendar invite to{" "}
        <span className="text-accent underline decoration-4 underline-offset-4">
          {formData.email}
        </span>{" "}
        for{" "}
        <span className="font-black text-foreground italic">
          {selectedSlot ? format(selectedSlot, "MMMM do 'at' h:mm a") : ""}
        </span>
        .
      </p>
      <div className="flex flex-col sm:flex-row gap-6 w-full max-w-md">
        <Button
          variant="outline"
          className="flex-1 h-16 rounded-2xl font-black border-2 border-border/60 text-lg hover:text-cta transition-all active:scale-95"
          onClick={onReschedule}
        >
          Reschedule
        </Button>
      </div>
    </motion.div>
  );
};
