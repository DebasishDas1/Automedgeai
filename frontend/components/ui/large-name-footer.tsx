"use client";

import Link from "next/link";
import { Icons } from "@/components/ui/icons";
import Image from "next/image";
import { Mail, MapPin } from "lucide-react";

const FOOTER_LINKS = {
  Solutions: [
    { label: "HVAC Automation", href: "/demo-hvac" },
    { label: "Plumbing Leads", href: "/demo-plumbing" },
    { label: "Roofing Systems", href: "/demo-roofing" },
    { label: "Pest Control", href: "/demo-pest-control" },
  ],
  Platform: [
    { label: "The Engine", href: "#the-engine" },
    { label: "How it Works", href: "#how-it-works" },
    { label: "ROI Calculator", href: "#roi" },
    { label: "Success Stories", href: "#impact" },
  ],
  Legal: [
    { label: "Privacy Policy", href: "/privacy-policy" },
    { label: "Terms of Service", href: "/tos" },
  ],
};

export function Footer() {
  return (
    <footer
      id="footer"
      className="relative pt-32 pb-12 overflow-hidden border-t border-border/40 bg-background"
    >
      {/* Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-[radial-gradient(circle_at_center,var(--tw-gradient-stops))] from-accent/5 via-transparent to-transparent -z-10" />

      <div className="container mx-auto px-6 max-w-7xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 mb-24">
          <div className="space-y-10">
            <Link
              href="/"
              className="flex items-center relative w-[200px] h-[60px] hover:opacity-80 transition-opacity"
            >
              <Image
                src="/AutomEdge-logo-light.png"
                alt="AutomEdge logo"
                fill
                sizes="200px"
                className="object-contain dark:hidden select-none"
              />
              <Image
                src="/AutomEdge-logo.png"
                alt="AutomEdge logo"
                fill
                sizes="200px"
                className="object-contain hidden dark:block select-none"
              />
            </Link>

            <p className="text-2xl text-muted-foreground font-medium max-w-sm leading-tight tracking-tight">
              Stopping job loss due to slow follow-up. We respond to every lead
              in{" "}
              <span className="text-foreground underline decoration-accent/30 decoration-4">
                under 60 seconds.
              </span>
            </p>

            <div className="flex flex-col gap-6 pt-4">
              <a 
                href="mailto:team@automedge.com"
                className="flex items-center gap-4 text-muted-foreground font-bold hover:text-accent transition-colors"
                aria-label="Send email to team@automedge.com"
              >
                <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
                  <Mail size={20} />
                </div>
                Contact Support
              </a>
              <div className="flex items-center gap-4 text-muted-foreground font-bold">
                <div className="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
                  <MapPin size={20} />
                </div>
                Austin, Texas — USA
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-12 sm:gap-8">
            {Object.entries(FOOTER_LINKS).map(([title, links]) => (
              <div key={title} className="space-y-8">
                <h3 className="font-outfit font-black uppercase tracking-[0.3em] text-xs opacity-40">
                  {title}
                </h3>
                <ul className="space-y-5">
                  {links.map((link) => (
                    <li key={link.label}>
                      <Link
                        href={link.href}
                        className="text-lg text-muted-foreground hover:text-accent font-bold transition-all hover:translate-x-1 inline-block"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Massive Brand Name (Optimized Visibility) */}
        <div className="relative w-full pt-16 mt-16 border-t border-border/10 overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-1 bg-accent/20 rounded-full" />

          <div className="flex flex-col items-center">
            {/* Main Big Lettering */}
            <div className="w-full text-center text-[10vw] font-outfit font-black tracking-tighter leading-none bg-linear-to-b from-foreground/5 via-foreground/20 to-foreground/60 bg-clip-text text-transparent select-none opacity-20 transform scale-[1.1]">
              AutomEdge
            </div>

            {/* Sub-Footer Controls */}
            <div className="w-full flex flex-col md:flex-row items-center justify-between gap-8 mt-16 text-muted-foreground font-bold text-xs uppercase tracking-[0.2em]">
              <div className="flex flex-wrap items-center justify-center md:justify-start gap-8">
                <span className="opacity-60 hover:opacity-100 transition-opacity">
                  © {new Date().getFullYear()} AutomEdge AI Inc.
                </span>
              </div>

              <div className="flex items-center gap-4 bg-muted/30 px-6 py-2 rounded-full border border-border/40">
                <div className="w-2 h-2 rounded-full bg-accent animate-pulse shadow-[0_0_10px_rgba(0,194,168,0.5)]" />
                <span className="text-[10px] font-black tracking-[0.3em]">
                  Network Live
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
