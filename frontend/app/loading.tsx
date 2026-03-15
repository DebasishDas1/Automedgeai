import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="fixed inset-0 min-h-screen bg-background/80 backdrop-blur-sm flex flex-col items-center justify-center">
      <div className="relative flex items-center justify-center">
        {/* Outer pulsing ring */}
        <div className="absolute w-24 h-24 border-2 border-accent/20 rounded-full animate-ping shadow-[0_0_20px_rgba(0,194,168,0.2)]" />

        {/* Core spinner */}
        <div className="bg-background border border-border p-4 rounded-full shadow-2xl relative z-10 flex items-center justify-center filter drop-shadow-[0_0_15px_rgba(0,194,168,0.3)]">
          <Loader2 className="w-10 h-10 text-accent animate-spin" />
        </div>
      </div>

      <p className="mt-8 font-outfit font-bold text-lg text-foreground animate-pulse tracking-wide">
        Loading<span className="text-accent">...</span>
      </p>
    </div>
  );
}
