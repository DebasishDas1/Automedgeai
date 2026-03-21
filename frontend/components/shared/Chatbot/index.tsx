"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { startChatSession, sendChatMessage } from "@/lib/api/chat";
import { toast } from "sonner";

import { Message, ChatbotProps, UserInfo } from "./types";
import { CONFIGS, uid } from "./configs";
import { Toggle } from "./Toggle";
import { Header } from "./Header";
import { LeadForm } from "./LeadForm";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { ShieldCheck } from "lucide-react";

export function Chatbot({ vertical = "general" }: ChatbotProps) {
  const cfg = CONFIGS[vertical];
  const accentColor = "#1D9E75";
  const apiVertical = vertical === "general" ? "hvac" : vertical;

  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState<"form" | "chat">("form");
  const [userInfo, setUserInfo] = useState<UserInfo>({
    name: "",
    email: "",
    phone: "",
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sessionInit = useRef(false);

  // ── THE CORE FIX ──────────────────────────────────────────────────────────
  const sessionIdRef = useRef<string | null>(null);

  // Keep ref in sync with state (state drives UI reactivity, ref drives logic)
  const setSession = (id: string) => {
    setSessionId(id);
    sessionIdRef.current = id;
  };

  // ── Auto-scroll ────────────────────────────────────────────────────────────
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, isTyping, step]);

  // ── Focus input when chat opens ────────────────────────────────────────────
  useEffect(() => {
    if (isOpen && step === "chat" && sessionInit.current) {
      setTimeout(() => inputRef.current?.focus(), 400);
    }
  }, [isOpen, step]);

  // ── addBotMsg ──────────────────────────────────────────────────────────────
  const addBotMsg = useCallback(
    (text: string, quickReplies?: Message["quickReplies"]) => {
      setMessages((prev) => [
        ...prev,
        { id: uid(), text, sender: "bot", quickReplies },
      ]);
    },
    [],
  );

  // ── Form submit ────────────────────────────────────────────────────────────
  const handleFormSubmit = async (data: UserInfo) => {
    setUserInfo(data);
    setIsSubmitting(true);
    try {
      const resp = await startChatSession(apiVertical, data);
      setSession(resp.session_id);

      setTimeout(() => {
        setMessages([
          {
            id: uid(),
            text: `Hi ${data.name.split(" ")[0]}! ${cfg.initialMessage}`,
            sender: "bot",
            quickReplies: cfg.quickReplies,
          },
        ]);
        setStep("chat");
        sessionInit.current = true;
        setIsSubmitting(false);
      }, 400);
    } catch (err) {
      console.error("Failed to start session:", err);
      setIsSubmitting(false);
    }
  };

  // ── Reset Chat ─────────────────────────────────────────────────────────────
  const resetChat = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    sessionIdRef.current = null;
    isTypingRef.current = false;
    isCompleteRef.current = false;
    setUserInfo({ name: "", email: "", phone: "" });
    setStep("form");
    setIsComplete(false);
    sessionInit.current = false;
  }, []);

  // ── Send message ───────────────────────────────────────────────────────────
  const isTypingRef = useRef(false);
  const isCompleteRef = useRef(false);

  const handleSend = useCallback(
    async (textOverride?: string) => {
      const msg = (textOverride ?? "").trim();

      if (!msg) return;
      if (isCompleteRef.current || isTypingRef.current) return;

      // 🧠 optimistic UI
      setMessages((prev) => [
        ...prev,
        { id: uid(), text: msg, sender: "user" },
      ]);
      
      // Clear input state
      setInput("");

      setIsTyping(true);
      isTypingRef.current = true;

      try {
        const currentSessionId = sessionIdRef.current;

        if (!currentSessionId) {
          addBotMsg("Session still warming up… give it a second.");
          return;
        }

        const data = await sendChatMessage(apiVertical, currentSessionId, msg);

        if (data?.is_complete) {
          setIsComplete(true);
          isCompleteRef.current = true;

          // Transition to direct alert/success state
          setIsOpen(false);
          
          toast.success("Request Processed!", {
            description: "Your inquiry has been successfully received by our team.",
            duration: 6000,
            icon: <ShieldCheck className="w-5 h-5 text-emerald-500" />,
            className: "bg-white dark:bg-slate-900 border-2 border-emerald-500/20 rounded-2xl shadow-xl",
          });

          resetChat();
          return;
        }

        addBotMsg(
          data?.message || "Something slipped through the wires. Try again?",
        );
      } catch (err: any) {
        // 🌐 smarter error UX
        if (err?.status === 408) {
          addBotMsg("Server is waking up… try again in a moment.");
        } else if (err?.status === 404) {
          addBotMsg("Session expired. Refresh and start again.");
        } else {
          addBotMsg("Network hiccup. Check connection and retry.");
        }

        console.error("send error:", err);
      } finally {
        setIsTyping(false);
        isTypingRef.current = false;
      }
    },
    [apiVertical, addBotMsg, resetChat],
  );

  return (
    <>
      <Toggle
        isOpen={isOpen}
        accentColor={accentColor}
        onClick={() => setIsOpen((o) => !o)}
      />

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            className="fixed bottom-28 right-8 w-[calc(100vw-64px)] sm:w-[410px] h-[640px] max-h-[calc(100vh-140px)] rounded-[32px] shadow-[0_32px_80px_-16px_rgba(0,0,0,0.5)] z-50 flex flex-col overflow-hidden border border-slate-200 dark:border-white/10 bg-white dark:bg-slate-950"
          >
            <Header
              title={cfg.title}
              accentColor={accentColor}
              onClose={() => setIsOpen(false)}
            />

            <div className="flex-1 flex flex-col overflow-hidden relative">
              {/* Background Pattern */}
              <div
                className="absolute inset-0 pointer-events-none opacity-[0.03] dark:opacity-[0.05]"
                style={{
                  backgroundImage: `radial-gradient(${accentColor} 0.5px, transparent 0.5px)`,
                  backgroundSize: "24px 24px",
                }}
              />

              <AnimatePresence mode="wait">
                {step === "form" ? (
                  <LeadForm
                    userInfo={userInfo}
                    isSubmitting={isSubmitting}
                    accentColor={accentColor}
                    onFormComplete={handleFormSubmit}
                  />
                ) : (
                  <motion.div
                    key="chat"
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex-1 flex flex-col overflow-hidden"
                  >
                    <MessageList
                      messages={messages}
                      isTyping={isTyping}
                      scrollRef={scrollRef}
                      onQuickReply={handleSend}
                    />

                    <ChatInput
                      input={input}
                      isComplete={isComplete}
                      isTyping={isTyping}
                      accentColor={accentColor}
                      inputRef={inputRef}
                      onInputChange={setInput}
                      onSend={handleSend}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default Chatbot;
