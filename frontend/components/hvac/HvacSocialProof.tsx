import React from 'react';

const testimonials = [
    {
        quote: "We were missing 30% of our leads because we couldn't answer the phone on jobs. Automedge fixed that in a day.",
        name: "James R.",
        city: "Dallas TX",
        company: "R&S HVAC"
    },
    {
        quote: "The quote follow-up alone recovered 4 jobs last month that I would have just forgotten about.",
        name: "Maria C.",
        city: "Phoenix AZ",
        company: "Desert Air Systems"
    },
    {
        quote: "Response time went from hours to 47 seconds. We went from 2 Google reviews a month to 18.",
        name: "Tom H.",
        city: "Atlanta GA",
        company: "Heritage Mechanical"
    },
    {
        quote: "This software is like having a full-time dispatch assistant working 24/7.",
        name: "Kevin L.",
        city: "Chicago IL",
        company: "Windy City Cooling"
    },
    {
        quote: "Customers literally tell us they booked with us because we replied so fast.",
        name: "Sarah B.",
        city: "Austin TX",
        company: "Lone Star A/C"
    },
    {
        quote: "Absolutely a game changer. Less time on the phone, more time actually doing the work.",
        name: "David T.",
        city: "Denver CO",
        company: "Peak Plumbing & Heating"
    }
];

export const HvacSocialProof = () => {
    return (
        <section className="py-32 px-6 bg-white overflow-hidden">
            <div className="max-w-7xl mx-auto">
                <div className="flex flex-col md:flex-row gap-8 overflow-x-auto no-scrollbar pb-8 snap-x">
                    {testimonials.map((t, i) => (
                        <div
                            key={i}
                            className="min-w-full md:min-w-[calc(33.333%-20px)] bg-[#EEF2F5] p-10 rounded-[32px] snap-center flex flex-col justify-between"
                        >
                            <div>
                                <div className="text-orange-400 text-xl mb-6 leading-none">⭐⭐⭐⭐⭐</div>
                                <p className="text-lg font-medium italic text-[#1A1A1A] leading-relaxed mb-8">"{t.quote}"</p>
                            </div>
                            <div>
                                <div className="text-[#1A1A1A] font-black font-outfit uppercase tracking-tighter text-lg">{t.name}</div>
                                <div className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-4">{t.company} · {t.city}</div>
                                <div className="inline-block bg-white text-[#00C2A8] text-[8px] font-black px-3 py-1.5 rounded-full uppercase border border-[#00C2A8]/20 tracking-[0.2em] shadow-sm">HVAC OWNER</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};
