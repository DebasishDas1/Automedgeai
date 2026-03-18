import { Metadata } from "next";
import Chatbot from "@/components/shared/Chatbot";
import { DemoPageNavbar } from "@/components/shared/DemoPageNavbar";
import { DemoPageHero } from "@/components/shared/DemoPageHero";
import { DemoPageFooter } from "@/components/shared/DemoPageFooter";
import { DemoFullSystem } from "@/components/shared/DemoFullSystem";
import { DemoPageCalendar } from "@/components/shared/DemoPageCalendar";
import { FAQSection } from "@/components/FAQSection";
import { RoiCalculator } from "@/components/shared/RoiCalculator";

export const metadata: Metadata = {
  title: "See AI Book Roofing Jobs in 60 Seconds — Live Demo | AutomEdge",
  description:
    "Roof leaks don't wait for business hours. See how AutomEdge responds instantly, assesses the damage, and books a tarp or repair appointment automatically. Try the live demo — real SMS in under 60 seconds.",
  openGraph: {
    title: "Live Roofing Demo — AutomEdge",
    description:
      "Roof leaks don't wait for business hours. See how AutomEdge responds instantly, assesses the damage, and books a tarp or repair appointment automatically. Try the live demo — real SMS in under 60 seconds.",
    images: ["/roofing.png"],
  },
  twitter: {
    title: "Live Roofing Demo — AutomEdge",
    description:
      "Roof leaks don't wait for business hours. See how AutomEdge responds instantly, assesses the damage, and books a tarp or repair appointment automatically. Try the live demo — real SMS in under 60 seconds.",
    images: ["/roofing.png"],
  },
};

const FAQS = [
  {
    question: "How quickly can you get a crew out for an emergency tarp?",
    answer:
      "For emergency tarp requests, the system automatically offers the next available same-day or next-morning slot. Most crews can be on-site within 2–4 hours depending on location and current workload.",
  },
  {
    question: "What happens if the customer doesn't have insurance?",
    answer:
      "The AI automatically routes them down a retail sales path with cash-pricing options. It never pitches insurance to cash customers — that's a major conversion killer.",
  },
  {
    question: "Can the AI handle multiple storm leads at once?",
    answer:
      "Yes. The system is built for storm volume. It can handle 100+ concurrent conversations and prioritize based on damage severity and urgency.",
  },
  {
    question: "Do you charge extra for insurance claim support?",
    answer:
      "No. It's included. The AI sends guided email templates and photo attachments to help homeowners work with their adjusters — a service that wins loyalty and referrals.",
  },
  {
    question: "What happens after the job is completed?",
    answer:
      "The system automatically follows up at 30, 60, and 90 days to check on the roof and offer maintenance plans or gutter guard upsells. This captures 20–30% more recurring revenue from your existing customer base.",
  },
  {
    question: "Is there a contract or long-term commitment?",
    answer: "Month-to-month. Cancel any time. No fees.",
  },
];

const STEPS = [
  {
    title: "Instant Storm Lead Response",
    description:
      "Every lead gets a response in under 60 seconds. Critical during storm season when 50–200 leads can hit in a 24-hour window.",
    message:
      "Hi Jake from Skyline Storm Roofing. We got your request — was this hail damage, wind, or both?",
    smallWin: "In storm markets, the inspection window is 24–72 hours.",
  },
  {
    title: "Insurance vs Cash Routing (Critical)",
    description:
      "The AI routes insurance and retail leads down completely different follow-up paths. Right message, right moment, every time.",
    message:
      "We'll give you a full written estimate on-site. No surprises. Inspection is completely free.",
    smallWin:
      "Treating an insurance lead like a cash lead is one of the biggest conversion killers in roofing.",
  },
  {
    title: "Automated Tarp Booking (Emergency)",
    description:
      "For emergency tarp requests, the system automatically offers the next available same-day or next-morning slot.",
    message:
      "We can get a crew out there today between 2–4pm to tarp the damaged area. Takes 30 seconds to confirm: [link]",
    smallWin:
      "Tarps prevent secondary water damage — and every day you wait is another day the homeowner is talking to your competitors.",
  },
  {
    title: "AI-Powered Inspection Scheduling",
    description:
      "The AI asks about property access, roof exposure, and whether they have an insurance adjuster coming. It then offers the next available 30-minute inspection slot in your calendar.",
    message:
      "We can inspect your roof tomorrow at 9am or 2pm. Which works? [link]",
    smallWin: "Most roofers lose the lead in the first hour. This locks it in.",
  },
  {
    title: "Insurance Claim Support (Automated)",
    description:
      "After inspection, the AI sends a guided email template for the homeowner to send to their adjuster — with damage photos, claim number, and your estimate attached.",
    message:
      "Here’s the email template to send your adjuster. Just copy, paste, and attach the photos we took:",
    smallWin:
      "Most roofers don't help with the claim. This positions you as the homeowner's advocate — and wins loyalty for life.",
  },
  {
    title: "Automated 30/60/90 Day Follow-Up",
    description:
      "After the job, the system automatically follows up at 30, 60, and 90 days to check on the roof and offer maintenance plans or gutter guard upsells.",
    message:
      "Hi [Name] — been 30 days since your roof replacement. How’s everything holding up?",
    smallWin:
      "Most roofers disappear after the check clears. This captures 20–30% more recurring revenue from your existing customer base.",
  },
  {
    title: "Review Generation",
    description:
      "2 hours post-job, the system sends a Google review request with a direct link. If they don't respond in 24 hours, it sends a reminder.",
    message:
      "Hope you're enjoying your new roof! If we did a great job, a quick Google review helps us out a lot: [link]",
    smallWin:
      "More reviews = higher Google ranking = more free leads. Simple math.",
  },
];

export default function RoofingPage() {
  return (
    <main className="min-h-screen">
      <DemoPageNavbar />

      <DemoPageHero
        title="Storm Season Leads Have a"
        highlight="48-Hour"
        subTitle="Window Are You Winning Them?"
        description="After every storm, every homeowner in your area files
          a request at the same time. The roofing company that
          responds in 60 seconds gets the inspection — and the job.
          See AutomEdge do it below."
        tags={[
          "Handles storm, insurance, and retail jobs separately",
          "Qualifies insurance vs cash automatically",
          "Books inspections into your calendar 24/7",
        ]}
      />

      <DemoFullSystem steps={STEPS} />

      <RoiCalculator
        defaultLeads={30}
        minLeads={5}
        maxLeads={150}
        defaultTicketValue={9500}
        minTicketValue={1000}
        maxTicketValue={50000}
        defaultCloseRate={22}
        minCloseRate={5}
        maxCloseRate={60}
      />

      <FAQSection faqs={FAQS} />

      <DemoPageCalendar
        title="Ready to respond to every storm lead in 60 seconds?"
        highlight="you need 15 minutes. We build your custom roofing automation live on the call."
        description="We'll show you the conversation flow for your most common roofing issues, how insurance routing works, and what the post-job follow-up sequence looks like."
        type="roofing"
        tags={[
          "Handles storm, insurance, and retail jobs separately",
          "Qualifies insurance vs cash automatically",
          "Real SMS to your phone in 60 seconds",
          "No commitment",
          "See live build",
          "14-day setup if you proceed",
        ]}
      />

      <DemoPageFooter />

      <Chatbot vertical="roofing" />
    </main>
  );
}
