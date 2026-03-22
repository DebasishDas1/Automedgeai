"use client";

import { m as motion } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import { useState } from "react";

type FAQSectionProps = {
  faqs: {
    question: string;
    answer: string;
  }[];
};

export function FAQSection({ faqs }: FAQSectionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="py-24 px-6 max-w-4xl mx-auto scroll-mt-24">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-16"
      >
        <h2 className="text-5xl md:text-7xl font-outfit tracking-tighter mb-4">
          Frequently Asked Questions
        </h2>
      </motion.div>

      <div className="space-y-6">
        {faqs.map((faq, index) => (
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
              <span className="font-outfit font-extrabold text-xl md:text-2xl tracking-tight pr-8 leading-tight">
                {faq.question}
              </span>
              {openIndex === index ? (
                <Minus className="w-6 h-6 text-accent" />
              ) : (
                <Plus className="w-6 h-6 text-muted-foreground" />
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
