import { X, Bot } from "lucide-react";

interface HeaderProps {
  title: string;
  accentColor: string;
  onClose: () => void;
}

export function Header({ title, accentColor, onClose }: HeaderProps) {
  return (
    <div
      className="px-6 py-5 flex items-center justify-between shrink-0 relative overflow-hidden"
      style={{
        background: `linear-gradient(135deg, ${accentColor} 0%, #0F2A47 100%)`,
      }}
    >
      {/* Ambient glow */}
      <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(circle_at_20%_30%,#ffffff_0%,transparent_50%),radial-gradient(circle_at_80%_70%,#ffffff_0%,transparent_50%)]" />

      <div className="flex items-center gap-4 text-white min-w-0 relative z-10">
        {/* Icon container */}
        <div className="w-12 h-12 bg-white/10 backdrop-blur-md rounded-2xl flex items-center justify-center shrink-0 border border-white/20 shadow-lg">
          <Bot size={26} strokeWidth={2} className="drop-shadow-sm" />
        </div>

        {/* Title + status */}
        <div className="min-w-0">
          <p className="font-extrabold text-[16px] leading-none tracking-tight uppercase truncate">
            {title}
          </p>

          <div className="flex items-center gap-2 mt-1.5">
            {/* Premium subtle indicator */}
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60 blur-[2px]"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>

            <span className="text-[10px] text-white/80 font-bold tracking-widest uppercase">
              Platinum Status
            </span>
          </div>
        </div>
      </div>

      {/* Close button */}
      <button
        onClick={onClose}
        className="text-white/70 hover:text-white transition-all p-2 rounded-xl hover:bg-white/10 backdrop-blur-md"
      >
        <X size={20} />
      </button>
    </div>
  );
}
