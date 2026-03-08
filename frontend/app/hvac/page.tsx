import React from 'react';
import { Metadata } from 'next';
import dynamic from 'next/dynamic';
import { HvacNavbar } from '@/components/hvac/HvacNavbar';
import { HvacHero } from '@/components/hvac/HvacHero';
import { HvacFooter } from '@/components/hvac/HvacFooter';

// Component fallbacks/skeletons for lazy loading
const ComponentSkeleton = ({ height = "h-[400px]" }) => (
    <div className={`w-full max-w-6xl mx-auto ${height} bg-slate-200/50 dark:bg-slate-800/50 animate-pulse rounded-3xl my-12`}></div>
);

// Dynamically import heavy/non-critical components with skeleton fallbacks
const HvacWorkflowDemo = dynamic(() => import('@/components/hvac/HvacWorkflowDemo').then(mod => mod.HvacWorkflowDemo), {
    loading: () => <ComponentSkeleton />
});
const HvacFeatures = dynamic(() => import('@/components/hvac/HvacFeatures').then(mod => mod.HvacFeatures), {
    loading: () => <ComponentSkeleton height="h-[600px]" />
});
const HvacSocialProof = dynamic(() => import('@/components/hvac/HvacSocialProof').then(mod => mod.HvacSocialProof), {
    loading: () => <ComponentSkeleton />
});
const LeadForm = dynamic(() => import('@/components/shared/LeadForm').then(mod => mod.LeadForm), {
    loading: () => <ComponentSkeleton />
});
const Chatbot = dynamic(() => import('@/components/shared/Chatbot').then(mod => mod.Chatbot));

export const metadata: Metadata = {
    title: 'HVAC Lead Automation — automedge',
    description: 'Stop losing HVAC jobs to slow replies. Automedge follows up with every lead in 60 seconds — while you are still on the job site.',
    openGraph: {
        title: 'HVAC Lead Automation — automedge',
        description: 'Stop losing HVAC jobs to slow replies. Automedge follows up with every lead in 60 seconds.',
        images: ['/hvac.png'],
    }
};

export default function HvacLandingPage() {
    return (
        <main className="min-h-screen bg-[#EEF2F5] dark:bg-slate-950 selection:bg-[#00C2A8]/30 transition-colors duration-500">
            <HvacNavbar />

            <div className="flex flex-col">
                <HvacHero />
                <HvacWorkflowDemo />
                <HvacSocialProof />
                <HvacFeatures />

                <section className="py-32 px-6 bg-white dark:bg-slate-900 transition-colors duration-500" id="contact">
                    <LeadForm
                        vertical="hvac"
                        title="Book your HVAC demo"
                        subtitle="We'll set up your automated follow-up system live on the call."
                        accentColor="#00C2A8"
                    />
                </section>
            </div>

            <HvacFooter />
            <Chatbot vertical="hvac" accentColor="#00C2A8" />

            {/* Smooth background decoration */}
            <div className="fixed top-0 left-0 w-full h-full pointer-events-none -z-10">
                <div className="absolute top-[20%] -left-[10%] w-[400px] h-[400px] bg-[#00C2A8]/5 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[20%] -right-[10%] w-[500px] h-[500px] bg-orange-500/5 dark:bg-orange-950/10 rounded-full blur-[150px]"></div>
            </div>
        </main>
    );
}
