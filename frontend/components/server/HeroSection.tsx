import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export const HeroSection = ({
    title,
    subtitle,
    ctaText,
    ctaLink
}: {
    title: string,
    subtitle: string,
    ctaText: string,
    ctaLink: string
}) => {
    return (
        <section className="relative py-20 px-6 lg:py-32 overflow-hidden bg-slate-950 text-white">
            <div className="max-w-7xl mx-auto flex flex-col items-center text-center relative z-10">
                <h1 className="text-5xl lg:text-7xl font-bold tracking-tight mb-6 bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
                    {title}
                </h1>
                <p className="text-xl lg:text-2xl text-slate-300 max-w-2xl mb-10">
                    {subtitle}
                </p>
                <div className="flex gap-4">
                    <Button asChild size="lg" className="bg-emerald-500 hover:bg-emerald-600">
                        <Link href={ctaLink}>{ctaText}</Link>
                    </Button>
                    <Button variant="outline" size="lg" className="border-slate-700 text-white hover:bg-slate-800">
                        Learn More
                    </Button>
                </div>
            </div>
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full opacity-20 pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full blur-[128px]"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500 rounded-full blur-[128px]"></div>
            </div>
        </section>
    );
};
