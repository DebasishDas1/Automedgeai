"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { startChatSession, sendChatMessage } from "@/lib/api/chat";

import { Message, ChatbotProps, UserInfo } from "./types";
import { CONFIGS, uid } from "./configs";
import { Toggle } from "./Toggle";
import { Header } from "./Header";
import { LeadForm } from "./LeadForm";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";

export function Chatbot({ vertical = "general" }: ChatbotProps) {
  const cfg = CONFIGS[vertical];
  const accentColor = "#1D9E75";

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

  const apiVertical = vertical === "general" ? "hvac" : vertical;

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, isTyping, step]);

  useEffect(() => {
    if (isOpen && step === "chat" && sessionInit.current) {
      setTimeout(() => inputRef.current?.focus(), 400);
    }
  }, [isOpen, step]);

  const addBotMsg = useCallback(
    (text: string, quickReplies?: Message["quickReplies"]) => {
      setMessages((prev) => [
        ...prev,
        { id: uid(), text, sender: "bot", quickReplies },
      ]);
    },
    [],
  );

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInfo.name || !userInfo.email || !userInfo.phone) return;

    setIsSubmitting(true);
    try {
      const data = await startChatSession(apiVertical, userInfo);
      setSessionId(data.session_id);

      setTimeout(() => {
        setMessages([
          {
            id: uid(),
            text: `Terrific to meet you, ${userInfo.name.split(" ")[0]}. ${cfg.initialMessage}`,
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

  const handleSend = useCallback(
    async (text: string = input) => {
      const msg = text.trim();
      if (!msg || isComplete || isTyping) return;

      setMessages((prev) => [
        ...prev,
        { id: uid(), text: msg, sender: "user" },
      ]);
      setInput("");
      setIsTyping(true);

      try {
        if (!sessionId) {
          addBotMsg("Establishing secure connection…");
          return;
        }
        const data = await sendChatMessage(apiVertical, sessionId, msg);
        if (data.is_complete) setIsComplete(true);
        addBotMsg(
          data.message || "My apologies, an unexpected interruption occurred.",
        );
      } catch {
        addBotMsg("Connectivity disruption. Please verify your connection.");
      } finally {
        setIsTyping(false);
      }
    },
    [input, isComplete, isTyping, sessionId, apiVertical, addBotMsg],
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
                    onUserInfoChange={setUserInfo}
                    onSubmit={handleFormSubmit}
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
                      // accentColor={accentColor}
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
