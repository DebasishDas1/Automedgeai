"use client";

import { Clock } from "lucide-react";
import { format } from "date-fns";

type BookingFormProps = {
  selectedSlot: Date | null;
  formData: { name: string; email: string; website: string; teamSize: string };
  setFormData: (data: {
    name: string;
    email: string;
    website: string;
    teamSize: string;
  }) => void;
  onConfirm: (e: React.FormEvent) => void;
  onBack: () => void;
  isSubmitting?: boolean;
};

export const BookingForm = ({
  selectedSlot,
  formData,
  setFormData,
  onConfirm,
  onBack,
  isSubmitting = false,
}: BookingFormProps) => {
  return (
    <div className="p-8 md:p-14 max-w-2xl mx-auto w-full">
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-3 bg-accent/10 px-6 py-3 rounded-full text-accent font-black text-sm mb-6 border border-accent/20 animate-in fade-in slide-in-from-bottom-2">
          <Clock className="w-5 h-5" />
          {selectedSlot ? format(selectedSlot, "MMMM do 'at' h:mm a") : ""}
        </div>
        <h3 className="text-3xl md:text-4xl font-outfit font-black text-foreground tracking-tight">
          A few quick details
        </h3>
        <p className="text-muted-foreground mt-3 text-lg font-medium opacity-80 leading-relaxed">
          Just enough to help us customize <br className="hidden sm:block" />
          the demo for your business.
        </p>
      </div>

      <form onSubmit={onConfirm} className="space-y-6">
        <div className="space-y-3">
          <label className="text-sm font-black text-foreground/70 ml-2 tracking-wide uppercase">
            Full Name
          </label>
          <input
            required
            type="text"
            placeholder="e.g. Mike Miller"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full bg-background/60 border-2 border-border/50 rounded-2xl p-5 focus:border-accent focus:ring-4 focus:ring-accent/10 outline-none font-bold text-lg placeholder:text-muted-foreground/30 transition-all shadow-inner"
          />
        </div>
        <div className="space-y-3">
          <label className="text-sm font-black text-foreground/70 ml-2 tracking-wide uppercase">
            Work Email
          </label>
          <input
            required
            type="email"
            placeholder="e.g. mike@hvacpros.com"
            value={formData.email}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
            className="w-full bg-background/60 border-2 border-border/50 rounded-2xl p-5 focus:border-accent focus:ring-4 focus:ring-accent/10 outline-none font-bold text-lg placeholder:text-muted-foreground/30 transition-all shadow-inner"
          />
        </div>
        <div className="space-y-3">
          <label className="text-sm font-black text-foreground/70 ml-2 tracking-wide uppercase">
            Company Name
          </label>
          <input
            required
            type="text"
            placeholder="e.g. www.hvacpros.com"
            value={formData.website}
            onChange={(e) =>
              setFormData({ ...formData, website: e.target.value })
            }
            className="w-full bg-background/60 border-2 border-border/50 rounded-2xl p-5 focus:border-accent focus:ring-4 focus:ring-accent/10 outline-none font-bold text-lg placeholder:text-muted-foreground/30 transition-all shadow-inner"
          />
        </div>

        <div className="space-y-3">
          <label className="text-sm font-black text-foreground/70 ml-2 tracking-wide uppercase">
            Team Size
          </label>
          <select
            value={formData.teamSize}
            onChange={(e) =>
              setFormData({ ...formData, teamSize: e.target.value })
            }
            className="w-full bg-background/60 border-2 border-border/50 rounded-2xl p-5 focus:border-accent focus:ring-4 focus:ring-accent/10 outline-none font-bold text-lg appearance-none cursor-pointer transition-all shadow-inner"
          >
            <option value="1-5">1-5 Employees</option>
            <option value="6-20">6-20 Employees</option>
            <option value="20+">20+ Employees</option>
          </select>
        </div>

        <div className="pt-6 flex flex-col sm:flex-row gap-5">
          <button
            type="button"
            onClick={onBack}
            className="flex-1 py-5 px-6 rounded-2xl font-black bg-muted/40 text-muted-foreground hover:bg-muted/80 transition-all border-2 border-border/50 text-lg active:scale-95"
          >
            Back
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className={`flex-2 py-5 px-6 rounded-2xl font-black bg-cta glow-cta shadow-2xl text-foreground hover:-translate-y-1 active:scale-95 transition-all text-xl ${
              isSubmitting ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            {isSubmitting ? "Booking..." : "Confirm My Demo"}
          </button>
        </div>
      </form>
    </div>
  );
};
