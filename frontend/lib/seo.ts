import { Metadata } from "next";

interface SEOProps {
  title: string;
  description: string;
  image?: string;
  path?: string;
  noIndex?: boolean;
}

const siteName = "automedge";
export const baseUrl =
  process.env.NEXT_PUBLIC_SITE_URL || "https://automedge.com";

/**
 * Reusable SEO config generator for Next.js App Router
 */
export function constructMetadata({
  title,
  description,
  image = "/og-image.png",
  path = "",
  noIndex = false,
}: SEOProps): Metadata {
  return {
    title: {
      default: title,
      template: `%s | ${siteName}`,
    },
    description,
    metadataBase: new URL(baseUrl),
    alternates: {
      canonical: `${baseUrl}${path}`,
    },
    authors: [{ name: "AutomEdge Team" }],
    robots: {
      index: !noIndex,
      follow: !noIndex,
      googleBot: {
        index: !noIndex,
        follow: !noIndex,
        "max-video-preview": -1,
        "max-image-preview": "large",
        "max-snippet": -1,
      },
    },
    openGraph: {
      title,
      description,
      url: `${baseUrl}${path}`,
      siteName,
      images: [
        {
          url: image,
          width: 1200,
          height: 630,
          alt: title,
        },
      ],
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [image],
      creator: "@automedge",
    },
  };
}

/**
 * Reusable JSON-LD schema generator for Local Businesses / Software
 */
export function generateOrganizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "AutomEdge",
    url: baseUrl,
    applicationCategory: "BusinessApplication",
    description: "Lead automation platform for home service companies.",
    provider: {
      "@type": "Organization",
      name: "AutomEdge",
      url: baseUrl,
    },
  };
}
