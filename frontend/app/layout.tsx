import type { Metadata, Viewport } from "next";
import { Outfit, Plus_Jakarta_Sans, DM_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";

// Display — Outfit
const outfit = Outfit({
  subsets: ["latin"],
  weight: ["700", "800", "900"],
  variable: "--font-display",
  display: "swap",
  preload: true,
});

// Body — Plus Jakarta Sans
const jakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-sans",
  display: "swap",
  preload: true,
});

// Mono — DM Mono
const dmMono = DM_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  title: {
    default: "Automedge — 24/7 AI Lead Automation for HVAC, Roofing & Plumbing Firms",
    template: "%s | Automedge AI — Lead Response in Under 60 Seconds",
  },
  alternates: {
    canonical: "https://automedge.com",
  },
  description:
    "Automedge captures every lead from HVAC, Roofing, Plumbing, and Pest Control " +
    "businesses and follows up automatically in 60 seconds. Never miss a job again.",
  metadataBase: new URL("https://automedge.com"),
  keywords: [
    "HVAC lead management",
    "roofing CRM",
    "plumbing lead automation",
    "pest control software",
    "home service automation",
  ],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://automedge.com",
    siteName: "automedge",
    title: "automedge — Lead Automation for Home Service Companies",
    description:
      "Follow up with every lead in 60 seconds. Built for HVAC, Roofing, Plumbing, and Pest Control businesses.",
    images: [
      {
        url: "/AutomEdge-logo.png",
        width: 1200,
        height: 630,
        alt: "automedge logo",
      },
      {
        url: "/hvac.png",
        width: 1200,
        height: 630,
        alt: "automedge — Lead Automation",
      },
    ],
  },
};

export const viewport: Viewport = {
  themeColor: "#00C2A8",
  width: "device-width",
  initialScale: 1,
};

import { cn } from "@/lib/utils";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={cn(outfit.variable, jakartaSans.variable, dmMono.variable)}
      suppressHydrationWarning
    >
      <body
        className={cn(
          "font-sans",
          "text-slate-900 dark:text-slate-100",
          "antialiased",
          "min-h-screen",
          "text-base",
          "leading-relaxed",
          "[word-break:break-word]",
        )}
      >
        <Script
          id="json-ld"
          type="application/ld+json"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify([
              {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": "Automedge",
                "url": "https://automedge.com",
                "logo": "https://automedge.com/AutomEdge-logo.png",
                "description": "24/7 AI Lead Automation for HVAC, Roofing, Plumbing, and Pest Control businesses.",
                "sameAs": ["https://twitter.com/automedge", "https://linkedin.com/company/automedge"],
              },
              {
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": "Automedge AI",
                "image": "https://automedge.com/hvac.png",
                "address": {
                  "@type": "PostalAddress",
                  "addressLocality": "Austin",
                  "addressRegion": "TX",
                  "addressCountry": "US"
                },
                "geo": {
                  "@type": "GeoCoordinates",
                  "latitude": 30.2672,
                  "longitude": -97.7431
                },
                "url": "https://automedge.com",
                "telephone": "+15125550199",
                "priceRange": "$$",
                "openingHoursSpecification": {
                  "@type": "OpeningHoursSpecification",
                  "dayOfWeek": [
                    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
                  ],
                  "opens": "00:00",
                  "closes": "23:59"
                }
              }
            ]),
          }}
        />
        {children}
        <Toaster position="top-center" expand={true} richColors />
      </body>
    </html>
  );
}
