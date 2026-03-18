"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calendar as CalendarIcon,
  Clock,
  CheckCircle2,
  ChevronRight,
  Video,
  Check,
} from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { addMinutes, setHours, setMinutes, isToday, format } from "date-fns";
import { Badge } from "@/components/ui/badge";

type DemoPageCalendarProps = {
  title?: string;
  highlight?: string;
  description?: string;
  type?: "hvac" | "pest_control" | "plumbing" | "roofing" | "landscaping";
  tags?: string[];
};

export const DemoPageCalendar = ({
  title = "Ready to build this for",
  highlight = "your business?",
  description = "Book a quick 15-minute chat to see exactly how AutomEdge fits into your specific workflow. No pressure, just a live demo.",
  tags = [],
}: DemoPageCalendarProps) => {
  const [mounted, setMounted] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(
    new Date(),
  );
  const [slots, setSlots] = useState<Date[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<Date | null>(null);
  const [isBooked, setIsBooked] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!selectedDate) {
      setSlots([]);
      return;
    }

    const generated: Date[] = [];
    let start = setHours(setMinutes(selectedDate, 0), 9);
    let end = setHours(setMinutes(selectedDate, 0), 18);

    if (isToday(selectedDate)) {
      const now = new Date();
      // Round to next 15/30 min increment
      const remainder = 30 - (now.getMinutes() % 30);
      start = addMinutes(now, remainder);
      // Ensure we don't start before 9 AM even if it's today
      if (start < setHours(setMinutes(selectedDate, 0), 9)) {
        start = setHours(setMinutes(selectedDate, 0), 9);
      }
    }

    // Generate slots
    while (start < end && generated.length < 16) {
      // Don't generate slots in the past
      if (start > new Date()) {
        generated.push(start);
      }
      start = addMinutes(start, 30);
    }

    setSlots(generated);
  }, [selectedDate]);

  const handleBooking = () => {
    if (selectedSlot) {
      setIsBooked(true);
      // Here you would typically trigger an API call or analytics event
    }
  };

  if (!mounted) return null;

  return (
    <section
      id="calendar"
      className="relative py-24 px-6 max-w-5xl mx-auto scroll-mt-24"
    >
      {/* Background Blobs */}
      <div className="absolute top-1/2 left-0 w-[400px] h-[400px] bg-accent/5 rounded-full blur-[120px] -translate-y-1/2 -z-10 pointer-events-none" />
      <div className="absolute top-1/2 right-0 w-[400px] h-[400px] bg-primary/5 rounded-full blur-[120px] -translate-y-1/2 -z-10 pointer-events-none" />

      {/* Heading */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-16 max-w-3xl mx-auto flex flex-col items-center"
      >
        <div className="flex items-center justify-center gap-2 mb-4">
          <CalendarIcon className="w-5 h-5 text-accent" />
          <span className="label text-accent">Book a Live Demo</span>
        </div>

        <h2 className="text-4xl md:text-5xl font-outfit tracking-tight leading-tight mb-4">
          {title} <span className="text-accent">{highlight}</span>
        </h2>

        {description && (
          <p className="text-lg text-muted-foreground opacity-90 max-w-2xl mx-auto leading-relaxed">
            {description}
          </p>
        )}
      </motion.div>

      {/* Booking Interface */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.1 }}
      >
        <Card className="w-full max-w-4xl mx-auto border-2 border-border/50 shadow-xl bg-card/60 backdrop-blur-sm overflow-hidden relative">
          <AnimatePresence mode="wait">
            {!isBooked ? (
              <motion.div
                key="calendar"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="p-8 md:p-10"
              >
                <div className="flex flex-col md:flex-row gap-10 lg:gap-16">
                  {/* Left: Calendar Picker */}
                  <div className="flex-1">
                    <h3 className="text-xl font-outfit font-bold tracking-tight mb-6 flex items-center gap-2 text-foreground">
                      <CalendarIcon className="w-5 h-5 text-accent" />
                      Select a Date
                    </h3>
                    <div className="bg-background/50 rounded-2xl p-4 border border-border/50">
                      <Calendar
                        mode="single"
                        selected={selectedDate}
                        onSelect={(date) => {
                          setSelectedDate(date);
                          setSelectedSlot(null); // Reset slot when date changes
                        }}
                        disabled={[
                          { before: new Date() },
                          { dayOfWeek: [0, 6] },
                        ]} // Disable past days & weekends
                        className="w-full pointer-events-auto"
                        classNames={{
                          months:
                            "w-full flex flex-col sm:flex-row space-y-4 sm:space-x-4 sm:space-y-0",
                          month: "w-full space-y-4",
                          caption:
                            "flex justify-center pt-1 relative items-center",
                          caption_label: "text-sm font-medium font-outfit",
                          nav: "space-x-1 flex items-center",
                          nav_button:
                            "h-7 w-7 bg-transparent p-0 opacity-50 hover:opacity-100",
                          nav_button_previous: "absolute left-1",
                          nav_button_next: "absolute right-1",
                          table: "w-full border-collapse space-y-1",
                          head_row: "flex w-full justify-between",
                          head_cell:
                            "text-muted-foreground rounded-md w-9 font-normal text-[0.8rem]",
                          row: "flex w-full mt-2 justify-between",
                          cell: "text-center text-sm p-0 w-9 h-9 flex items-center justify-center relative [&:has([aria-selected])]:bg-accent/10 first:[&:has([aria-selected])]:rounded-l-md last:[&:has([aria-selected])]:rounded-r-md focus-within:relative focus-within:z-20",
                          day: "h-9 w-9 p-0 font-normal aria-selected:opacity-100 hover:bg-muted rounded-full transition-colors",
                          day_selected:
                            "bg-accent text-accent-foreground hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground rounded-full",
                          day_today: "bg-accent/10 text-accent font-bold",
                          day_outside: "text-muted-foreground opacity-50",
                          day_disabled:
                            "text-muted-foreground opacity-30 cursor-not-allowed",
                        }}
                      />
                    </div>
                  </div>

                  {/* Right: Time Slots */}
                  <div className="flex-1 flex flex-col">
                    <h3 className="text-xl font-outfit font-bold tracking-tight mb-6 flex items-center gap-2 text-foreground">
                      <Clock className="w-5 h-5 text-accent" />
                      {selectedDate
                        ? format(selectedDate, "EEEE, MMMM do")
                        : "Select a Time"}
                    </h3>

                    {!selectedDate ? (
                      <div className="flex-1 flex items-center justify-center border-2 border-dashed border-border/50 rounded-2xl bg-muted/20 pb-10">
                        <p className="text-muted-foreground text-sm flex flex-col items-center gap-2">
                          <CalendarIcon className="w-8 h-8 opacity-20" />
                          Please select a date first
                        </p>
                      </div>
                    ) : slots.length === 0 ? (
                      <div className="flex-1 flex items-center justify-center border-2 border-dashed border-border/50 rounded-2xl bg-muted/20 pb-10">
                        <p className="text-muted-foreground text-sm flex flex-col items-center gap-2">
                          <Clock className="w-8 h-8 opacity-20" />
                          No slots available today
                        </p>
                      </div>
                    ) : (
                      <div className="flex flex-col h-full gap-6">
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 overflow-y-auto pr-2 max-h-[250px] custom-scrollbar">
                          {slots.map((slot) => {
                            const active =
                              selectedSlot?.toISOString() ===
                              slot.toISOString();

                            return (
                              <button
                                key={slot.toISOString()}
                                onClick={() => setSelectedSlot(slot)}
                                className={`
                                  flex items-center justify-center py-2.5 px-4 rounded-xl border-2 text-sm font-semibold transition-all duration-200
                                  ${
                                    active
                                      ? "bg-accent border-accent text-accent-foreground shadow-md shadow-accent/20 scale-[1.02]"
                                      : "bg-background border-border/50 text-foreground hover:border-accent/40 hover:bg-accent/5"
                                  }
                                `}
                              >
                                {format(slot, "h:mm a")}
                              </button>
                            );
                          })}
                        </div>

                        {/* Sticky CTA Area */}
                        <div className="mt-auto pt-6 border-t border-border/50">
                          <button
                            onClick={handleBooking}
                            disabled={!selectedSlot}
                            className={`w-full group py-4 px-6 rounded-xl font-bold flex items-center justify-center gap-2 transition-all duration-300 ${
                              selectedSlot
                                ? "bg-cta glow-cta shadow-xl text-foreground hover:-translate-y-1"
                                : "bg-muted text-muted-foreground cursor-not-allowed border border-border"
                            }`}
                          >
                            {selectedSlot ? (
                              <>
                                Confirm {format(selectedSlot, "h:mm a")} Slot
                                <ChevronRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                              </>
                            ) : (
                              "Select a time slot"
                            )}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="py-16 px-8 flex flex-col items-center justify-center text-center bg-accent/5"
              >
                <div className="w-20 h-20 rounded-full bg-green-500/20 flex items-center justify-center mb-6">
                  <CheckCircle2 className="w-10 h-10 text-green-500" />
                </div>
                <h3 className="text-3xl font-outfit font-bold text-foreground mb-4">
                  You're all set!
                </h3>
                <p className="text-lg text-muted-foreground max-w-md mb-8">
                  We'll send a calendar invite to your email for{" "}
                  <span className="font-semibold text-foreground">
                    {selectedSlot
                      ? format(selectedSlot, "MMMM do 'at' h:mm a")
                      : ""}
                  </span>
                  .
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Button
                    variant="outline"
                    className="gap-2 px-6"
                    onClick={() => {
                      setIsBooked(false);
                      setSelectedSlot(null);
                    }}
                  >
                    Reschedule
                  </Button>
                  <Button className="bg-cta gap-2 px-6">
                    <Video className="w-4 h-4" />
                    Join Google Meet (Test)
                  </Button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </motion.div>
      <div className="flex gap-6 flex-wrap items-center justify-center mt-5">
        {tags.map((tag) => (
          <Badge variant="outline" key={tag} className="flax gap-2">
            <Check data-icon="inline-start" className="text-accent" />
            {tag}
          </Badge>
        ))}
      </div>
    </section>
  );
};
