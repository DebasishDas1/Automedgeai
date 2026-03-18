import { AnimatePresence, motion } from "framer-motion";
import { Message } from "./types";
import { RefObject, memo } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface MessageListProps {
  messages: Message[];
  isTyping: boolean;
  scrollRef: RefObject<HTMLDivElement | null>;
  onQuickReply: (text: string) => void;
}

// ─── Message Bubble ─────────────────────────
const MessageBubble = memo(({ msg, isLast, isTyping }: any) => {
  const isUser = msg.sender === "user";

  const shouldAnimate = !isUser && isLast && isTyping;

  return (
    <motion.div
      key={msg.id + (shouldAnimate ? "-typing" : "")} // 🔥 force re-trigger
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn("flex", isUser ? "justify-end" : "justify-start")}
    >
      <motion.div
        className={cn(
          "max-w-[75%] px-4 py-3 rounded-lg text-[14px] leading-relaxed text-black dark:text-white",
          isUser ? "bg-accent/60" : "",
        )}
        animate={shouldAnimate ? { opacity: [0.5, 1, 0.5] } : { opacity: 1 }}
        transition={
          shouldAnimate
            ? { duration: 1, repeat: Infinity, ease: "easeInOut" }
            : {}
        }
      >
        {msg.text}
      </motion.div>
    </motion.div>
  );
});

// ─── Quick Replies ─────────────────────────
const QuickReplies = memo(({ replies, onQuickReply }: any) => {
  if (!replies?.length) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {replies.map((r: any) => (
        <Button
          key={r.id}
          onClick={() => onQuickReply(r.text)}
          className="hover:dark:bg-accent hover:dark:text-black bg-accent/20 text-black dark:text-white"
        >
          {r.text}
        </Button>
      ))}
    </div>
  );
});

// ─── Typing Indicator ───────────────────────
const TypingIndicator = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="flex justify-start"
  >
    <div className="px-4 py-2 flex gap-1.5 items-center">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="w-2 h-2 rounded-full bg-(--accent)"
          animate={{
            y: [0, -6, 0],
            opacity: [0.3, 1, 0.3],
          }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * 0.2,
          }}
        />
      ))}
    </div>
  </motion.div>
);

// ─── Main Component ─────────────────────────
export function MessageList({
  messages,
  isTyping,
  scrollRef,
  onQuickReply,
}: MessageListProps) {
  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
      <AnimatePresence initial={false}>
        {messages.map((msg, i) => (
          <div key={msg.id} className="space-y-2">
            <MessageBubble
              msg={msg}
              isLast={i === messages.length - 1}
              isTyping={isTyping}
            />
            <QuickReplies
              replies={msg.quickReplies}
              onQuickReply={onQuickReply}
            />
          </div>
        ))}
      </AnimatePresence>

      {/* Typing Indicator */}
      <AnimatePresence>
        {isTyping && (
          <motion.div
            key="typing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <TypingIndicator />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
