import { Navbar } from "@/components/Navbar";
import { ModernHero } from "@/components/ModernHero";
import { ProblemSection } from "@/components/ProblemSection";
import { SolutionSection } from "@/components/SolutionSection";
import { ImpactSection } from "@/components/ImpactSection";
import { LogoCloud } from "@/components/LogoCloud";
import { FAQSection } from "@/components/FAQSection";
import { ContactSection } from "@/components/ContactSection";
import { HowItWorks } from "@/components/HowItWorks";
import { Footer } from "@/components/ui/large-name-footer";

export default function Homepage() {
  return (
    <main className="min-h-screen relative overflow-hidden">
      <Navbar />
      <ModernHero />

      <div className="space-y-32 pb-12">
        <ProblemSection />
        <HowItWorks />
        <SolutionSection />
        <ImpactSection />
        <LogoCloud />
        <FAQSection />
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
