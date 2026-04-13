"use client";

import HeroSection from "@/components/ui/hero-section-9";
import { Users, Briefcase, Link as LinkIcon } from "lucide-react";

export const ClinicHero = () => {
  const heroData = {
    title: (
      <>
        Never Miss a Patient Again <br /> Even After Clinic Hours
      </>
    ),
    subtitle:
      "Automatically capture calls, WhatsApp inquiries, and website leads — and turn them into booked appointments without adding more staff.",
    actions: [
      {
        text: "Book a Demo",
        onClick: () => {
          const el = document.getElementById("calendar");
          el?.scrollIntoView({ behavior: "smooth" });
        },
        variant: "default" as const,
      },
      {
        text: "Direct Contact",
        onClick: () => {
          const el = document.getElementById("direct-contact");
          el?.scrollIntoView({ behavior: "smooth" });
        },
        variant: "outline" as const,
      },
    ],
    stats: [
      {
        value: "24/7",
        label: "Lead Response",
        icon: <Users className="h-5 w-5 text-primary" />,
      },
      {
        value: "60s",
        label: "Booking Time",
        icon: <Briefcase className="h-5 w-5 text-primary" />,
      },
      {
        value: "AI",
        label: "Powered Bot",
        icon: <LinkIcon className="h-5 w-5 text-primary" />,
      },
    ],
    images: [
      "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2070&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=2071&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1543269865-cbf427effbad?q=80&w=2070&auto=format&fit=crop",
    ],
  };

  return (
    <div className="w-full bg-background">
      <HeroSection {...heroData} />
    </div>
  );
};
