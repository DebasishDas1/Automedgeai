"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Mic, PhoneOff, PhoneCall, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { m } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { createWebCall } from "@/lib/api/retell";

// Lazy load Retell SDK to avoid SSR issues
let RetellWebClient: any;

type CallAgentProp = {
  type:
    | "hvac"
    | "plumbing"
    | "roofing"
    | "landscaping"
    | "painting"
    | "pest_control";
};

type CallStatus = "idle" | "connecting" | "active" | "error";

export const CallAgent = ({ type }: CallAgentProp) => {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<CallStatus>("idle");
  const retellClientRef = useRef<any>(null);

  useEffect(() => {
    let isCancelled = false;
    let localClient: any = null;

    if (!open) {
      if (retellClientRef.current) {
        retellClientRef.current.stopCall();
        retellClientRef.current = null;
      }
      setStatus("idle");
      return;
    }

    const initAndStartCall = async () => {
      try {
        setStatus("connecting");
        
        const { access_token } = await createWebCall(type);
        if (isCancelled) return;

        const { RetellWebClient } = await import("retell-client-js-sdk");
        if (isCancelled) return;
        
        localClient = new RetellWebClient();
        retellClientRef.current = localClient;

        localClient.on("call_started", () => {
          if (!isCancelled) setStatus("active");
        });

        localClient.on("call_ended", () => {
          if (!isCancelled) {
            setStatus("idle");
            setOpen(false);
          }
        });

        localClient.on("error", (err: any) => {
          console.error("Retell error:", err);
          if (!isCancelled) setStatus("error");
        });

        await localClient.startCall({ accessToken: access_token });

      } catch (err) {
        if (!isCancelled) setStatus("error");
        console.error("Failed to start call:", err);
      }
    };

    initAndStartCall();

    return () => {
      isCancelled = true;
      if (localClient) {
        localClient.stopCall();
      }
      if (retellClientRef.current === localClient) {
        retellClientRef.current = null;
      }
    };
  }, [open, type]);

  const handleStop = () => {
    if (retellClientRef.current) {
      retellClientRef.current.stopCall();
      retellClientRef.current = null;
    }
    setOpen(false);
  };

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
            {status === "connecting"
              ? "Initializing..."
              : status === "active"
                ? "AI Agent Live"
                : status === "error"
                  ? "Connection Failed"
                  : "Let's talk"}
          </DialogTitle>
          <p className="text-muted-foreground mt-2">
            {status === "active"
              ? "Connected and listening..."
              : status === "connecting"
                ? "Setting up your secure line."
                : status === "error"
                  ? "Please check your mic and try again."
                  : "Our AI agent is ready to help you."}
          </p>
        </DialogHeader>

        {/* Center Mic Visualizer */}
        <div className="relative flex items-center justify-center flex-1 w-full my-8">
          {/* Ambient Glow */}
          <m.div
            animate={{
              scale: status === "active" ? [1, 1.3, 1] : [1, 1.15, 1],
              opacity: status === "active" ? [0.3, 0.6, 0.3] : [0.2, 0.35, 0.2],
            }}
            transition={{
              duration: status === "active" ? 2 : 4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className={`absolute w-40 h-40 ${status === "error" ? "bg-destructive/20" : "bg-accent/20"} rounded-full blur-[60px]`}
          />

          {/* Staggered Ripples */}
          {(status === "active" || status === "connecting") &&
            [1, 2, 3].map((i) => (
              <m.div
                key={i}
                animate={{
                  scale: [1, 2.5],
                  opacity: [0.4, 0],
                }}
                transition={{
                  duration: status === "active" ? 2 : 3,
                  repeat: Infinity,
                  delay: i * 0.6,
                  ease: "easeOut",
                }}
                className="absolute w-24 h-24 border border-accent/40 rounded-full"
              />
            ))}

          {/* Core Icon Container */}
          <m.div
            animate={
              status === "active"
                ? { scale: [1, 1.1, 1] }
                : { scale: [1, 1.05, 1] }
            }
            transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
            className={`
              relative z-10 w-24 h-24 rounded-full 
              ${status === "error" ? "bg-destructive" : "bg-accent"} 
              flex items-center justify-center 
              shadow-2xl shadow-accent/40
            `}
          >
            {status === "connecting" ? (
              <Loader2 size={42} className="text-white animate-spin" />
            ) : status === "active" ? (
              <PhoneCall size={42} className="text-white animate-pulse" />
            ) : status === "error" ? (
              <Mic size={42} className="text-white opacity-50" />
            ) : (
              <Mic size={42} className="text-white" />
            )}
          </m.div>
        </div>

        <div className="flex flex-col gap-3 w-full">
          <Button
            onClick={handleStop}
            disabled={status === "connecting"}
            variant={status === "error" ? "outline" : "default"}
            className="
                rounded-2xl h-14 text-lg font-semibold w-full
                shadow-lg shadow-accent/20 transition-all active:scale-95
                flex items-center justify-center gap-2
              "
          >
            {status === "active" ? (
              <>
                <PhoneOff size={20} />
                End Call
              </>
            ) : status === "error" ? (
              "Try Again"
            ) : status === "connecting" ? (
              "Connecting..."
            ) : (
              "Stop Agent"
            )}
          </Button>

          {status === "active" && (
            <p className="text-[10px] text-center text-muted-foreground uppercase tracking-widest">
              Secure encrypted web call
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
