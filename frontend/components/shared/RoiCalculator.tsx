"use client";

import { useState, useMemo } from "react";
import { m as motion } from "framer-motion";
import {
  Calculator,
  TrendingUp,
  DollarSign,
  Target,
  ChevronRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";

type RoiCalculatorProps = {
  currencySymbol?: string;
  defaultLeads?: number;
  minLeads?: number;
  maxLeads?: number;
  leadsStep?: number;
  defaultTicketValue?: number;
  minTicketValue?: number;
  maxTicketValue?: number;
  ticketStep?: number;
  defaultCloseRate?: number;
  minCloseRate?: number;
  maxCloseRate?: number;
  closeRateStep?: number;
  customSubResult?: string;
};

export const RoiCalculator = ({
  currencySymbol = "$",
  defaultLeads = 40,
  minLeads = 10,
  maxLeads = 200,
  leadsStep = 5,
  defaultTicketValue = 3500,
  minTicketValue = 500,
  maxTicketValue = 15000,
  ticketStep = 500,
  defaultCloseRate = 20,
  minCloseRate = 5,
  maxCloseRate = 60,
  closeRateStep = 5,
  customSubResult,
}: RoiCalculatorProps) => {
  // States with intelligent defaults for trade businesses
  const [leads, setLeads] = useState<number>(defaultLeads);
  const [ticketValue, setTicketValue] = useState<number>(defaultTicketValue);
  const [closeRate, setCloseRate] = useState<number>(defaultCloseRate); // Percentage

  // Calculations
  const calculations = useMemo(() => {
    // 12% close rate lift implies recovering 12% of total leads
    const recoveredJobs = leads * 0.12;
    const additionalRevenue = Math.round(recoveredJobs * ticketValue);

    const systemCost = 997;
    const roi = Math.round(
      ((additionalRevenue - systemCost) / systemCost) * 100,
    );

    return {
      recoveredJobs: Number(recoveredJobs.toFixed(1)),
      additionalRevenue,
      systemCost,
      roi,
    };
  }, [leads, ticketValue]);

  return (
    <section id="roi" className="py-24 px-6 max-w-5xl mx-auto scroll-mt-24 w-full flex flex-col items-center">
      {/* Heading */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-16 max-w-3xl mx-auto"
      >
        <div className="flex items-center justify-center gap-2 mb-4">
          <Calculator className="w-5 h-5 text-accent" />
          <span className="label text-accent uppercase tracking-widest font-bold text-xs">ROI Calculator</span>
        </div>
        <h2 className="text-4xl md:text-6xl font-outfit tracking-tight leading-tight mb-4 text-balance">
          What's this worth to <br className="hidden md:block" />
          <span className="text-accent underline decoration-accent/20 decoration-8 underline-offset-4">your business?</span>
        </h2>
        <p className="text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
          See how much revenue is slipping through the cracks when leads wait
          hours (or days) for a response instead of seconds.
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-8 lg:gap-16 items-center w-full">
        {/* Left: Interactive Controls */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          className="space-y-10 p-8 md:p-12 rounded-4xl bg-card/50 backdrop-blur-sm border-2 border-border/50 shadow-sm"
        >
          {/* Monthly Leads Slider */}
          <div className="space-y-5">
            <div className="flex justify-between items-end">
              <div>
                <label 
                  htmlFor="leads-input"
                  className="font-bold text-foreground flex items-center gap-2 text-lg cursor-pointer"
                >
                  <Target className="w-5 h-5 text-accent" />
                  Monthly leads
                </label>
                <p className="text-sm text-muted-foreground">
                  Total inbound inquiries
                </p>
              </div>
              <span className="font-outfit font-black text-3xl text-accent">
                {leads}
              </span>
            </div>
            <input
              id="leads-input"
              type="range"
              min={minLeads}
              max={maxLeads}
              step={leadsStep}
              value={leads}
              onChange={(e) => setLeads(Number(e.target.value))}
              className="w-full h-3 bg-muted rounded-full appearance-none cursor-pointer accent-accent transition-all hover:h-4"
              aria-label="Monthly leads"
            />
          </div>

          {/* Average Ticket Value Slider */ }
          <div className="space-y-5">
            <div className="flex justify-between items-end">
              <div>
                <label 
                  htmlFor="ticket-input"
                  className="font-bold text-foreground flex items-center gap-2 text-lg cursor-pointer"
                >
                  <DollarSign className="w-5 h-5 text-accent" />
                  Average job value
                </label>
                <p className="text-sm text-muted-foreground">
                  Revenue per booked job
                </p>
              </div>
              <span className="font-outfit font-black text-3xl text-accent">
                {currencySymbol}
                {ticketValue.toLocaleString()}
              </span>
            </div>
            <input
              id="ticket-input"
              type="range"
              min={minTicketValue}
              max={maxTicketValue}
              step={ticketStep}
              value={ticketValue}
              onChange={(e) => setTicketValue(Number(e.target.value))}
              className="w-full h-3 bg-muted rounded-full appearance-none cursor-pointer accent-accent transition-all hover:h-4"
              aria-label="Average ticket value"
            />
          </div>

          {/* Current Close Rate Slider */}
          <div className="space-y-5">
            <div className="flex justify-between items-end">
              <div>
                <label 
                  htmlFor="rate-input"
                  className="font-bold text-foreground flex items-center gap-2 text-lg cursor-pointer"
                >
                  <TrendingUp className="w-5 h-5 text-accent" />
                  Current close rate
                </label>
                <p className="text-sm text-muted-foreground">
                  Leads that become paying jobs
                </p>
              </div>
              <span className="font-outfit font-black text-3xl text-accent">
                {closeRate}%
              </span>
            </div>
            <input
              id="rate-input"
              type="range"
              min={minCloseRate}
              max={maxCloseRate}
              step={closeRateStep}
              value={closeRate}
              onChange={(e) => setCloseRate(Number(e.target.value))}
              className="w-full h-3 bg-muted rounded-full appearance-none cursor-pointer accent-accent transition-all hover:h-4"
              aria-label="Current close rate"
            />
          </div>
        </motion.div>

        {/* Right: Results Display */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="flex flex-col h-full"
        >
          <Card className="border-2 border-accent/20 bg-accent/5 shadow-2xl relative overflow-hidden flex-1 flex flex-col justify-center rounded-4xl">
            {/* Background Blob */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-accent/20 rounded-full blur-[80px] -translate-y-1/2 translate-x-1/3 pointer-events-none animate-pulse" />

            <CardContent className="p-8 md:p-12 relative z-10 flex flex-col gap-8 justify-center h-full text-center items-center">
              <div className="space-y-6">
                <p className="text-sm font-black uppercase tracking-[0.2em] text-accent flex items-center justify-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  AutomEdge could recover
                </p>
                <div className="flex flex-col items-center">
                  <p className="font-outfit text-6xl md:text-8xl font-black text-foreground tracking-tighter leading-none mb-2">
                    <span className="text-accent inline-block mr-1">
                      {currencySymbol}
                    </span>
                    {calculations.additionalRevenue.toLocaleString()}
                  </p>
                  <p className="text-2xl font-bold text-muted-foreground uppercase tracking-widest">per month</p>
                </div>

                <div className="text-sm font-bold text-muted-foreground bg-background/80 border border-border/50 py-3 px-8 rounded-full inline-flex flex-wrap items-center justify-center tracking-wide gap-3">
                  <span>
                    System cost: {currencySymbol}
                    {calculations.systemCost.toLocaleString()}/mo
                  </span>
                  <span className="hidden sm:inline font-black opacity-20">|</span>
                  <span className="text-accent">
                    {customSubResult
                      ? customSubResult
                      : `ROI: ${calculations.roi.toLocaleString()}%`}
                  </span>
                </div>
              </div>

              <div className="pt-8 border-t border-accent/10 w-full">
                <Link href="#calendar" className="w-full">
                  <button className="w-full py-5 rounded-2xl bg-cta glow-cta shadow-xl text-[#412402] font-black text-xl hover:-translate-y-1 transition-all active:scale-95 group">
                    Start Recovering Jobs
                    <ChevronRight className="w-6 h-6 ml-1 inline-block transition-transform group-hover:translate-x-1" />
                  </button>
                </Link>
                <p className="text-center text-xs font-medium text-muted-foreground mt-6 opacity-60">
                  *Calculation assumes recovering 12% of your currently
                  unconverted leads based on industry standards.
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>

  );
};
