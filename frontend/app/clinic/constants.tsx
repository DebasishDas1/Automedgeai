import {
  Clock,
  MessageSquareOff,
  EyeOff,
  UserX,
  Users,
  TrendingDown,
  PhoneCall,
  MessageCircle,
  Inbox,
  CalendarCheck,
  BrainCircuit,
  BarChart3,
  Globe,
  RefreshCcw,
  Timer,
  TrendingUp,
  Briefcase,
  Moon,
} from "lucide-react";

export const PROBLEMS = [
  {
    icon: <Clock className="w-8 h-8" />,
    text: "Missed calls during busy hours",
    desc: "Patients call while you’re occupied. Every missed call is a lost booking.",
  },
  {
    icon: <MessageSquareOff className="w-8 h-8" />,
    text: "Slow WhatsApp replies",
    desc: "Patients expect instant replies. Even a few minutes delay costs real leads.",
  },
  {
    icon: <EyeOff className="w-8 h-8" />,
    text: "No after-hours response system",
    desc: "Night and weekend inquiries go unanswered — and patients move on.",
  },
  {
    icon: <UserX className="w-8 h-8" />,
    text: "Manual follow-ups rarely happen",
    desc: "Most patients need multiple touchpoints, but teams rarely follow through.",
  },
  {
    icon: <Users className="w-8 h-8" />,
    text: "Staff overwhelmed with inquiries",
    desc: "Your team spends more time replying than treating patients.",
  },
  {
    icon: <TrendingDown className="w-8 h-8" />,
    text: "Leads drop off before booking",
    desc: "Without instant engagement, interest fades before conversion.",
  },
];

export const SOLUTIONS = [
  {
    icon: <PhoneCall className="w-6 h-6" />,
    title: "Answers calls instantly",
    description:
      "AI picks up every call, qualifies the patient, and responds in real time.",
  },
  {
    icon: <MessageCircle className="w-6 h-6" />,
    title: "Replies on WhatsApp instantly",
    description:
      "Human-like replies within seconds keep conversations active and engaged.",
  },
  {
    icon: <Inbox className="w-6 h-6" />,
    title: "Captures every inquiry",
    description: "All leads are tracked, organized, and ready for follow-up.",
  },
  {
    icon: <CalendarCheck className="w-6 h-6" />,
    title: "Books appointments automatically",
    description:
      "Schedules directly into your calendar without back-and-forth.",
  },
  {
    icon: <BrainCircuit className="w-6 h-6" />,
    title: "Qualifies leads intelligently",
    description: "Focus only on high-intent patients who are ready to book.",
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    title: "Tracks performance in real time",
    description: "Clear insights on leads, response times, and conversions.",
  },
];

export const STEPS = [
  {
    title: "Patient reaches out",
    description:
      "Leads contact you through calls, WhatsApp, or your website — whenever they’re ready.",
    message:
      "New inquiry from John — 'Need help with booking an appointment this week.'",
    smallWin: "Be present everywhere your customers are",
  },
  {
    title: "AI responds instantly",
    description:
      "No delays, no missed opportunities. AI replies within seconds, engaging the lead while interest is highest.",
    message:
      "Hi John! Thanks for reaching out 😊 I can help you book an appointment. What day works best for you?",
    smallWin: "Speed is the difference between winning and losing a lead",
  },
  {
    title: "Appointment gets booked",
    description:
      "AI checks your availability and schedules appointments automatically without back-and-forth.",
    message:
      "You're all set for Tuesday at 3 PM. Looking forward to seeing you!",
    smallWin: "Zero friction means more confirmed bookings",
  },
  {
    title: "Follow-ups happen automatically",
    description:
      "Reminders, reschedules, and re-engagement messages are handled for you — so no lead goes cold.",
    message:
      "Reminder: Your appointment is tomorrow at 3 PM. Reply here if you need to reschedule.",
    smallWin: "Consistent follow-ups = higher show-up rates",
  },
];

export const SERVICES = [
  {
    icon: <PhoneCall className="w-6 h-6" />,
    title: "AI Voice Receptionist",
    description:
      "Handles incoming calls, answers common questions, and books appointments — just like a real receptionist, but available 24/7.",
  },
  {
    icon: <MessageCircle className="w-6 h-6" />,
    title: "WhatsApp Automation",
    description:
      "Instant replies, guided service selection, and seamless booking — right where most of your patients already are.",
  },
  {
    icon: <Globe className="w-6 h-6" />,
    title: "AI Chatbot (Website & Ads)",
    description:
      "Captures leads from your website and campaigns, engages them instantly, and converts them into booked appointments.",
  },
  {
    icon: <RefreshCcw className="w-6 h-6" />,
    title: "Automated Follow-ups",
    description:
      "Reminders, missed appointment recovery, and re-engagement messages — all handled automatically without manual effort.",
  },
];

export const IMPACTS = [
  {
    icon: <Timer className="w-8 h-8 text-accent" />,
    stat: "2–3x",
    label: "Faster Response Time",
  },
  {
    icon: <TrendingUp className="w-8 h-8 text-accent" />,
    stat: "20–40%",
    label: "More Patient Inquiries Captured",
  },
  {
    icon: <CalendarCheck className="w-8 h-8 text-accent" />,
    stat: "↑ Daily",
    label: "Bookings Without Extra Staff",
  },
  {
    icon: <Briefcase className="w-8 h-8 text-accent" />,
    stat: "Up to 70%",
    label: "Reduced Front Desk Workload",
  },
  {
    icon: <Moon className="w-8 h-8 text-accent" />,
    stat: "24/7",
    label: "After-Hours Patients Captured",
  },
];

export const TESTIMONIALS = [
  {
    text: "Earlier, we used to miss a lot of calls during peak hours, especially evenings. We didn’t realize how many patients we were losing until we saw the data. After setting this up, calls are handled instantly and WhatsApp replies are automated. Our daily bookings have definitely gone up, and the front desk is much less chaotic now.",
    image:
      "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?q=80&w=1368&auto=format&fit=crop",
    name: "Dr. Ayesha Mehta",
    role: "Skin Clinic Owner",
  },
  {
    text: "We already had a receptionist, so I wasn’t sure if we needed this. But the difference came after hours — that’s where we were losing patients. Now inquiries at night or on Sundays are automatically captured and booked. It’s like the clinic never really closes.",
    image:
      "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?q=80&w=1368&auto=format&fit=crop",
    name: "Dr. Rohan Shah",
    role: "Dental Clinic Founder",
  },
  {
    text: "Our challenge wasn’t leads — it was conversion. We were spending on ads, but response time was inconsistent. With the automation in place, every inquiry gets an instant response and is tracked properly. We’ve seen a clear improvement in lead-to-appointment conversion.",
    image:
      "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=1368&auto=format&fit=crop",
    name: "Neha Kapoor",
    role: "Marketing Manager, Multi-Speciality Hospital",
  },
  {
    text: "Most of our patients come from WhatsApp, and earlier it was completely manual. If we got busy, replies were delayed and people would just drop off. Now the system handles initial conversations and booking smoothly. It’s saved a lot of time and improved consistency.",
    image:
      "https://images.unsplash.com/photo-1594824476967-48c8b964273f?q=80&w=1368&auto=format&fit=crop",
    name: "Karan Malhotra",
    role: "Hair Clinic Owner",
  },
  {
    text: "Managing appointments, follow-ups, and missed calls used to be messy, especially with multiple staff involved. This system brought everything into one flow. We’re not just saving time — we’re also seeing better patient retention because follow-ups actually happen now.",
    image:
      "https://images.unsplash.com/photo-1582750433449-648ed127bb54?q=80&w=1368&auto=format&fit=crop",
    name: "Priya Nair",
    role: "Operations Manager, Wellness Clinic",
  },
  {
    text: "What I liked most is that it didn’t require us to change everything. We started small, tested it, and saw results within a few weeks. It’s a practical solution — not just another tool. It actually improves how the clinic runs day to day.",
    image:
      "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?q=80&w=1368&auto=format&fit=crop",
    name: "Dr. Vikram Sethi",
    role: "Cosmetic Clinic Director",
  },
  {
    text: "We were missing a surprising number of calls during peak hours, and patients wouldn’t always leave voicemails. After implementing this system, every call gets answered and routed properly. We’ve seen a noticeable increase in booked appointments without adding more staff.",
    image:
      "https://images.unsplash.com/photo-1550831107-1553da8c8464?q=80&w=1368&auto=format&fit=crop",
    name: "Dr. Emily Carter",
    role: "Dermatology Clinic Owner (USA)",
  },
  {
    text: "Our front desk team was constantly juggling calls, walk-ins, and scheduling. It was easy for things to slip through. The automation now handles a large portion of incoming inquiries and bookings, which has reduced the pressure on our staff significantly.",
    image:
      "https://images.unsplash.com/photo-1524267213992-b76e8577d046?q=80&w=1368&auto=format&fit=crop&ixlib=rb-4.0.3",
    name: "Jason Miller",
    role: "Practice Manager, Dental Clinic (USA)",
  },
  {
    text: "A lot of our leads come in after hours, especially from ads and social media. Before, we were losing those opportunities. Now every inquiry is responded to instantly, and clients can book without waiting. It’s made a real difference in how we convert leads.",
    image:
      "https://images.unsplash.com/photo-1598257006458-087169a1f08d?q=80&w=1368&auto=format&fit=crop",
    name: "Sophia Reynolds",
    role: "Med Spa Owner (USA)",
  },
  {
    text: "Speed of response was our biggest bottleneck. Even a delay of 10–15 minutes was impacting conversions. With this system, response time is no longer an issue. Every lead is captured, followed up, and tracked properly.",
    image:
      "https://images.unsplash.com/photo-1607746882042-944635dfe10e?q=80&w=1368&auto=format&fit=crop",
    name: "Daniel Brooks",
    role: "Marketing Lead, Healthcare Group (USA)",
  },
  {
    text: "We wanted something that could support our front desk without replacing the human touch. This system handles the repetitive tasks like answering basic questions and booking appointments, so our team can focus on patient experience.",
    image:
      "https://images.unsplash.com/photo-1537368910025-700350fe46c7?q=80&w=1368&auto=format&fit=crop",
    name: "Dr. Michael Turner",
    role: "Chiropractic Clinic Owner (USA)",
  },
  {
    text: "What stood out was how easy it was to integrate into our existing workflow. We didn’t need to overhaul our systems. Within a few weeks, we could clearly see improved booking consistency and fewer missed opportunities.",
    image:
      "https://images.unsplash.com/photo-1576091160550-2173dba999ef?q=80&w=1368&auto=format&fit=crop",
    name: "Laura Bennett",
    role: "Aesthetic Clinic Director (USA)",
  },
];
