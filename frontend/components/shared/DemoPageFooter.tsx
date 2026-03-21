"use client";

import { ShieldCheck } from "lucide-react";

export const DemoPageFooter = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative w-full overflow-hidden">
      <div className="relative mx-auto max-w-7xl px-6 pt-12 pb-16">
        <div className="flex flex-col items-center">
          {/* Main Massive Branding - Stylized as an ambient backdrop */}
          <div className="relative mb-16 select-none pointer-events-none">
            <div className="w-full text-center text-[10vw] font-outfit font-black tracking-tighter leading-none bg-linear-to-b from-foreground/5 via-foreground/20 to-foreground/60 bg-clip-text text-transparent select-none opacity-20 transform scale-[1.1]">
              AutomEdge
            </div>
          </div>

          <div className="w-full flex flex-col lg:flex-row items-center justify-between gap-10 text-primary/60">
            <p className="text-[11px] font-bold uppercase tracking-widest mt-2 md:mt-0">
              © {currentYear} AutomEdge Intelligence.
            </p>

            <div className="flex items-center gap-3 grayscale">
              <ShieldCheck size={16} className="text-accent" />
              <span className="text-[9px] font-black uppercase tracking-[0.3em]">
                Secure Platform
              </span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
