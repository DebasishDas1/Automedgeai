import { Metadata } from "next";
import dynamic from "next/dynamic";

import {
  PROBLEMS,
  SOLUTIONS,
  STEPS,
  SERVICES,
  IMPACTS,
  TESTIMONIALS,
} from "./constants";

import { Mail, MessageCircle } from "lucide-react";

import { SectionSkeleton } from "@/components/shared/SectionSkeleton";
import { PositioningSection } from "@/components/PositioningSection";
import { DemoPageNavbar } from "@/components/shared/DemoPageNavbar";

import { ClinicHero } from "@/components/ClinicHero";

// 🔹 dynamic imports
const ProblemSection = dynamic(
  () => import("@/components/ProblemSection").then((m) => m.ProblemSection),
  { loading: () => <SectionSkeleton /> },
);

const SolutionSection = dynamic(
  () => import("@/components/SolutionSection").then((m) => m.SolutionSection),
  { loading: () => <SectionSkeleton /> },
);

const ServicesSection = dynamic(
  () => import("@/components/ServicesSection").then((m) => m.ServicesSection),
  { loading: () => <SectionSkeleton /> },
);

const DemoFullSystem = dynamic(
  () =>
    import("@/components/shared/DemoFullSystem").then((m) => m.DemoFullSystem),
  { loading: () => <SectionSkeleton /> },
);

const ImpactSection = dynamic(
  () => import("@/components/ImpactSection").then((m) => m.ImpactSection),
  { loading: () => <SectionSkeleton /> },
);

const DemoPageCalendar = dynamic(() =>
  import("@/components/shared/DemoPageCalendar").then(
    (mod) => mod.DemoPageCalendar,
  ),
);

const TestimonialSection = dynamic(
  () =>
    import("@/components/TestimonialSection").then(
      (m) => m.CircularTestimonialsDemo,
    ),
  { loading: () => <SectionSkeleton /> },
);

export const metadata: Metadata = {
  title:
    "See AI Book Clinic Appointments in 60 Seconds — Live Demo | AutomEdge",
  description:
    "Watch AutomEdge respond to a clinic lead, qualify the issue, and book the appointment automatically.",
  openGraph: {
    title: "Live Clinic Demo — AutomEdge",
    description:
      "Watch AutomEdge respond to a clinic lead, qualify the issue, and book the appointment automatically.",
    images: ["/clinic.png"],
  },
  twitter: {
    title: "Live Clinic Demo — AutomEdge",
    description:
      "Watch AutomEdge respond to a clinic lead, qualify the issue, and book the appointment automatically.",
    images: ["/clinic.png"],
  },
};

const navItems = [
  { label: "Problems", href: "#problem" },
  { label: "Solutions", href: "#solution" },
  { label: "How it Works", href: "#how-it-works" },
  { label: "Services", href: "#services" },
  { label: "Impact", href: "#impact" },
  { label: "Testimonials", href: "#testimonials" },
  { label: "Direct Contact", href: "#direct-contact" },
];


export default function ClinicPage() {
  const whatsappNumber = "9073896612"; // 🔁 replace with your number
  const email = "contact.automedgeai@gmail.com"; // 🔁 replace with your email

  return (
    <main className="min-h-screen w-full">
      <DemoPageNavbar navItems={navItems} iconLink="/clinic" />
      <ClinicHero />

      <div className="space-y-20 md:space-y-28 pb-16 md:pb-24">
        <ProblemSection problems={PROBLEMS} />
        <SolutionSection solutions={SOLUTIONS} />
        <DemoFullSystem steps={STEPS} />
        <ServicesSection services={SERVICES} />
        <ImpactSection impacts={IMPACTS} />
        <TestimonialSection testimonials={TESTIMONIALS} />
        <PositioningSection />
        <DemoPageCalendar
          title="Ready to see it in action?"
          highlight="Book a 15-minute demo"
          description="15 minutes. We show you exactly what this looks like built for your business — your branding, your calendar, your CRM. No pitch. No pressure."
          type="clinic"
        />

        <section id="direct-contact" className="px-4 md:px-8 py-12 md:py-20">
          <div className="max-w-5xl mx-auto text-center">
            {/* Heading */}
            <h2 className="text-3xl md:text-5xl font-outfit tracking-tight leading-tight mb-10 text-foreground">
              Direct Contact
            </h2>

            {/* Cards Wrapper */}
            <div className="flex flex-col md:flex-row gap-6 justify-center items-stretch">
              {/* WhatsApp Card */}
              <a
                href={`https://wa.me/${whatsappNumber}?text=Hi, I want to see the clinic automation demo`}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-center gap-6 w-full md:w-[420px] rounded-[28px] border border-white/10 bg-white/5 backdrop-blur-xl p-6 md:p-8 transition-all duration-300 hover:bg-white/10 hover:shadow-[0_10px_40px_rgba(16,185,129,0.15)]"
              >
                {/* Icon */}
                <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-emerald-500/10 shrink-0">
                  <MessageCircle className="w-7 h-7 text-emerald-400" />
                </div>

                {/* Text */}
                <div className="text-left">
                  <div className="text-lg md:text-2xl font-medium text-white">
                    WhatsApp Us
                  </div>
                  <div className="text-slate-400 text-sm md:text-base mt-1">
                    Instant support for urgent inquiries.
                  </div>
                </div>
              </a>

              {/* Email Card */}
              <a
                href={`mailto:${email}`}
                className="group flex items-center gap-6 w-full md:w-[420px] rounded-[28px] border border-white/10 bg-white/5 backdrop-blur-xl p-6 md:p-8 transition-all duration-300 hover:bg-white/10 hover:shadow-[0_10px_40px_rgba(255,255,255,0.08)]"
              >
                {/* Icon */}
                <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 shrink-0">
                  <Mail className="w-7 h-7 text-white/80" />
                </div>

                {/* Text */}
                <div className="text-left">
                  <div className="text-lg md:text-2xl font-medium text-white">
                    Email Us
                  </div>
                  <div className="text-slate-400 text-sm md:text-base mt-1">
                    {email}
                  </div>
                </div>
              </a>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
