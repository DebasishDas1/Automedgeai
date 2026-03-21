import { Metadata } from "next";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/ui/large-name-footer";
import { Mail, LifeBuoy, Send } from "lucide-react";

export const metadata: Metadata = {
  title: "Contact the Automedge Team | Support & Sales for Service Automation",
  description:
    "Get in touch with the Automedge team. We're here to help HVAC, Roofing, and Plumbing businesses automate their leads and bookings.",
};

export default function ContactPage() {
  return (
    <main className="min-h-screen relative flex flex-col bg-background selection:bg-accent/30">
      <Navbar />

      <div className="flex-1 pt-32 pb-24 px-6 max-w-4xl mx-auto w-full relative z-10">
        {/* Premium Background Blobs */}
        <div className="absolute top-0 right-1/3 w-[600px] h-[600px] bg-accent/5 rounded-full blur-[120px] -z-10 pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[100px] -z-10 pointer-events-none" />

        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-7xl font-outfit font-black tracking-tighter mb-6">
            Contact <span className="text-accent">Us</span>
          </h1>
          <p className="text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto font-sans">
            Have a question about Automedge, need help with your account, or
            just want to chat about AI automation? We'd love to hear from you.
          </p>
        </div>

        <div className="prose prose-lg dark:prose-invert max-w-none font-sans relative z-20">
          <div className="grid sm:grid-cols-2 gap-8 mb-16">
            <div className="p-10 rounded-[2.5rem] border border-border bg-card/40 backdrop-blur-2xl shadow-xl hover:shadow-2xl transition-all hover:-translate-y-1 text-center group">
              <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto mb-6 text-accent group-hover:scale-110 transition-transform">
                <Mail className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold font-outfit mb-4 text-foreground">
                Talk to Sales
              </h3>
              <p className="text-muted-foreground mb-6 leading-relaxed">
                Interested in how Automedge can scale your business?
              </p>
              <a
                href="mailto:hello@automedge.com"
                className="text-accent font-bold hover:underline text-lg inline-block"
              >
                Email Sales Team
              </a>
            </div>

            <div className="p-10 rounded-[2.5rem] border border-border bg-card/40 backdrop-blur-2xl shadow-xl hover:shadow-2xl transition-all hover:-translate-y-1 text-center group">
              <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6 text-primary group-hover:scale-110 transition-transform">
                <LifeBuoy className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-bold font-outfit mb-4 text-foreground">
                Support
              </h3>
              <p className="text-muted-foreground mb-6 leading-relaxed">
                Need technical assistance with your current system?
              </p>
              <a
                href="mailto:support@automedge.com"
                className="text-primary font-bold hover:underline text-lg inline-block"
              >
                Email Technical Support
              </a>
            </div>
          </div>

          <h2 className="text-3xl font-bold font-outfit mb-6 text-foreground text-center">
            Send a Message
          </h2>

          <form className="space-y-6 max-w-2xl mx-auto border-t border-border pt-10">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label
                  htmlFor="name"
                  className="font-semibold text-sm pl-4 block"
                >
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  className="w-full px-6 py-4 rounded-full bg-card border border-border focus:border-accent outline-none transition-all font-sans font-medium"
                  placeholder="John Doe"
                  required
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="email"
                  className="font-semibold text-sm pl-4 block"
                >
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  className="w-full px-6 py-4 rounded-full bg-card border border-border focus:border-accent outline-none transition-all font-sans font-medium"
                  placeholder="john@company.com"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label
                htmlFor="message"
                className="font-semibold text-sm pl-4 block"
              >
                Message
              </label>
              <textarea
                id="message"
                rows={5}
                className="w-full px-6 py-4 rounded-4xl bg-card border border-border focus:border-accent outline-none transition-all font-sans font-medium resize-none"
                placeholder="How can we help?"
                required
              />
            </div>

            <div className="flex justify-center pt-4">
              <button
                type="submit"
                className="w-full md:w-auto px-12 py-5 bg-foreground text-background rounded-full font-sans font-black text-xl hover:scale-105 transition-all flex items-center justify-center gap-3 group shadow-xl"
              >
                Send Message
                <Send className="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
              </button>
            </div>
          </form>
        </div>
      </div>

      <Footer />
    </main>
  );
}
