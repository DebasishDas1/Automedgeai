"use client";

import { motion } from "framer-motion";

export function LogoCloud() {
    return (
        <section className="py-24 px-6 bg-muted/20 border-y border-border/10">
            <div className="max-w-7xl mx-auto text-center">
                <motion.h2
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    className="text-xl font-black tracking-[0.4em] uppercase text-muted-foreground/60 mb-16"
                >
                    Trusted by Service Businesses
                </motion.h2>

                <div className="flex flex-wrap items-center justify-center gap-x-12 md:gap-x-20 gap-y-12 opacity-80 grayscale group hover:grayscale-0 transition-all duration-700">
                    <span className="text-3xl font-black font-outfit tracking-tighter">SERVICE TITAN</span>
                    <span className="text-2xl font-black font-inter italic tracking-tight underline-offset-8 underline decoration-accent decoration-[6px]">HOUSECALL PRO</span>
                    <span className="text-3xl font-black tracking-widest uppercase">Jobber</span>
                    <span className="text-4xl font-outfit font-[900] tracking-normal italic text-foreground">XOi</span>
                    <span className="text-3xl font-black font-inter tracking-[0.1em] border-4 border-foreground px-6 py-2">FIELDEDGE</span>
                </div>
            </div>
        </section>
    );
}
