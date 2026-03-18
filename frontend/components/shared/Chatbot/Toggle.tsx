import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, X } from "lucide-react";

interface ToggleProps {
  isOpen: boolean;
  accentColor: string;
  onClick: () => void;
}

export function Toggle({ isOpen, accentColor, onClick }: ToggleProps) {
  return (
    <motion.button
      initial={{ scale: 0, opacity: 0, y: 20 }}
      animate={{ scale: 1, opacity: 1, y: 0 }}
      whileHover={{
        scale: 1.1,
        boxShadow:
          "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
      }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      className="fixed bottom-8 right-8 w-16 h-16 rounded-full shadow-lg z-50 flex items-center justify-center overflow-hidden transition-all duration-300"
      style={{
        backgroundColor: accentColor,
        background: `linear-gradient(135deg, ${accentColor} 0%, ${accentColor}dd 100%)`,
      }}
      aria-label={isOpen ? "Close Concierge" : "Open Concierge"}
    >
      <AnimatePresence mode="wait" initial={false}>
        {isOpen ? (
          <motion.div
            key="x"
            initial={{ rotate: -90, opacity: 0, scale: 0.5 }}
            animate={{ rotate: 0, opacity: 1, scale: 1 }}
            exit={{ rotate: 90, opacity: 0, scale: 0.5 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            <X size={28} className="text-white" />
          </motion.div>
        ) : (
          <motion.div
            key="msg"
            initial={{ rotate: 90, opacity: 0, scale: 0.5 }}
            animate={{ rotate: 0, opacity: 1, scale: 1 }}
            exit={{ rotate: -90, opacity: 0, scale: 0.5 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="relative"
          >
            <MessageSquare size={28} className="text-white fill-white/10" />
            <motion.span
              animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
              transition={{
                repeat: Infinity,
                duration: 2.5,
                ease: "easeInOut",
              }}
              className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-rose-500 rounded-full border-2 border-white shadow-sm"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
