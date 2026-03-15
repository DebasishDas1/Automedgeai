import { GLSLHills } from "@/components/ui/glsl-hills";
import Link from "next/link";
import { Zap, Check, Video } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const badges = ["14 day setup", "No long contracts", "Works with your CRM"];

export const ModernHero = () => {
  return (
    <div className="relative flex h-full w-full flex-col items-center justify-center overflow-hidden ">
      <GLSLHills />
      <div className="space-y-6 pointer-events-none z-10 text-center absolute">
        <h1 className="font-semibold text-7xl whitespace-pre-wrap">
          <span className="italic text-6xl font-thin">
            Stop Losing Jobs <br />
          </span>
          to Slow Follow-Up
        </h1>
        <p className="text-sm text-primary/60">
          AutomEdge responds to every HVAC lead in under 60 seconds — qualifies,
          <br />
          books, and follows up automatically. No extra staff.
        </p>
        <div className="flex gap-4 flex-wrap items-center justify-center">
          <Link href="/hvac">
            <button className="flex items-center gap-2 bg-[#00C2A8] text-[#0D1B2A] px-7 py-4 rounded-xl font-bold hover:scale-[1.03] transition">
              <Zap className="w-4 h-4" />
              See it Live - Free Demo
            </button>
          </Link>

          <Link href="#contact">
            <button className="flex items-center gap-2 px-7 py-4 rounded-xl border border-[#00C2A8]">
              <Video className="w-4 h-4 text-[#00C2A8]" />
              Watch 3-minute Video
            </button>
          </Link>
        </div>

        <div className="flex gap-6 flex-wrap items-center justify-center">
          {badges.map((badge) => (
            <Badge variant="outline" key={badge} className="flax gap-2">
              <Check data-icon="inline-start" className="text-accent" />
              {badge}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
};
