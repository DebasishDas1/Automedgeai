"use client";

import dynamic from "next/dynamic";
import { Zap, Check, Video } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useDomainNavigation } from "@/hook/useDomainNavigation";
import Link from "next/link";

const GLSLHills = dynamic(
  () => import("@/components/ui/glsl-hills").then((mod) => mod.GLSLHills),
  {
    ssr: false,
    loading: () => <div className="absolute inset-0 bg-background" />,
  },
);

const badges = ["14 day setup", "No long contracts", "Works with your CRM"];

export const ModernHero = () => {
  const { goTo } = useDomainNavigation();
  return (
    <section className="relative pt-24 md:pt-28 min-h-[720px] md:min-h-[880px] lg:min-h-[95vh] w-full flex flex-col items-center justify-center overflow-hidden bg-background transition-colors duration-500">
      <div className="absolute inset-0 z-0 hidden md:block">
        <GLSLHills />
      </div>
      <div className="space-y-8 z-10 text-center absolute px-6">
        <h1 className="font-semibold text-5xl md:text-7xl whitespace-pre-wrap leading-tight tracking-tighter">
          <span className="italic text-4xl md:text-6xl font-thin block mb-2 opacity-80 decoration-accent/10 underline underline-offset-8">
            Stop Losing Jobs
          </span>
          to <span className="text-accent">Slow Lead Response</span>
        </h1>
        <p className="text-lg md:text-xl text-primary/60 max-w-2xl mx-auto leading-relaxed font-medium">
          AutomEdge responds to every HVAC lead in under 60 seconds — qualifies,
          books, and follows up automatically. No extra staff.
        </p>

        <div className="flex flex-col sm:flex-row gap-5 items-center justify-center font-bold">
          <Link
            href="/demo-hvac"
            onClick={(e) => {
              e.preventDefault();
              goTo("demo-hvac");
            }}
            aria-label="See HVAC Demo Live"
            className="w-full sm:w-auto flex items-center justify-center gap-3 bg-accent text-secondary px-10 py-5 rounded-2xl font-black hover:scale-[1.05] active:scale-95 transition-all group"
          >
            <Zap className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            See it Live - Free Demo
          </Link>

          <button
            onClick={() => goTo("contact")}
            aria-label="Watch Introduction Video"
            className="w-full sm:w-auto flex items-center justify-center gap-3 px-10 py-5 rounded-2xl border-2 border-accent/30 bg-background/50 backdrop-blur-sm hover:border-accent hover:bg-accent/5 transition-all font-bold text-lg"
          >
            <Video className="w-5 h-5 text-accent" />
            Watch 3-minute Video
          </button>
        </div>

        <div className="flex gap-4 md:gap-8 flex-wrap items-center justify-center mt-4">
          {badges.map((badge) => (
            <Badge
              variant="outline"
              key={badge}
              className="flex gap-2 py-2 px-4 border-accent/20 bg-accent/5 rounded-full text-sm font-bold"
            >
              <Check className="w-4 h-4 text-accent stroke-[3px]" />
              {badge}
            </Badge>
          ))}
        </div>
      </div>
      <div
        className="
          pointer-events-none
          absolute bottom-0 left-0 w-full
          h-[100px] md:h-[140px] lg:h-[180px]
          bg-linear-to-t
          from-background
          via-background/70
          to-transparent
          backdrop-blur-[2px]
          z-20
        "
      />
    </section>
  );
};
