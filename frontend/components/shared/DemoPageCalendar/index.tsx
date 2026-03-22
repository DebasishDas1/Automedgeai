"use client";

import { useState, useEffect, useMemo } from "react";
import { m as motion, AnimatePresence } from "framer-motion";
import { Calendar as CalendarIcon, Check } from "lucide-react";
import { Calendar } from "@/components/ui/calendar";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { addMinutes, setHours, setMinutes, isToday } from "date-fns";

// Internal components
import { CalendarHeader } from "./CalendarHeader";
import { TimeSlotPicker } from "./TimeSlotPicker";
import { BookingForm } from "./BookingForm";
import { SuccessDisplay } from "./SuccessDisplay";
import { createBooking } from "@/lib/api/booking";

type DemoPageCalendarProps = {
  title?: string;
  highlight?: string;
  description?: string;
  tags?: string[];
  type?: string;
};

export const DemoPageCalendar = ({
  title = "Ready to build this for",
  highlight = "your business?",
  description = "Book a quick 15-minute chat to see exactly how AutomEdge fits into your specific workflow. No pressure, just a live demo.",
  tags = [],
  type = "general",
}: DemoPageCalendarProps) => {
  const [mounted, setMounted] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(
    new Date(),
  );
  const [selectedSlot, setSelectedSlot] = useState<Date | null>(null);
  const [bookingStep, setBookingStep] = useState<
    "calendar" | "details" | "success"
  >("calendar");
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    website: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Use useMemo for slot generation to keep it stable
  const slots = useMemo(() => {
    if (!selectedDate) return [];

    const generated: Date[] = [];
    let start = setHours(setMinutes(selectedDate, 0), 9);
    let end = setHours(setMinutes(selectedDate, 0), 18);

    if (isToday(selectedDate)) {
      const now = new Date();
      const remainder = 30 - (now.getMinutes() % 30);
      start = addMinutes(now, remainder);
      if (start < setHours(setMinutes(selectedDate, 0), 9)) {
        start = setHours(setMinutes(selectedDate, 0), 9);
      }
    }

    // Deterministic random (based on date) so it doesn't flicker
    const dateSeed = selectedDate.getDate() + selectedDate.getMonth();

    while (start < end && generated.length < 12) {
      if (start > new Date()) {
        const hour = start.getHours();
        // Skip lunch and very late slots
        if (hour !== 12 && hour !== 13) {
          generated.push(start);
        }
      }
      start = addMinutes(start, 30);
    }

    return generated;
  }, [selectedDate]);

  const handleBooking = () => {
    if (selectedSlot) {
      setBookingStep("details");
    }
  };

  const handleFinalConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await createBooking({
        name:         formData.name,
        email:        formData.email,
        business:      formData.website || "No Business Listed",
        vertical:      type,
        scheduled_at:  selectedSlot ? selectedSlot.toISOString() : new Date().toISOString(),
      });
      setBookingStep("success");
    } catch (err) {
      console.error("Booking failed:", err);
      // In a real app, use a toast. For now, alert is fine.
      alert("Booking failed. Please try again or contact us directly.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!mounted) return null;

  return (
    <section
      id="calendar"
      className="relative py-28 px-6 max-w-6xl mx-auto scroll-mt-24 w-full flex flex-col items-center overflow-hidden"
    >
      {/* Background Blobs */}
      <div className="absolute top-1/2 left-0 w-[600px] h-[600px] bg-accent/10 rounded-full blur-[140px] -translate-y-1/2 -z-10 pointer-events-none animate-pulse" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-primary/5 rounded-full blur-[120px] -z-10 pointer-events-none animate-pulse delay-1000" />

      <CalendarHeader
        title={title}
        highlight={highlight}
        description={description}
      />

      {/* Booking Interface */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="w-full"
      >
        <Card className="w-full max-w-5xl mx-auto border-2 border-border/50 shadow-3xl bg-card/60 backdrop-blur-3xl overflow-hidden relative rounded-[3rem]">
          <AnimatePresence mode="wait">
            {bookingStep === "calendar" ? (
              <motion.div
                key="calendar"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-8 md:p-14 lg:p-16"
              >
                <div className="flex flex-col md:flex-row gap-12 lg:gap-20">
                  {/* Left: Calendar Picker */}
                  <div className="flex-1">
                    <h3 className="text-xl font-outfit font-black tracking-tight mb-8 flex items-center gap-3 text-foreground uppercase sm:text-sm">
                      <CalendarIcon className="w-5 h-5 text-accent" />
                      Select Date
                    </h3>
                    <div className="bg-background/50 rounded-4xl p-8 border-2 border-border/40 shadow-xl ring-8 ring-accent/5">
                      <Calendar
                        mode="single"
                        selected={selectedDate}
                        onSelect={(date) => {
                          setSelectedDate(date);
                          setSelectedSlot(null);
                        }}
                        disabled={[
                          { before: new Date() },
                          { dayOfWeek: [0, 6] },
                        ]}
                        className="w-full pointer-events-auto"
                        classNames={{
                          months: "w-full",
                          month: "w-full space-y-6",
                          caption:
                            "flex justify-center pt-2 relative items-center mb-6",
                          caption_label:
                            "text-lg font-black font-outfit text-foreground tracking-tight",
                          nav: "space-x-1 flex items-center",
                          nav_button:
                            "h-10 w-10 bg-background border-2 border-border/80 rounded-xl flex items-center justify-center hover:bg-accent/10 transition-colors shadow-sm",
                          nav_button_previous: "absolute left-1",
                          nav_button_next: "absolute right-1",
                          table: "w-full border-collapse",
                          head_row: "flex w-full justify-between mb-4",
                          head_cell:
                            "text-muted-foreground/50 rounded-md w-10 font-black text-[0.65rem] uppercase tracking-widest",
                          row: "flex w-full mt-2 justify-between",
                          cell: "text-center text-sm p-0 w-10 h-10 flex items-center justify-center relative",
                          day: "h-10 w-10 p-0 font-bold aria-selected:opacity-100 hover:bg-accent/10 rounded-xl transition-all duration-300",
                          day_selected:
                            "bg-accent !text-white hover:bg-accent hover:text-white focus:bg-accent focus:text-white rounded-xl shadow-[0_10px_20px_-5px_rgba(29,158,117,0.4)] scale-110",
                          day_today:
                            "border-2 border-accent/40 text-accent font-black",
                          day_outside: "text-muted-foreground opacity-20",
                          day_disabled:
                            "text-muted-foreground opacity-10 cursor-not-allowed",
                        }}
                      />
                    </div>
                  </div>

                  {/* Right: Time Slots */}
                  <TimeSlotPicker
                    selectedDate={selectedDate}
                    selectedSlot={selectedSlot}
                    onSelectSlot={setSelectedSlot}
                    slots={slots}
                    onContinue={handleBooking}
                  />
                </div>
              </motion.div>
            ) : bookingStep === "details" ? (
              <BookingForm
                selectedSlot={selectedSlot}
                formData={formData}
                setFormData={setFormData}
                onConfirm={handleFinalConfirm}
                onBack={() => setBookingStep("calendar")}
                isSubmitting={isSubmitting}
              />
            ) : (
              <SuccessDisplay
                formData={formData}
                selectedSlot={selectedSlot}
                onReschedule={() => {
                  setBookingStep("calendar");
                  setSelectedSlot(null);
                }}
              />
            )}
          </AnimatePresence>
        </Card>
      </motion.div>

      <div className="flex gap-4 md:gap-10 flex-wrap items-center justify-center mt-16 bg-muted/10 py-5 px-10 rounded-full border-2 border-border/30 backdrop-blur-md max-w-fit mx-auto shadow-sm">
        {tags.map((tag) => (
          <Badge
            variant="outline"
            key={tag}
            className="flex gap-3 text-muted-foreground/80 font-black border-none hover:text-accent transition-colors"
          >
            <Check className="w-5 h-5 text-accent stroke-[3px]" />
            {tag}
          </Badge>
        ))}
      </div>
    </section>
  );
};
