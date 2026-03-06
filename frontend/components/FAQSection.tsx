"use client";

import { motion } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import { useState } from "react";

const FAQS = [
    {
        question: "What industries does Automedge AI serve?",
        answer: "Automedge AI is specifically built for service-based businesses, primarily focusing on HVAC, Roofing, Plumbing, and other trade services that rely on rapid lead response.",
    },
    {
        question: "How quickly can I get started with Automedge AI?",
        answer: "Most businesses can get their AI sales engine up and running within 24 to 48 hours. Our team handles the initial setup and model training for you.",
    },
    {
        question: "What happens to leads that aren't ready to book immediately?",
        answer: "The AI automatically puts them into a nurturing sequence. It checks in via text or WhatsApp at strategic intervals to answer questions and keep your business top-of-mind.",
    },
    {
        question: "Can I integrate Automedge AI with my existing CRM?",
        answer: "Yes, we support native integrations with major CRMs like ServiceTitan, Housecall Pro, and HubSpot, as well as thousands of others through Zapier.",
    },
    {
        question: "What kind of analytics and reporting do I get?",
        answer: "You get a real-time dashboard showing exactly how many leads were captured, qualified, and booked, along with detailed conversation transcripts and conversion rate trends.",
    },
];

export function FAQSection() {
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    return (
        <section id="faq" className="py-24 px-6 max-w-4xl mx-auto scroll-mt-24">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-center mb-16"
            >
                <h2 className="text-5xl md:text-7xl font-outfit font-[800] tracking-tighter mb-4">
                    Frequently Asked Questions
                </h2>
            </motion.div>

            <div className="space-y-6">
                {FAQS.map((faq, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: index * 0.1 }}
                        className="border-2 border-border/50 rounded-3xl overflow-hidden bg-card hover:border-accent/30 transition-all shadow-sm hover:shadow-lg"
                    >
                        <button
                            onClick={() => setOpenIndex(openIndex === index ? null : index)}
                            className="w-full px-8 py-8 flex items-center justify-between text-left hover:bg-muted/30 transition-colors"
                        >
                            <span className="font-outfit font-extrabold text-xl md:text-2xl tracking-tight pr-8 leading-tight">{faq.question}</span>
                            {openIndex === index ? (
                                <Minus className="w-6 h-6 flex-shrink-0 text-accent" />
                            ) : (
                                <Plus className="w-6 h-6 flex-shrink-0 text-muted-foreground" />
                            )}
                        </button>
                        {openIndex === index && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                className="px-8 pb-10 text-muted-foreground leading-relaxed font-sans font-medium text-lg"
                            >
                                {faq.answer}
                            </motion.div>
                        )}
                    </motion.div>
                ))}
            </div>
        </section>
    );
}
