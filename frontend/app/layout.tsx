import type { Metadata, Viewport } from 'next';
import { Outfit, Plus_Jakarta_Sans, DM_Mono } from 'next/font/google';
import './globals.css';

const outfit = Outfit({
    subsets: ['latin'],
    weight: ['700', '800', '900'],   // removed 400/500/600 — never used in headings
    variable: '--font-display',
    display: 'swap',                 // shows fallback font immediately → better LCP
    preload: true,                   // above the fold — preload
});

// Body — Plus Jakarta Sans
// Why over Inter: better letter-spacing on mobile,
// rounder glyphs read easier at 14-16px on small screens,
// less overused than Inter in SaaS
const jakartaSans = Plus_Jakarta_Sans({
    subsets: ['latin'],
    weight: ['400', '500', '600'],   // regular / medium / semibold only
    variable: '--font-sans',
    display: 'swap',
    preload: true,
});

// Mono — not preloaded (never above the fold)
const dmMono = DM_Mono({
    subsets: ['latin'],
    weight: ['400', '500'],
    variable: '--font-mono',
    display: 'swap',
    preload: false,
});

// ─────────────────────────────────────────────────────────────────────────────
//  METADATA
// ─────────────────────────────────────────────────────────────────────────────
export const metadata: Metadata = {
    title: {
        default: 'automedge — Lead Automation for Home Service Companies',
        template: '%s — automedge',
    },
    description:
        'Automedge captures every lead from HVAC, Roofing, Plumbing, and Pest Control ' +
        'businesses and follows up automatically in 60 seconds. Never miss a job again.',
    metadataBase: new URL('https://automedge.com'),
    keywords: [
        'HVAC lead management',
        'roofing CRM',
        'plumbing lead automation',
        'pest control software',
        'home service automation',
    ],
    authors: [{ name: 'Automedge Inc.' }],
    creator: 'Automedge',
    openGraph: {
        type: 'website',
        locale: 'en_US',
        url: 'https://automedge.com',
        siteName: 'automedge',
        title: 'automedge — Lead Automation for Home Service Companies',
        description: 'Follow up with every lead in 60 seconds. Built for HVAC, Roofing, Plumbing, and Pest Control businesses.',
        images: [{
            url: '/og-image.png',
            width: 1200,
            height: 630,
            alt: 'automedge — Lead Automation',
        }],
    },
    twitter: {
        card: 'summary_large_image',
        title: 'automedge — Lead Automation',
        description: 'Follow up with every lead in 60 seconds.',
        images: ['/og-image.png'],
    },
    robots: {
        index: true,
        follow: true,
        googleBot: {
            index: true,
            follow: true,
            'max-image-preview': 'large',
        },
    },
    icons: {
        icon: '/favicon.ico',
        shortcut: '/favicon-16x16.png',
        apple: '/apple-touch-icon.png',
    },
};

// ─────────────────────────────────────────────────────────────────────────────
//  VIEWPORT
//  maximum-scale=1 prevents iOS auto-zoom on input focus
//  but keep user-scalable=yes for accessibility
// ─────────────────────────────────────────────────────────────────────────────
export const viewport: Viewport = {
    themeColor: '#0D1B2A',
    width: 'device-width',
    initialScale: 1,
    // maximumScale: 1,  ← DO NOT add this — breaks accessibility
};

// ─────────────────────────────────────────────────────────────────────────────
//  ROOT LAYOUT
// ─────────────────────────────────────────────────────────────────────────────
export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html
            lang="en"
            className={[
                outfit.variable,
                jakartaSans.variable,
                dmMono.variable,
            ].join(' ')}
            suppressHydrationWarning  // prevents mismatch from browser extensions
        >
            <body
                className={[
                    'font-sans',           // Plus Jakarta Sans as default
                    'bg-background',       // from CSS vars
                    'text-foreground',
                    'antialiased',         // smoother text rendering on all screens
                    'min-h-screen',
                    // Mobile reading optimizations:
                    'text-base',           // 16px base — never go below on mobile
                    'leading-relaxed',     // 1.625 line-height — easier to track lines
                    '[word-break:break-word]', // prevents overflow on narrow screens
                ].join(' ')}
            >
                {children}
            </body>
        </html>
    );
}