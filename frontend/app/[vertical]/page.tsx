import { VERTICALS } from '@/lib/verticals';
import { HeroSection } from '@/components/server/HeroSection';
import { PainPoints } from '@/components/server/PainPoints';
import { Metadata } from 'next';
import { notFound } from 'next/navigation';

export async function generateStaticParams() {
    return Object.keys(VERTICALS).map((vertical) => ({
        vertical: vertical,
    }));
}

export async function generateMetadata({ params }: { params: Promise<{ vertical: string }> }): Promise<Metadata> {
    const { vertical } = await params;
    const v = VERTICALS[vertical];
    if (!v) return { title: 'Not Found' };

    return {
        title: `${v.label} Lead Automation — Automedge`,
        description: `${v.pain}. Automedge fixes this with automated follow-up in 60 seconds. Built for ${v.label} companies.`,
        openGraph: {
            title: `Automedge for ${v.label}`,
            url: `https://automedge.com/${v.slug}`,
        },
        robots: { index: true, follow: true }
    };
}

import { DemoWorkflow } from '@/components/client/DemoWorkflow';

export default async function VerticalPage({ params }: { params: Promise<{ vertical: string }> }) {
    const { vertical } = await params;
    const v = VERTICALS[vertical];

    if (!v) {
        notFound();
    }

    return (
        <main className="min-h-screen bg-slate-950">
            <HeroSection
                title={`Automated Lead Management for ${v.label}`}
                subtitle={`Don't let another ${v.label} lead go cold. Capture, qualify, and book clients in under 60 seconds.`}
                ctaText="Start Free Demo"
                ctaLink="/dashboard"
            />
            <PainPoints
                vertical={v.label}
                pain={v.pain}
                fix={v.fix}
            />

            <DemoWorkflow vertical={vertical} />

            {/* 
        TODO: Add PricingTable (Server Component) here
      */}
        </main>
    );
}
