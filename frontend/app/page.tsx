import { Navbar } from "@/components/Navbar";
import { ModernHero } from "@/components/ModernHero";
import { ProblemSection } from "@/components/ProblemSection";
import { SolutionSection } from "@/components/SolutionSection";
import { ImpactSection } from "@/components/ImpactSection";
import { LogoCloud } from "@/components/LogoCloud";
import { FAQSection } from "@/components/FAQSection";
import { ContactSection } from "@/components/ContactSection";
import { HowItWorks } from "@/components/HowItWorks";
import { DemoWorkflowSection } from "@/components/DemoWorkflowSection";
import { Footer } from "@/components/ui/large-name-footer";

const FAQS = [
  {
    question: "What industries does Automedge AI serve?",
    answer:
      "Automedge AI is specifically built for service-based businesses, primarily focusing on HVAC, Roofing, Plumbing, and other trade services that rely on rapid lead response.",
  },
  {
    question: "How quickly can I get started with Automedge AI?",
    answer:
      "Most businesses can get their AI sales engine up and running within 24 to 48 hours. Our team handles the initial setup and model training for you.",
  },
  {
    question: "What happens to leads that aren't ready to book immediately?",
    answer:
      "The AI automatically puts them into a nurturing sequence. It checks in via text or WhatsApp at strategic intervals to answer questions and keep your business top-of-mind.",
  },
  {
    question: "Can I integrate Automedge AI with my existing CRM?",
    answer:
      "Yes, we support native integrations with major CRMs like ServiceTitan, Housecall Pro, and HubSpot, as well as thousands of others through Zapier.",
  },
  {
    question: "What kind of analytics and reporting do I get?",
    answer:
      "You get a real-time dashboard showing exactly how many leads were captured, qualified, and booked, along with detailed conversation transcripts and conversion rate trends.",
  },
];

export default function Homepage() {
  return (
    <main className="min-h-screen relative overflow-hidden">
      <Navbar />
      <ModernHero />

      <div className="space-y-32 pb-12">
        <ProblemSection />
        <HowItWorks />
        <SolutionSection />
        <DemoWorkflowSection />
        <ImpactSection />
        <LogoCloud />
        <FAQSection faqs={FAQS} />
        <ContactSection />
        <Footer />
      </div>

      {/* <Footer /> */}

      {/* Subtle background decoration */}
      <div className="fixed top-1/4 -left-20 w-80 h-80 bg-accent/5 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="fixed bottom-1/4 -right-20 w-96 h-96 bg-primary/5 rounded-full blur-3xl -z-10 animate-pulse delay-700"></div>
    </main>
  );
}
