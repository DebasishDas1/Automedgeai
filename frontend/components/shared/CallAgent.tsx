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

// FIX: Removed dead module-level `let RetellWebClient: any` declaration.
// It was declared but never assigned here — the real import happens inside
// the effect via dynamic import(). The stale declaration caused confusion
// and shadowed the destructured name inside initAndStartCall.

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

  // FIX: Split into two refs so handleStop can always reach the client even
  // when the effect cleanup races with an in-flight initAndStartCall.
  // `retellClientRef` holds the live client once startCall() resolves.
  // `pendingClientRef` holds the client the moment it is constructed,
  // so handleStop can abort it before startCall() returns.
  const retellClientRef = useRef<any>(null);
  const pendingClientRef = useRef<any>(null);

  useEffect(() => {
    let isCancelled = false;

    if (!open) {
      // Tear down any live or pending client when the dialog closes.
      const client = retellClientRef.current ?? pendingClientRef.current;
      client?.stopCall();
      retellClientRef.current = null;
      pendingClientRef.current = null;
      setStatus("idle");
      return;
    }

    const initAndStartCall = async () => {
      try {
        setStatus("connecting");

        const { access_token } = await createWebCall(type);
        if (isCancelled) return;

        // Lazy import to avoid SSR issues — intentional, kept as-is.
        const { RetellWebClient } = await import("retell-client-js-sdk");
        if (isCancelled) return;

        const client = new RetellWebClient();

        // FIX: Assign to pendingClientRef immediately after construction so
        // handleStop can call stopCall() even while startCall() is awaiting.
        pendingClientRef.current = client;

        client.on("call_started", () => {
          if (!isCancelled) {
            retellClientRef.current = client;
            pendingClientRef.current = null;
            setStatus("active");
          }
        });

        client.on("call_ended", () => {
          if (!isCancelled) {
            retellClientRef.current = null;
            pendingClientRef.current = null;
            setStatus("idle");
            setOpen(false);
          }
        });

        client.on("error", (err: unknown) => {
          console.error("Retell error:", err);
          if (!isCancelled) setStatus("error");
        });

        await client.startCall({ accessToken: access_token });
      } catch (err) {
        if (!isCancelled) setStatus("error");
        console.error("Failed to start call:", err);
      }
    };

    initAndStartCall();

    return () => {
      isCancelled = true;
      // Clean up whichever ref is populated at teardown time.
      const client = retellClientRef.current ?? pendingClientRef.current;
      client?.stopCall();
      retellClientRef.current = null;
      pendingClientRef.current = null;
    };
  }, [open, type]);

  const handleStop = () => {
    // FIX: Original only checked retellClientRef, which is only assigned after
    // call_started fires. If the user clicks End Call while we are still
    // awaiting startCall() (status === "connecting"), the client existed in
    // the local variable but not in the ref — stopCall() was never called,
    // leaving a zombie WebRTC session open. Now we also check pendingClientRef.
    const client = retellClientRef.current ?? pendingClientRef.current;
    client?.stopCall();
    retellClientRef.current = null;
    pendingClientRef.current = null;
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
          <m.div
            animate={{ scale: [1, 1.2], opacity: [0.1, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute inset-0 bg-white rounded-full"
          />
          <Mic size={28} className="relative z-10 text-white" />
        </m.button>
      </DialogTrigger>

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

          {(status === "active" || status === "connecting") &&
            [1, 2, 3].map((i) => (
              <m.div
                key={i}
                animate={{ scale: [1, 2.5], opacity: [0.4, 0] }}
                transition={{
                  duration: status === "active" ? 2 : 3,
                  repeat: Infinity,
                  delay: i * 0.6,
                  ease: "easeOut",
                }}
                className="absolute w-24 h-24 border border-accent/40 rounded-full"
              />
            ))}

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
