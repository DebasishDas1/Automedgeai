import dynamic from "next/dynamic";
import { Metadata } from "next";

// Above the fold - static
import { DemoPageNavbar } from "@/components/shared/DemoPageNavbar";
import { DemoPageHero } from "@/components/shared/DemoPageHero";
import { DemoPageFooter } from "@/components/shared/DemoPageFooter";
import { ChatbotWrapper } from "@/components/shared/ChatbotWrapper";
import { CallAgent } from "@/components/shared/CallAgent";

const DemoPageCalendar = dynamic(() =>
  import("@/components/shared/DemoPageCalendar").then(
    (mod) => mod.DemoPageCalendar,
  ),
);
const FAQSection = dynamic(() =>
  import("@/components/FAQSection").then((mod) => mod.FAQSection),
);
const RoiCalculator = dynamic(() =>
  import("@/components/shared/RoiCalculator").then((mod) => mod.RoiCalculator),
);
const DemoFullSystem = dynamic(() =>
  import("@/components/shared/DemoFullSystem").then(
    (mod) => mod.DemoFullSystem,
  ),
);

export const metadata: Metadata = {
  title: "See AI Book HVAC Jobs in 60 Seconds — Live Demo | AutomEdge",
  description:
    "Watch AutomEdge respond to an HVAC lead, qualify the issue, and book the job automatically. Enter your number — get a real text in under 60 seconds.",
  openGraph: {
    title: "Live HVAC Demo — AutomEdge",
    description:
      "Watch AutomEdge respond to an HVAC lead, qualify the issue, and book the job automatically. Enter your number — get a real text in under 60 seconds.",
    images: ["/hvac.png"],
  },
  twitter: {
    title: "Live HVAC Demo — AutomEdge",
    description:
      "Watch AutomEdge respond to an HVAC lead, qualify the issue, and book the job automatically. Enter your number — get a real text in under 60 seconds.",
    images: ["/hvac.png"],
  },
};

const FAQS = [
  {
    question: "How long does setup take?",
    answer:
      "14 days from signed agreement to fully live system. We handle everything — you provide calendar access and CRM login. Most owners spend under 2 hours total.",
  },
  {
    question: "Does it work with ServiceTitan / Jobber / HouseCall Pro?",
    answer:
      "Yes — we integrate natively with all three plus most other major HVAC platforms. We'll confirm compatibility on the demo call.",
  },
  {
    question: "What if a customer gets upset about automated texts?",
    answer:
      "Extremely rare in practice. Messages are personalised with name and business name — they feel like a real response. Most customers comment on how fast the reply was.",
  },
  {
    question: "Is there a long-term contract?",
    answer:
      "Month-to-month, always. No lock-in, no cancellation fees. Average client stays 18+ months because it works.",
  },
  {
    question: "What if I only get 20 leads a month?",
    answer:
      "That's a great starting point. Recovering 3 extra jobs at $3,500 average = $10,500 extra per month. The system pays for itself in the first recovered job.",
  },
];

const STEPS = [
  {
    title: "60-Second Lead Response",
    description:
      "Every HVAC lead — web form, missed call, ad click — gets a personalised SMS in under 60 seconds. 24/7, including weekends and after-hours.",
    message:
      "Hi Sarah! Mike here from Lone Star Cooling. Quick question — is your AC blowing warm air, or barely any airflow at all?",
    smallWin: "78% of HVAC jobs go to whoever responds first",
  },
  {
    title: "AI Lead Qualifier",
    description:
      "The AI asks the right questions — unit age, issue type, urgency level. Tags each lead automatically so your tech arrives prepared with the right parts.",
    message:
      "Got it — and how old is the unit approximately? Helps us send the right tech with the right parts.",
    smallWin: "No more wasted site visits on unqualified leads",
  },
  {
    title: "Automatic Appointment Booking",
    description:
      "Once qualified, the AI sends available slots and a direct booking link. Lead picks a time. Calendar invite fires to both parties instantly.",
    message:
      "We have tomorrow 9–11am or Thursday 2–4pm open. Here's your booking link — takes 30 seconds: [link]",
    smallWin: "Lead to booked job in under 10 minutes",
  },
  {
    title: "14-Day Follow-Up Sequence",
    description:
      "Leads who don't book immediately get a 4-touch sequence over 14 days. Different angle each time — value, urgency, seasonal offer.",
    message:
      "Day 5: Still having trouble with the AC? We have openings this week and it's only getting hotter in Dallas.",
    smallWin: "Most HVAC jobs close on follow-up 3–5",
  },
  {
    title: "Google Review Generation",
    description:
      "2 hours after job complete, the system sends a review request with a direct Google link. More reviews = higher Google ranking = free leads.",
    message:
      "Hi Sarah! Hope the AC is running perfectly 🙌 If we did a great job, a quick Google review would mean the world: [link]",
    smallWin: "Reputation building on autopilot",
  },
];

export default function HvacLandingPage() {
  return (
    <main className="min-h-screen">
      <DemoPageNavbar />
      <CallAgent type={"hvac"} />

      <DemoPageHero
        title="See How HVAC Companies Book"
        highlight="30% More Jobs"
        subTitle="Without Hiring Anyone."
        description="Enter your number in the demo below. In under 60 seconds you'll get a real text — the exact experience your customers get the moment they contact your business."
        tags={[
          "No app needed",
          "Real SMS to your phone",
          "90 seconds to see it",
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
        title="Like what you saw? Let's build this for"
        highlight="your HVAC business."
        description="15 minutes. We show you exactly what this looks like built for your business — your branding, your calendar, your CRM. No pitch. No pressure."
        type="hvac"
      />

      <DemoPageFooter />

      <ChatbotWrapper vertical="hvac" />
    </main>
  );
}
