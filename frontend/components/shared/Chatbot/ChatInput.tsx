import { m as motion } from "framer-motion";
import { Send, Sparkles } from "lucide-react";
import { RefObject } from "react";

interface ChatInputProps {
  input: string;
  isComplete: boolean;
  isTyping: boolean;
  accentColor: string;
  inputRef: RefObject<HTMLInputElement | null>;
  onInputChange: (val: string) => void;
  onSend: (val: string) => void;
}

export function ChatInput({
  input,
  isComplete,
  isTyping,
  accentColor,
  inputRef,
  onInputChange,
  onSend,
}: ChatInputProps) {
  return (
    <div className="px-6 py-5 bg-white dark:bg-slate-950 border-t border-slate-100 dark:border-white/5 shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex-1 relative group">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && onSend(input)}
            placeholder={
              isComplete ? "Session Finalized" : "Compose your message…"
            }
            disabled={isComplete}
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 focus:border-emerald-500/30 focus:ring-4 focus:ring-emerald-500/5 rounded-2xl py-4 pl-5 pr-12 text-[14px] font-medium text-slate-700 dark:text-white transition-all duration-300 outline-none disabled:opacity-50 placeholder:text-slate-400 dark:placeholder:text-slate-500"
          />
          <motion.div
            animate={{ opacity: input ? 1 : 0.4 }}
            className="absolute right-4 top-1/2 -translate-y-1/2"
          >
            <Sparkles size={16} className="text-emerald-500/60" />
          </motion.div>
        </div>
        <motion.button
          whileHover={{
            scale: 1.05,
            boxShadow: `0 10px 20px -5px ${accentColor}44`,
          }}
          whileTap={{ scale: 0.9 }}
          onClick={() => onSend(input)}
          disabled={!input.trim() || isComplete || isTyping}
          className="w-13 h-13 rounded-2xl flex items-center justify-center transition-all duration-300 disabled:opacity-30 disabled:grayscale group"
          style={{ backgroundColor: accentColor }}
        >
          <Send
            size={20}
            strokeWidth={2}
            className="text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform"
          />
        </motion.button>
      </div>
      <div className="mt-3.5 flex items-center justify-center gap-2">
        <div className="w-8 h-px bg-slate-200 dark:bg-white/10" />
        <p className="text-[9px] font-black tracking-[0.2em] uppercase text-slate-400 dark:text-slate-500">
          Automedge Intelligence
        </p>
        <div className="w-8 h-px bg-slate-200 dark:bg-white/10" />
      </div>
    </div>
  );
}
