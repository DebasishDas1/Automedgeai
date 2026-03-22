"use client";

import { m as motion } from "framer-motion";
import {
  Send,
  MessageCircle,
  Mail,
  X,
  Linkedin,
  Instagram,
  Facebook,
  ArrowRight,
} from "lucide-react";
import { useState } from "react";

export function ContactSection() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    industry: "",
    message: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Thank you! We'll be in touch shortly.");
  };

  return (
    <section id="contact" className="px-6 max-w-7xl mx-auto scroll-mt-24">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-start">
        {/* Left: Form */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="space-y-12 text-center lg:text-left"
        >
          <div className="flex flex-col items-center lg:items-start">
            <h2 className="text-5xl md:text-7xl font-outfit font-extrabold mb-6 tracking-tighter leading-none">
              Let's talk scale.
            </h2>
            <p className="text-xl md:text-2xl text-muted-foreground font-sans font-medium tracking-tight max-w-xl">
              Ready to automate your inquiries? Fill out the form and our team
              will get back to you within 60 minutes.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <input
                type="text"
                placeholder="Name"
                aria-label="Full Name"
                className="w-full px-8 py-5 rounded-4xl bg-card border-2 border-border focus:border-accent outline-none transition-all font-sans font-semibold text-lg"
                required
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
              />
              <input
                type="email"
                placeholder="Email"
                aria-label="Work Email"
                className="w-full px-8 py-5 rounded-4xl bg-card border-2 border-border focus:border-accent outline-none transition-all font-sans font-semibold text-lg"
                required
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
              />
            </div>
            <select
              aria-label="Filter by Industry"
              className="w-full px-8 py-5 rounded-4xl bg-card border-2 border-border focus:border-accent outline-none transition-all font-sans font-semibold text-lg appearance-none cursor-pointer"
              required
              value={formData.industry}
              onChange={(e) =>
                setFormData({ ...formData, industry: e.target.value })
              }
            >
              <option value="" disabled>
                Select Industry
              </option>
              <option value="hvac">HVAC</option>
              <option value="roofing">Roofing</option>
              <option value="plumbing">Plumbing</option>
              <option value="other">Other</option>
            </select>
            <textarea
              placeholder="How can we help?"
              aria-label="Your Message"
              rows={4}
              className="w-full px-8 py-5 rounded-4xl bg-card border-2 border-border focus:border-accent outline-none transition-all font-sans font-semibold text-lg resize-none"
              required
              value={formData.message}
              onChange={(e) =>
                setFormData({ ...formData, message: e.target.value })
              }
            ></textarea>
            <div className="flex justify-center lg:justify-start">
              <button
                type="submit"
                className="w-full md:w-auto px-12 py-5 bg-primary text-primary-foreground rounded-full font-sans font-black text-xl hover:scale-105 transition-all flex items-center justify-center gap-3 group shadow-2xl"
              >
                Send Message
                <Send className="w-6 h-6 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
              </button>
            </div>
          </form>
        </motion.div>

        {/* Right: Direct Contact & Socials */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="space-y-16 flex flex-col items-center lg:items-start text-center lg:text-left"
        >
          <div className="space-y-8 w-full">
            <h3 className="text-xl font-outfit font-black tracking-[0.3em] uppercase opacity-40">
              Direct Contact
            </h3>
            <div className="space-y-6">
              <a
                href="https://wa.me/9830561158"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-col sm:flex-row items-center gap-8 p-8 rounded-[2.5rem] border-2 border-border hover:border-accent/40 bg-card hover:bg-accent/5 transition-all group shadow-sm hover:shadow-xl"
              >
                <div className="w-20 h-20 rounded-2xl bg-accent/10 flex items-center justify-center text-accent group-hover:bg-accent group-hover:text-accent-foreground group-hover:scale-110 transition-all duration-300 shadow-inner [&_svg]:w-10 [&_svg]:h-10">
                  <MessageCircle />
                </div>
                <div>
                  <div className="font-outfit font-extrabold text-2xl tracking-tight">
                    WhatsApp Us
                  </div>
                  <div className="text-lg text-muted-foreground font-sans font-medium leading-tight">
                    Instant support for urgent inquiries.
                  </div>
                </div>
                <ArrowRight className="w-8 h-8 ml-auto opacity-0 group-hover:opacity-100 transition-all -translate-x-4 group-hover:translate-x-0 hidden sm:block" />
              </a>

              <a
                href="mailto:hello@automedge.com"
                className="flex flex-col sm:flex-row items-center gap-8 p-8 rounded-[2.5rem] border-2 border-border hover:border-primary/40 bg-card hover:bg-primary/5 transition-all group shadow-sm hover:shadow-xl"
              >
                <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground group-hover:scale-110 transition-all duration-300 shadow-inner [&_svg]:w-10 [&_svg]:h-10">
                  <Mail />
                </div>
                <div>
                  <div className="font-outfit font-extrabold text-2xl tracking-tight">
                    Email Us
                  </div>
                  <div className="text-lg text-muted-foreground font-sans font-medium tracking-tight">
                    hello@automedge.com
                  </div>
                </div>
                <ArrowRight className="w-8 h-8 ml-auto opacity-0 group-hover:opacity-100 transition-all -translate-x-4 group-hover:translate-x-0 hidden sm:block" />
              </a>
            </div>
          </div>

          <div className="space-y-8">
            <h3 className="text-xl font-outfit font-black tracking-[0.3em] uppercase opacity-40">
              Follow Us
            </h3>
            <div className="flex flex-wrap justify-center lg:justify-start gap-6">
              {[
                { icon: <X />, href: "#" },
                { icon: <Linkedin />, href: "#" },
                { icon: <Facebook />, href: "#" },
                { icon: <Instagram />, href: "#" },
              ].map((social, i) => (
                <a
                  key={i}
                  href={social.href}
                  className="w-20 h-20 rounded-3xl border-2 border-border flex items-center justify-center hover:bg-foreground hover:text-background hover:border-foreground transition-all text-muted-foreground shadow-sm hover:shadow-xl [&_svg]:w-8 [&_svg]:h-8"
                >
                  {social.icon}
                </a>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
