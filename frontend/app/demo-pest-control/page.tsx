import { Metadata } from "next";
import Chatbot from "@/components/shared/Chatbot";
import { DemoPageNavbar } from "@/components/shared/DemoPageNavbar";
import { DemoPageHero } from "@/components/shared/DemoPageHero";
import { DemoPageFooter } from "@/components/shared/DemoPageFooter";
import { DemoFullSystem } from "@/components/shared/DemoFullSystem";
import { RoiCalculator } from "@/components/shared/RoiCalculator";
import { FAQSection } from "@/components/FAQSection";
import { DemoPageCalendar } from "@/components/shared/DemoPageCalendar";

export const metadata: Metadata = {
  title: "See AI Book Pest Control Jobs in 60 Seconds — Live Demo | AutomEdge",
  description:
    "Pest leads are urgent. See AutomEdge respond, identify the pest, and book a treatment automatically. Try the live demo — real SMS in under 60 seconds.",
  openGraph: {
    title: "Live Pest Control Demo — AutomEdge",
    description:
      "Pest leads are urgent. See AutomEdge respond, identify the pest, and book a treatment automatically. Try the live demo — real SMS in under 60 seconds.",
    images: ["/pest_control.png"],
  },
  twitter: {
    title: "Live Pest Control Demo — AutomEdge",
    description:
      "Pest leads are urgent. See AutomEdge respond, identify the pest, and book a treatment automatically. Try the live demo — real SMS in under 60 seconds.",
    images: ["/pest_control.png"],
  },
};

const FAQS = [
  {
    question: "Does it handle both residential and commercial accounts?",
    answer:
      "Yes. Commercial leads get routed to a separate sequence with business-appropriate language and pricing context.",
  },
  {
    question: "What about emergency calls — active infestations?",
    answer:
      "Leads flagged Active or Emergency trigger an immediate notification to your on-call tech via SMS. You define what counts as an emergency — we build the rule.",
  },
  {
    question: "Can it sell quarterly maintenance plans automatically?",
    answer:
      "Yes — this is one of the highest-value automations for pest control. The 30-day and 90-day post-treatment sequences pitch your maintenance plans automatically. Most clients see 20–30% plan conversion from this alone.",
  },
  {
    question: "What if a customer complains about the treatment?",
    answer:
      'Any reply containing "complaint," "sick," or "reaction" gets flagged immediately and forwarded to you. The AI never handles complaints — it escalates them instantly.',
  },
  {
    question: "Is there a contract?",
    answer: "Month-to-month. Cancel any time. No fees.",
  },
];

const STEPS = [
  {
    title: "Instant Pest Inquiry Response",
    description: "",
    message:
      "Hi Tom here from Sunbelt Shield. Got your message — we'll get this sorted fast. Are you seeing the pests themselves or just signs?",
    smallWin:
      "Pest control is the most urgency-driven home service. First reply wins",
  },
  {
    title: "AI Pest Qualifier + Priority Tagging",
    description:
      "Identifies pest type, severity, and property type. Tags leads as Routine, Active, or Emergency. Emergency leads notify your on-call tech instantly.",
    message:
      "Got it. And is this in just the kitchen, or other rooms too? Helps us bring the right treatment.",
    smallWin: "Techs arrive prepared. No wrong products, no return visits.",
  },
  {
    title: "Treatment Booking",
    description:
      "Offers same-day or next-morning slots. Customer books in 30 seconds. Calendar updates instantly.",
    message:
      "We can be there today at 4pm or tomorrow at 9am. Here's your slot: [link]. Takes 30 seconds.",
    smallWin:
      "Urgency converts. The booking flow matches the emotional moment.",
  },
  {
    title: "Pre-Treatment Prep Instructions",
    description:
      "Night before the appointment, the system sends prep instructions — clear under sinks, store pet food. Reduces failed treatments and return visits.",
    message:
      "Reminder: Tomorrow 9–11am. For best results: clear under your kitchen sink and store pet food in sealed containers tonight.",
    smallWin:
      "Prepared customers = effective first treatments = 5-star reviews.",
  },
  {
    title: "Quarterly Plan Upsell (30/60/90 days)",
    description:
      "After treatment, the system follows up at 30, 60, and 90 days — checks results, offers quarterly plans. Your highest-margin recurring revenue, automated.",
    message:
      "Hi been 30 days since your roach treatment — all clear? Ask us about our quarterly prevention plan — most clients save $200+ annually.",
    smallWin:
      "One-time jobs have low margin. Quarterly plans are your profit engine.",
  },
  {
    title: "Review Generation",
    description: "2 hours post-treatment, automated Google review request.",
    message:
      "Hope you're pest-free! 🙏 If we did a great job, a quick Google review helps us a lot: [link]",
    smallWin: "More reviews = Google ranks you higher = free leads.",
  },
];

export default function PestControlPage() {
  return (
    <main className="min-h-screen">
      <DemoPageNavbar />

      <DemoPageHero
        title="Pest Leads Are Urgent."
        highlight="Your Response"
        subTitle="Needs to Be Even Faster."
        description="A homeowner finding roaches at 9pm books the first
company that replies — not the best one. AutomEdge
responds in under 60 seconds, identifies the pest,
and books the treatment. See it live below."
        tags={[
          "Residential and commercial",
          "Handles any pest type",
          "Real SMS to your phone in 60 seconds",
        ]}
      />

      <DemoFullSystem steps={STEPS} />

      <RoiCalculator
        defaultLeads={60}
        minLeads={10}
        maxLeads={300}
        defaultTicketValue={280}
        minTicketValue={100}
        maxTicketValue={1500}
        defaultCloseRate={30}
        minCloseRate={5}
        maxCloseRate={70}
        customSubResult="Plus quarterly plan LTV multiplier"
      />

      <FAQSection faqs={FAQS} />

      <DemoPageCalendar
        title="Ready to respond to every pest lead in 60 seconds?"
        highlight="you need 15 minutes. We build your custom pest automation live on the call."
        description="We'll show you the conversation flow for your most common pests, how emergency routing works, and what the quarterly plan upsell sequence looks like."
        type="pest_control"
        tags={[
          "Residential and commercial",
          "Handles any pest type",
          "Real SMS to your phone in 60 seconds",
          "No commitment",
          "See live build",
          "14-day setup if you proceed",
        ]}
      />

      <DemoPageFooter />

      <Chatbot vertical="pest_control" />
    </main>
  );
}
