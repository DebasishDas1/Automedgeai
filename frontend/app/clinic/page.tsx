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

import { SectionSkeleton } from "@/components/shared/SectionSkeleton";
import { PositioningSection } from "@/components/PositioningSection";
import { DemoPageNavbar } from "@/components/shared/DemoPageNavbar";
import { DirectContactSection } from "@/components/DirectContactSection";
import { YoutubeEmbed } from "@/components/shared/YoutubeEmbed";

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
    "See AI Book Clinic Appointments in 60 Seconds — Live Demo | AutomEdgeAi",
  description:
    "Watch AutomEdge respond to a clinic lead, qualify the issue, and book the appointment automatically.",
  openGraph: {
    title: "Live Clinic Demo — AutomEdgeAi",
    description:
      "Watch AutomEdgeAi respond to a clinic lead, qualify the issue, and book the appointment automatically.",
    images: ["/clinic.png"],
  },
  twitter: {
    title: "Live Clinic Demo — AutomEdgeAi",
    description:
      "Watch AutomEdgeAi respond to a clinic lead, qualify the issue, and book the appointment automatically.",
    images: ["/clinic.png"],
  },
};

const navItems = [
  { label: "Problems", href: "#problem" },
  { label: "Solutions", href: "#solution" },
  { label: "How it Works", href: "#how-it-works" },
  { label: "Services", href: "#services" },
  { label: "Impact", href: "#impact" },
  { label: "Watch Live Demo", href: "#youtube-demo" },
  { label: "Direct Contact", href: "#direct-contact" },
];

export default function ClinicPage() {
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

        <section id="youtube-demo" className="text-center space-y-8 py-16">
          <h2 className="text-3xl md:text-5xl font-black">
            See It Book Appointments in Real Time
          </h2>
          <p className="text-muted-foreground max-w-xl mx-auto">
            From incoming lead → AI response → confirmed booking. No human
            needed.
          </p>

          <YoutubeEmbed videoId="bDDlgM686Ds" />
        </section>

        <DemoPageCalendar
          title="Ready to see it in action?"
          highlight="Book a 15-minute demo"
          description="15 minutes. We show you exactly what this looks like built for your business — your branding, your calendar, your CRM. No pitch. No pressure."
          type="clinic"
        />
        <DirectContactSection
          whatsappNumber={"9073896612"}
          email={"team.automedgeai@gmail.com"}
        />
      </div>
    </main>
  );
}
