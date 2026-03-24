"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Mic } from "lucide-react";
import { Button } from "@/components/ui/button";
import { m } from "framer-motion";
import { useState, useEffect, useRef } from "react";

type CallAgentProp = {
  type:
    | "hvac"
    | "plumbing"
    | "roofing"
    | "landscaping"
    | "painting"
    | "pest_control";
};

export const CallAgent = ({ type }: CallAgentProp) => {
  const [open, setOpen] = useState(false);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    const requestMic = async () => {
      if (open) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            audio: true,
          });
          streamRef.current = stream;
        } catch (err) {
          console.error("Microphone access denied:", err);
        }
      } else {
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }
      }
    };

    requestMic();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <m.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="
            fixed bottom-28 right-8 
            w-16 h-16 rounded-full 
            flex items-center justify-center
            bg-accent text-white
            shadow-[0_12px_40px_rgba(0,0,0,0.35)]
            z-50
          "
        >
          {/* Subtle pulse for mobile attention */}
          <m.div
            animate={{ scale: [1, 1.2], opacity: [0.1, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute inset-0 bg-white rounded-full"
          />
          <Mic size={28} className="relative z-10 text-white" />
        </m.button>
      </DialogTrigger>

      {/* Responsive Dialog */}
      <DialogContent
        className="
          w-[calc(100%-2.5rem)] sm:max-w-md 
          h-auto min-h-[380px] sm:min-h-[420px] 
          rounded-[32px] sm:rounded-[40px] 
          border border-white/10 
          backdrop-blur-3xl bg-background/80
          shadow-[0_40px_100px_-20px_rgba(0,0,0,0.55)]
          flex flex-col items-center justify-between
          py-12 px-8
        "
        showCloseButton={false}
      >
        <DialogHeader className="text-center w-full">
          <DialogTitle className="text-3xl sm:text-4xl font-bold tracking-tight text-center">
            Let's talk
          </DialogTitle>
        </DialogHeader>

        {/* Center Mic Visualizer - Simplified & Refined for Mobile */}
        <div className="relative flex items-center justify-center flex-1 w-full my-8">
          {/* Ambient Glow */}
          <m.div
            animate={{
              scale: [1, 1.15, 1],
              opacity: [0.2, 0.35, 0.2],
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="absolute w-40 h-40 bg-accent/20 rounded-full blur-[60px]"
          />

          {/* Staggered Ripples */}
          {[1, 2].map((i) => (
            <m.div
              key={i}
              animate={{
                scale: [1, 2.2],
                opacity: [0.3, 0],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                delay: i * 1,
                ease: "easeOut",
              }}
              className="absolute w-24 h-24 border border-accent/30 rounded-full"
            />
          ))}

          {/* Core Icon Container */}
          <m.div
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="relative z-10 w-20 h-20 rounded-full bg-accent flex items-center justify-center shadow-xl shadow-accent/20"
          >
            <Mic size={38} className="text-white drop-shadow-md" />
          </m.div>
        </div>

        <Button
          onClick={() => setOpen(false)}
          className="
              rounded-2xl h-14 text-lg font-semibold w-full
              shadow-lg shadow-accent/20 transition-all active:scale-95
            "
        >
          Stop Agent
        </Button>
      </DialogContent>
    </Dialog>
  );
};
