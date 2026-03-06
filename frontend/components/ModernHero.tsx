"use client";

import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, Zap, MessageSquare } from "lucide-react";
import { useState, useEffect } from "react";

const HERO_IMAGES = [
    {
        src: "/hvac.png",
        alt: "HVAC Services",
    },
    {
        src: "/roofing.png",
        alt: "Roofing Services",
    },
    {
        src: "/hvac.png",
        alt: "HVAC Services",
    },
];

export function ModernHero() {
    const [currentImage, setCurrentImage] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentImage((prev) => (prev + 1) % HERO_IMAGES.length);
        }, 5000);
        return () => clearInterval(timer);
    }, []);

    return (
        <section className="relative min-h-screen py-32 px-6 flex flex-col items-center justify-center bg-background overflow-hidden">
            <div className="w-full max-w-4xl mx-auto flex flex-col items-center gap-12 text-center text-foreground">
                {/* Headline Above Pill */}
                <motion.h1
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="text-6xl md:text-8xl font-outfit font-[900] tracking-tighter leading-none"
                >
                    Turn Every Inquiry into a
                </motion.h1>

                {/* Giant Horizontal Pill Carousel */}
                <div className="relative w-full aspect-[16/9] md:aspect-[2.4/1] rounded-[3rem] md:rounded-full overflow-hidden shadow-2xl z-0">
                    <div
                        className="flex h-full transition-transform duration-700 ease-in-out"
                        style={{ transform: `translateX(-${currentImage * 100}%)` }}
                    >
                        {HERO_IMAGES.map((image, index) => (
                            <div key={index} className="relative min-w-full h-full">
                                <Image
                                    src={image.src}
                                    alt={image.alt}
                                    fill
                                    className="object-cover"
                                    priority={index === 0}
                                />

                                {/* Overlay */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent"></div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Sub-headline Below Pill */}
                <motion.div
                    initial={{ opacity: 0, y: -30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.8, ease: "easeOut" }}
                >
                    <h2 className="text-6xl md:text-8xl font-outfit font-[900] tracking-tighter leading-none text-accent">
                        Booked Appointment
                    </h2>

                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 1, duration: 1 }}
                        className="mt-12 max-w-2xl mx-auto text-xl md:text-2xl text-muted-foreground font-medium leading-relaxed"
                    >
                        The B2B SaaS for HVAC, Roofing, and Plumbing companies to capture, qualify, and book leads in seconds.
                    </motion.p>
                </motion.div>

                {/* Buttons Component */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.2, duration: 0.6 }}
                    className="flex flex-col sm:flex-row items-center justify-center gap-6 w-full"
                >
                    <Link href="/hvac" className="w-full sm:w-auto">
                        <button className="w-full bg-accent text-accent-foreground px-12 py-6 rounded-full font-bold text-xl hover:scale-105 transition-all shadow-xl hover:shadow-accent/40 flex items-center justify-center gap-3 group">
                            <Zap className="w-6 h-6 group-hover:animate-pulse" />
                            See it in action
                        </button>
                    </Link>
                    <button className="w-full sm:w-auto flex items-center justify-center gap-3 px-12 py-6 rounded-full border-2 border-border font-black text-xs tracking-widest hover:bg-muted transition-all group">
                        <MessageSquare className="w-6 h-6 text-accent" />
                        I NEED HELP
                        <ArrowUpRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                </motion.div>
            </div>
        </section>
    );
}
